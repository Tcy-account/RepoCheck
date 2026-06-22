"""
环境风险评分工具

输入：所有 dependencies 和元数据
输出：评分报告

评分维度：
  - dependencyRiskScore：越高风险越高
  - cudaRiskScore：越高风险越高
  - dockerReadinessScore：越高 Docker 支持越好
  - environmentScore：越高环境越容易复现
  - riskLevel：LOW / MEDIUM / HIGH

风险评估规则（详细）：
  flash-attn / xformers / deepspeed / bitsandbytes → HIGH
  mmcv / mmcv-full / detectron2 → HIGH（PyTorch+CUDA+编译器敏感）
  tensorflow-gpu → HIGH（CUDA/cuDNN 严格匹配）
  torch+torchvision → MEDIUM（版本需匹配）
  numpy 无版本 → LOW/MEDIUM
  依赖无版本 → MEDIUM，reason 说明
"""

import re
from typing import List, Dict, Tuple
from app.core.logger import logger


# ───────────────────── 框架识别 ─────────────────────

_FRAMEWORK_MAP = {
    "torch": "PyTorch",
    "torchvision": "PyTorch",
    "torchaudio": "PyTorch",
    "tensorflow": "TensorFlow",
    "tensorflow-gpu": "TensorFlow",
    "tf-nightly": "TensorFlow",
    "jax": "JAX",
    "jaxlib": "JAX",
    "paddlepaddle": "PaddlePaddle",
    "paddlepaddle-gpu": "PaddlePaddle",
    "mindspore": "MindSpore",
    "oneflow": "OneFlow",
}

_FRAMEWORK_PRIORITY = [
    "torch", "torchvision", "torchaudio",
    "tensorflow", "tensorflow-gpu",
    "jax", "jaxlib",
    "paddlepaddle", "paddlepaddle-gpu",
    "mindspore",
    "oneflow",
]


# ───────────────────── GPU 线索 ─────────────────────

_GPU_KEYWORDS = [
    "cuda", "cudatoolkit", "cuda-toolkit", "cuda-version", "cudnn",
    "nccl", "cuda-nvcc", "cuda-cudart",
    "tensorflow-gpu", "paddlepaddle-gpu",
    "onnxruntime-gpu",
]

_GPU_PACKAGES = {
    "bitsandbytes", "xformers", "flash-attn", "flashattn",
    "flash-attention", "deepspeed",
    "triton", "cupy", "cupy-cuda",
    "nvidia-ml-py", "pynvml",
    "vllm", "llama-cpp-python", "gguf",
}

# Docker base image 中的 CUDA 线索
_DOCKER_CUDA_KEYWORDS = {"nvidia/cuda", "nvidia", "cuda"}


# ───────────────────── 高风险依赖 ─────────────────────

_HIGH_RISK_PACKAGES = {
    "torch", "torchvision", "torchaudio",
    "tensorflow", "tensorflow-gpu",
    "jax", "jaxlib",
    "mmcv", "mmcv-full", "mmengine",
    "detectron2",
    "opencv-python", "opencv-contrib-python", "opencv-python-headless",
    "numpy", "scipy", "scikit-learn",
    "transformers", "diffusers",
    "xformers", "flash-attn", "flashattn", "flash-attention",
    "deepspeed", "bitsandbytes",
    "onnx", "onnxruntime", "onnxruntime-gpu",
    "triton",
    "cuda-python", "pycuda",
}


# ───────────────────── 风险评分入口 ─────────────────────

