"""
Dockerfile 解析器

用正则规则解析 Dockerfile，提取：
  - FROM 基础镜像
  - nvidia/cuda / python 镜像中的版本信息
  - pip install 后的包（含 -r 引用检测）
  - conda install 后的包（含 python/cuda 版本提取）
  - apt-get install 后的系统依赖
  - 多行续行（\\ 结尾行合并）

输出：
  - dependencies (List[Dict])
  - metadata (Dict)：{dockerBaseImage, cudaVersion, pythonVersion, channels,
                       hasDocker=true}
"""

import re
from typing import List, Dict, Tuple
from app.core.logger import logger

_FROM_PATTERN = re.compile(r'^FROM\s+(\S+)', re.IGNORECASE)
_CUDA_IMG_PATTERN = re.compile(r'(nvidia/)?cuda[:\-]?\s*(\d+\.\d+)', re.IGNORECASE)

_PYTHON_VERSION_PATTERNS = [
    re.compile(r'python[:=]\s*(\d+\.\d+)', re.IGNORECASE),
    re.compile(r'python(\d+\.\d+)', re.IGNORECASE),
    re.compile(r'FROM\s+python:(\d+\.\d+)', re.IGNORECASE),
]

_PIP_PKG_PATTERN = re.compile(r'([\w.\-_]+)([><!~=]+\S+)?')

_PIP_EXCLUDE_WORDS = {
    "-r", "--requirement", "--index-url", "--extra-index-url", "--find-links",
    "-i", "-f", "--trusted-host", "--no-deps", "--upgrade", "-U", "--user",
    "--no-cache-dir", ".", "-e", "--editable",
}

# apt 包中 HIGH risk 关键词
_APT_HIGH_RISK_KEYWORDS = {"cuda", "nvidia", "nvidia-driver", "driver", "cudnn"}


def parse_dockerfile(content: str, file_path: str = "Dockerfile") -> Tuple[List[Dict], Dict]:
    """
    解析 Dockerfile。

    Returns: (dependencies, metadata)
        metadata: {dockerBaseImage, cudaVersion, pythonVersion, hasDocker, channels}
    """
    deps: List[Dict] = []
    metadata: Dict = {
        "dockerBaseImage": None,
        "cudaVersion": None,
        "pythonVersion": None,
        "hasDocker": True,
        "channels": [],
    }

    # 将多行续行合并
    merged_text = _merge_continuation_lines(content)

    for line in merged_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # ── FROM 行 ──
        from_match = _FROM_PATTERN.match(stripped)
        if from_match:
            image = from_match.group(1)
            as_match = re.search(r'\s+(?:AS|as)\s+(\S+)', image)
            if as_match:
                image = image[:as_match.start()].strip()

            if metadata["dockerBaseImage"] is None:
                metadata["dockerBaseImage"] = image

            deps.append({
                "filePath": file_path,
                "packageName": image,
                "versionSpec": None,
                "source": "docker",
                "riskLevel": None,
                "riskReason": None,
            })

            # CUDA 版本
            if metadata["cudaVersion"] is None:
                cuda_match = _CUDA_IMG_PATTERN.search(image)
                if cuda_match:
                    metadata["cudaVersion"] = cuda_match.group(2)

            # Python 版本
            if metadata["pythonVersion"] is None:
                for pat in _PYTHON_VERSION_PATTERNS:
                    py_match = pat.search(image)
                    if py_match:
                        metadata["pythonVersion"] = py_match.group(1)
                        break
            continue

        # ── ENV PYTHON_VERSION ──
        if metadata["pythonVersion"] is None and "python" in stripped.lower():
            py_env = re.search(r'PYTHON_VERSION[= ]+(\d+\.\d+)', stripped, re.IGNORECASE)
            if py_env:
                metadata["pythonVersion"] = py_env.group(1)

        # ── RUN pip install ──
        if "pip" in stripped.lower() and "install" in stripped:
            _extract_pip_packages(stripped, file_path, deps)

        # ── RUN conda install ──
        if "conda" in stripped.lower() and "install" in stripped:
            _extract_conda_packages(stripped, file_path, deps, metadata)

        # ── RUN apt-get install ──
        if "apt-get" in stripped and "install" in stripped:
            _extract_apt_packages(stripped, file_path, deps)

    logger.info(f"dockerfile_parser: {file_path} → {len(deps)} deps, "
                f"image={metadata['dockerBaseImage']}, "
                f"cuda={metadata['cudaVersion']}, python={metadata['pythonVersion']}")
    return deps, metadata


def _merge_continuation_lines(content: str) -> str:
    """合并以 \\  结尾的多行"""
    lines = content.splitlines()
    merged = []
    buf = ""
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
        else:
            buf += stripped
            merged.append(buf)
            buf = ""
    if buf:
        merged.append(buf)
    return "\n".join(merged)


def _extract_pip_packages(line: str, file_path: str, deps: List[Dict]):
    """从 pip install 行提取包名"""
    pip_part = _get_after_install(line, "pip install") or _get_after_install(line, "pip3 install")
    if not pip_part:
        return

    # 去掉 && 及其后面
    if "&&" in pip_part:
        pip_part = pip_part.split("&&")[0]

    for match in _PIP_PKG_PATTERN.finditer(pip_part):
        pkg = match.group(1).lower()
        ver = match.group(2)

        if pkg in _PIP_EXCLUDE_WORDS or len(pkg) < 2:
            continue

        # -r / --requirement → include
        if pkg in ("-r", "--requirement"):
            deps.append({
                "filePath": file_path,
                "packageName": ver.strip() if ver else "unknown-requirements-file",
                "versionSpec": None,
                "source": "include",
                "riskLevel": "MEDIUM",
                "riskReason": "References another requirements file; dependency list may be incomplete",
            })
            continue

        deps.append({
            "filePath": file_path,
            "packageName": pkg,
            "versionSpec": ver.strip() if ver else None,
            "source": "pip",
            "riskLevel": None,
            "riskReason": None,
        })


def _get_after_install(line: str, cmd: str) -> str:
    """从 install 命令后提取包名部分"""
    pos = line.lower().find(cmd)
    if pos < 0:
        return None
    rest = line[pos + len(cmd):].strip()
    # 跳过 pip options（以 - 开头）
    words = rest.split()
    result_words = []
    for w in words:
        if w.startswith("-") and len(w) > 1:
            continue
        result_words.append(w)
    return " ".join(result_words)


def _extract_conda_packages(line: str, file_path: str, deps: List[Dict], metadata: Dict):
    """从 conda install 行提取包名，同时提取 python/cuda 版本"""
    conda_part = _get_after_install(line, "conda install")
    if not conda_part:
        return

    if "&&" in conda_part:
        conda_part = conda_part.split("&&")[0]

    for word in conda_part.split():
        word = word.strip().strip("\\")
        if not word or word.startswith("-") or len(word) < 2:
            continue

        # conda 格式：package=version
        if "=" in word:
            parts = word.split("=", 1)
            pkg = parts[0].lower()
            ver = parts[1]
        else:
            pkg = word.lower()
            ver = None

        # 提取 python/cuda 版本
        if pkg == "python" and ver and not metadata["pythonVersion"]:
            metadata["pythonVersion"] = ver
        elif pkg in ("cudatoolkit", "cuda", "cuda-version") and not metadata["cudaVersion"]:
            metadata["cudaVersion"] = ver or f"from {pkg}"

        deps.append({
            "filePath": file_path,
            "packageName": pkg,
            "versionSpec": ver,
            "source": "conda",
            "riskLevel": None,
            "riskReason": None,
        })


def _extract_apt_packages(line: str, file_path: str, deps: List[Dict]):
    """从 apt-get install 行提取系统包名，评估风险"""
    install_match = re.search(
        r'apt-get\s+(?:-[-\w]+\s+)*install\s+(?:-[-\w]+\s+)*(.+)',
        line, re.IGNORECASE,
    )
    if not install_match:
        return

    pkg_part = install_match.group(1)
    if "&&" in pkg_part:
        pkg_part = pkg_part.split("&&")[0]

    for word in pkg_part.split():
        word = word.strip().strip("\\")
        if not word or word.startswith("-") or len(word) < 2:
            continue

        pkg = word.lower()
        is_high = any(kw in pkg for kw in _APT_HIGH_RISK_KEYWORDS)

        deps.append({
            "filePath": file_path,
            "packageName": pkg,
            "versionSpec": None,
            "source": "apt",
            "riskLevel": "MEDIUM" if is_high else "LOW",
            "riskReason": "System dependency with CUDA/NVIDIA requirement" if is_high else None,
        })