def assess_environment_risk(
    all_dependencies: List[Dict],
    metadata: Dict,
) -> Dict:
    """综合环境风险评分"""
    logger.info(f"environment_risk_tool: assessing {len(all_dependencies)} dependencies")

    # ── 元数据提取 ──
    main_framework, framework_version = _detect_main_framework(all_dependencies)

    python_version = metadata.get("pythonVersion")

    cuda_version = metadata.get("cudaVersion")
    if not cuda_version:
        cuda_version = _detect_cuda_from_deps(all_dependencies)
    if not cuda_version:
        cuda_version = _detect_cuda_from_docker_meta(metadata)

    requires_gpu = _detect_gpu_requirement(all_dependencies, metadata)

    has_docker = bool(metadata.get("hasDocker", False))
    docker_base_image = metadata.get("dockerBaseImage")

    # ── chanels 额外线索 ──
    channels = metadata.get("channels", [])
    has_nvidia_ch = metadata.get("hasNvidiaChannel", False)
    has_pytorch_ch = metadata.get("hasPytorchChannel", False)
    if has_nvidia_ch and requires_gpu:
        requires_gpu = True  # 确认

    # ── 评分 ──
    high_count, medium_count = _count_risk_levels(all_dependencies)

    dependency_risk_score = _calc_dependency_risk(high_count, medium_count, len(all_dependencies), all_dependencies)
    cuda_risk_score = _calc_cuda_risk(cuda_version, requires_gpu)
    docker_readiness_score = _calc_docker_readiness(has_docker, docker_base_image)
    environment_score = _calc_environment_score(dependency_risk_score, cuda_risk_score, docker_readiness_score)

    risk_level = _calc_risk_label(environment_score)

    risk_summary = _build_risk_summary(
        high_count, medium_count, python_version, cuda_version,
        requires_gpu, has_docker, all_dependencies, channels,
    )
    install_advice = _build_install_advice(
        python_version, main_framework, framework_version,
        cuda_version, requires_gpu, has_docker, len(all_dependencies),
        all_dependencies,
    )

    result = {
        "pythonVersion": python_version,
        "cudaVersion": cuda_version,
        "mainFramework": main_framework,
        "frameworkVersion": framework_version,
        "requiresGpu": requires_gpu,
        "hasDocker": has_docker,
        "dockerBaseImage": docker_base_image,
        "dependencyRiskScore": dependency_risk_score,
        "cudaRiskScore": cuda_risk_score,
        "dockerReadinessScore": docker_readiness_score,
        "environmentScore": environment_score,
        "riskLevel": risk_level,
        "riskSummary": risk_summary,
        "installAdvice": install_advice,
    }

    logger.info(f"environment_risk_tool: score={environment_score}, risk={risk_level}, "
                f"framework={main_framework}, gpu={requires_gpu}")
    return result


def assess_dependency_risks(all_dependencies: List[Dict]) -> List[Dict]:
    """
    为每个依赖项评估风险等级（原地修改 + 返回）。

    详细风险规则：
    - flash-attn → HIGH: "often requires specific CUDA, PyTorch and compiler versions"
    - xformers → HIGH: "may require CUDA/PyTorch version compatibility"
    - deepspeed → HIGH: "often requires compiler and CUDA toolchain compatibility"
    - bitsandbytes → HIGH: "may fail without compatible CUDA runtime"
    - mmcv / mmcv-full → HIGH: "depends on matching PyTorch and CUDA versions"
    - detectron2 → HIGH: "installation is sensitive to PyTorch, CUDA and compiler versions"
    - tensorflow-gpu → HIGH: "has strict CUDA/cuDNN compatibility requirements"
    - torch+torchvision → MEDIUM if mismatched: "torchvision version should match torch version"
    - numpy unpinned → MEDIUM: "Unpinned numpy version may cause compatibility issues"
    - dependency unpinned → MEDIUM: "Dependency version is not pinned; reproducibility may vary"
    """
    # 先收集 torch/torchvision 版本信息
    torch_ver = None
    torchvision_ver = None
    for d in all_dependencies:
        pkg = d.get("packageName", "").lower()
        ver = d.get("versionSpec")
        if pkg == "torch":
            torch_ver = _clean_ver(ver)
        elif pkg == "torchvision":
            torchvision_ver = ver

    # 逐一评估
    for dep in all_dependencies:
        pkg = dep.get("packageName", "").lower()
        src = dep.get("source", "")
        ver = dep.get("versionSpec")

        # 跳过元数据标记和特殊 source
        if pkg.startswith("_meta:"):
            continue

        # 跳过非包 source（docker 镜像、include 引用等）
        if src in ("docker", "include", "pip-index", "editable", "local", "git"):
            if dep.get("riskLevel") is None:
                dep["riskLevel"] = "LOW"
            continue

        # ── HIGH 风险 ──
        if _apply_high_risk_rules(dep, pkg):
            continue

        # ── torch + torchvision 匹配 ──
        if pkg == "torchvision" and torch_ver and not torchvision_ver:
            dep["riskLevel"] = "MEDIUM"
            dep["riskReason"] = "torchvision version should match torch version"
            continue

        if pkg == "torch" and torchvision_ver and not torch_ver:
            dep["riskLevel"] = "MEDIUM"
            dep["riskReason"] = "torchvision exists but torch version is not pinned; versions may not match"
            continue

        # 深度学习框架
        if pkg in _FRAMEWORK_MAP:
            fw = _FRAMEWORK_MAP[pkg]
            if dep.get("riskLevel") is None:
                dep["riskLevel"] = "MEDIUM"
            if dep.get("riskReason") is None:
                if any(kw in pkg for kw in ("gpu", "cu")):
                    dep["riskReason"] = f"{fw} GPU version; version must match CUDA compatibility"
                else:
                    dep["riskReason"] = f"{fw} may require CUDA runtime; version controls GPU availability"
            continue

        # 无版本约束检查（在 _HIGH_RISK_PACKAGES 之前，因为 numpy unpinned 优先）
        if dep.get("riskLevel") is None:
            if not ver or not ver.strip():
                if pkg == "numpy":
                    dep["riskLevel"] = "MEDIUM"
                    dep["riskReason"] = "Unpinned numpy version may cause compatibility issues in older ML projects"
                elif pkg in _HIGH_RISK_PACKAGES:
                    dep["riskLevel"] = "MEDIUM"
                    dep["riskReason"] = f"{pkg} is a core deep-learning dependency; version compatibility matters"
                else:
                    dep["riskLevel"] = "LOW"
                    dep["riskReason"] = "Dependency version is not pinned; reproducibility may vary over time"
            else:
                dep["riskLevel"] = "LOW"
            continue

        # 高风险包（有版本但未命中 HIGH 的）
        if pkg in _HIGH_RISK_PACKAGES and dep.get("riskLevel") is None:
            dep["riskLevel"] = "MEDIUM"
            if dep.get("riskReason") is None:
                dep["riskReason"] = f"{pkg} is a core deep-learning dependency; version compatibility matters"
            continue

    return all_dependencies


def _apply_high_risk_rules(dep: Dict, pkg: str) -> bool:
    """应用 HIGH 风险规则，返回 True 表示已评估"""

    # CUDA 核心包
    if pkg in ("cuda", "cudatoolkit", "cudnn", "nccl", "cuda-nvcc", "cuda-cudart", "cuda-toolkit"):
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "CUDA toolkit dependency; GPU environment configuration is complex, version must match driver"
        return True

    if "cuda" in pkg and pkg.startswith("cuda"):
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "CUDA-related package; must match GPU driver and hardware"
        return True

    # flash-attn
    if pkg in ("flash-attn", "flashattn", "flash-attention"):
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "flash-attn often requires specific CUDA, PyTorch and compiler versions"
        return True

    # xformers
    if pkg == "xformers":
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "xformers may require CUDA/PyTorch version compatibility"
        return True

    # deepspeed
    if pkg == "deepspeed":
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "deepspeed often requires compiler and CUDA toolchain compatibility"
        return True

    # bitsandbytes
    if pkg == "bitsandbytes":
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "bitsandbytes may fail without compatible CUDA runtime"
        return True

    # mmcv
    if pkg in ("mmcv", "mmcv-full"):
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "mmcv depends on matching PyTorch and CUDA versions"
        return True

    # detectron2
    if pkg == "detectron2":
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "detectron2 installation is sensitive to PyTorch, CUDA and compiler versions"
        return True

    # tensorflow-gpu
    if pkg == "tensorflow-gpu":
        dep["riskLevel"] = "HIGH"
        dep["riskReason"] = "tensorflow-gpu has strict CUDA/cuDNN compatibility requirements"
        return True

    return False


def _clean_ver(ver: str) -> str:
    """清理版本号"""
    if not ver:
        return None
    return ver.lstrip("=><~^! ")


# ───────────────────── 内部辅助 ─────────────────────

def _detect_main_framework(all_deps: List[Dict]) -> Tuple:
    """检测主深度学习框架（优先级：PyTorch > TensorFlow > JAX > PaddlePaddle > MindSpore）"""
    dep_names = {d["packageName"].lower() for d in all_deps}

    for fw_pkg in _FRAMEWORK_PRIORITY:
        if fw_pkg in dep_names:
            for d in all_deps:
                if d["packageName"].lower() == fw_pkg:
                    ver = _clean_ver(d.get("versionSpec", ""))
                    return _FRAMEWORK_MAP.get(fw_pkg, fw_pkg), ver or None
            return _FRAMEWORK_MAP.get(fw_pkg, fw_pkg), None

    return None, None


def _detect_cuda_from_deps(all_deps: List[Dict]) -> str:
    """从依赖中检测 CUDA 版本"""
    for d in all_deps:
        pkg = d["packageName"].lower()
        ver = d.get("versionSpec", "")

        if pkg == "cudatoolkit":
            return _clean_ver(ver) if ver else "from cudatoolkit"

        if pkg in ("cuda", "cuda-version"):
            return _clean_ver(ver) if ver else f"from {pkg}"

    for d in all_deps:
        pkg = d["packageName"].lower()
        cu_match = re.search(r'cu(\d+)(\d+)', pkg)
        if cu_match:
            return f"{cu_match.group(1)}.{cu_match.group(2)}"

    return None


def _detect_cuda_from_docker_meta(metadata: Dict) -> str:
    """从 Docker base image 中检测 CUDA 版本"""
    img = (metadata.get("dockerBaseImage") or "").lower()
    for kw in _DOCKER_CUDA_KEYWORDS:
        if kw in img:
            cuda_match = re.search(r'cuda[:\-]?\s*(\d+\.\d+)', img)
            if cuda_match:
                return cuda_match.group(1)
    return None


def _detect_gpu_requirement(all_deps: List[Dict], metadata: Dict) -> bool:
    """判断是否需要 GPU"""
    if metadata.get("cudaVersion"):
        return True

    base_img = (metadata.get("dockerBaseImage") or "").lower()
    for kw in _DOCKER_CUDA_KEYWORDS:
        if kw in base_img:
            return True

    for d in all_deps:
        pkg = d["packageName"].lower()

        if pkg in _GPU_PACKAGES:
            return True
        if pkg in ("onnxruntime-gpu", "cupy", "cupy-cuda"):
            return True

        for kw in _GPU_KEYWORDS:
            if kw in pkg:
                return True

    # 框架含 -gpu 后缀
    for d in all_deps:
        if d["packageName"].lower().endswith("-gpu"):
            return True

    # channels 线索
    if metadata.get("hasNvidiaChannel"):
        return True

    return False


def _count_risk_levels(all_deps: List[Dict]) -> Tuple[int, int]:
    high = sum(1 for d in all_deps if d.get("riskLevel") == "HIGH")
    medium = sum(1 for d in all_deps if d.get("riskLevel") == "MEDIUM")
    return high, medium


def _calc_dependency_risk(high: int, medium: int, total: int, all_deps: List[Dict]) -> int:
    """依赖风险评分 0-100（越高风险越高）"""
    score = 0

    if total > 100:
        score += 30
    elif total > 50:
        score += 20
    elif total > 20:
        score += 10

    score += min(high * 20, 60)
    score += min(medium * 8, 40)

    # 检查是否有大量未固定版本
    unpinned = sum(1 for d in all_deps
                   if d.get("source") == "pip"
                   and not d.get("versionSpec")
                   and not d.get("packageName", "").startswith("_meta:"))
    if unpinned > 10:
        score += 15
    elif unpinned > 5:
        score += 8

    return min(score, 100)


def _calc_cuda_risk(cuda_version: str, requires_gpu: bool) -> int:
    """CUDA 风险评分 0-100（越高风险越高）"""
    if not requires_gpu and not cuda_version:
        return 0
    if cuda_version and requires_gpu:
        return 40
    if requires_gpu:
        return 70
    return 20


def _calc_docker_readiness(has_docker: bool, base_image: str) -> int:
    """Docker 准备度 0-100（越高越好）"""
    if not has_docker:
        return 20
    if base_image and ("cuda" in base_image.lower() or "nvidia" in base_image.lower()):
        return 90
    return 70


def _calc_environment_score(dep_risk: int, cuda_risk: int, docker_ready: int) -> int:
    raw = 0.4 * (100 - dep_risk) + 0.3 * (100 - cuda_risk) + 0.3 * docker_ready
    return max(0, min(100, int(raw)))


def _calc_risk_label(score: int) -> str:
    if score >= 70:
        return "LOW"
    if score >= 40:
        return "MEDIUM"
    return "HIGH"


# ───────────────────── 摘要与建议 ─────────────────────

def _build_risk_summary(high_count: int, medium_count: int,
                        python_version: str, cuda_version: str,
                        requires_gpu: bool, has_docker: bool,
                        all_deps: List[Dict], channels: List[str]) -> str:
    """生成具体中文风险摘要"""
    parts = []

    # 具体风险检测
    has_flash_attn = any(d.get("packageName", "").lower() in
                         ("flash-attn", "flashattn", "flash-attention") for d in all_deps)
    has_xformers = any(d.get("packageName", "").lower() == "xformers" for d in all_deps)
    has_deepspeed = any(d.get("packageName", "").lower() == "deepspeed" for d in all_deps)
    has_mmcv = any(d.get("packageName", "").lower() in ("mmcv", "mmcv-full") for d in all_deps)
    has_detectron2 = any(d.get("packageName", "").lower() == "detectron2" for d in all_deps)

    cuda_sensitive = [n for n, ok in [
        ("flash-attn", has_flash_attn), ("xformers", has_xformers),
        ("deepspeed", has_deepspeed),
    ] if ok]
    if cuda_sensitive:
        parts.append(f"检测到 {', '.join(cuda_sensitive)} 等 CUDA 敏感依赖，环境配置风险较高")

    if has_mmcv:
        parts.append("检测到 mmcv，需与 PyTorch/CUDA 版本精确匹配")
    if has_detectron2:
        parts.append("检测到 detectron2，安装对 PyTorch/CUDA/编译器版本敏感")

    # 版本未固定
    unpinned = sum(1 for d in all_deps
                   if d.get("source") == "pip"
                   and not d.get("versionSpec")
                   and not d.get("packageName", "").startswith("_meta:"))
    if unpinned > 10:
        parts.append(f"依赖版本大量未固定（{unpinned} 个无版本约束），长期复现风险较高")
    elif unpinned > 3:
        parts.append(f"部分依赖未固定版本（{unpinned} 个），建议锁定关键包版本")

    # Python 版本
    if not python_version:
        parts.append("未检测到明确的 Python 版本约束")

    # CUDA
    if not cuda_version:
        if requires_gpu:
            parts.append("需要 GPU 但未检测到 CUDA 版本，环境复现存在不确定性")
        else:
            parts.append("未发现明确 CUDA 依赖，可能支持 CPU 环境或 README 未说明 GPU 要求")
    else:
        parts.append(f"CUDA 版本线索：{cuda_version}")

    # Docker
    if not has_docker:
        parts.append("缺少 Dockerfile，环境复现难度增加")

    return "；".join(parts) if parts else "环境风险较低，依赖清晰"


def _build_install_advice(python_version: str, framework: str, framework_version: str,
                          cuda_version: str, requires_gpu: bool, has_docker: bool,
                          dep_count: int, all_deps: List[Dict]) -> str:
    """生成安装建议"""
    lines = []

    # 检测环境文件类型
    has_env_yml = any(d.get("filePath", "").endswith((".yml", ".yaml"))
                      and d.get("source") in ("conda", "pip")
                      for d in all_deps)
    has_requirements = any(d.get("source") == "pip" and not d.get("packageName", "").startswith("_meta:")
                           for d in all_deps)

    # 如果有 Docker：优先 Docker
    if has_docker:
        lines.append("1. 优先尝试 Docker 部署（检测到 Dockerfile）")
        if python_version:
            lines.append(f"2. 确认 Python 版本为 {python_version}")
        if cuda_version:
            lines.append(f"3. Docker 基础镜像已包含 CUDA {cuda_version}")
        if framework:
            fw_str = f"4. 安装 {framework}"
            if framework_version:
                fw_str += f" {framework_version}"
            lines.append(fw_str)
        else:
            lines.append("4. 识别主框架后安装")
        return "\n".join(lines)

    # 如果有 environment.yml：优先 Conda
    if has_env_yml:
        if python_version:
            lines.append(f"1. 使用 Conda 创建 Python {python_version} 环境")
        else:
            lines.append("1. 使用 Conda 创建虚拟环境")
        if cuda_version:
            lines.append(f"2. 安装 CUDA {cuda_version}（通过 conda 的 cudatoolkit/cuda-version）")
        if framework:
            fw_str = f"3. 安装 {framework}"
            if framework_version:
                fw_str += f" {framework_version}"
            lines.append(fw_str)
        lines.append("4. 使用 `conda env create -f environment.yml` 一键安装")
        return "\n".join(lines)

    # 如果只有 requirements.txt：建议 venv + pip
    if python_version:
        lines.append(f"1. 新建 Python {python_version} 虚拟环境")
    else:
        lines.append("1. 建议先查看 README 或 issues 确认 Python 版本")
        lines.append("2. 新建虚拟环境（建议 Python 3.10/3.11）")

    if framework:
        fw_str = f"{len(lines)+1}. 安装 {framework}"
        if framework_version:
            fw_str += f" {framework_version}"
        lines.append(fw_str)
    else:
        lines.append(f"{len(lines)+1}. 识别主深度学习框架后安装")

    if cuda_version:
        lines.append(f"{len(lines)+1}. 安装 CUDA {cuda_version}（确保 GPU 驱动兼容）")
    elif requires_gpu:
        lines.append(f"{len(lines)+1}. 需要 GPU 计算，建议确认 CUDA/PyTorch 匹配关系")

    lines.append(f"{len(lines)+1}. 使用 pip install -r requirements.txt 安装其余 {dep_count} 个依赖")

    return "\n".join(lines)
