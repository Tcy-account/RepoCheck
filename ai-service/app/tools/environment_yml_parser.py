"""
environment.yml 解析器

使用 PyYAML 解析 conda 环境文件，提取：
  - channels（nvidia/pytorch 作为 CUDA/PyTorch 线索）
  - Python 版本（dependencies 中的 python=3.10）
  - CUDA 版本（cudatoolkit=11.8 / cuda-version=12.1）
  - conda 依赖列表
  - pip 依赖列表

输出：
  - dependencies (List[Dict])：所有依赖项（含 source=conda/pip）
  - metadata (Dict)：{pythonVersion, cudaVersion, channels, hasNvidiaChannel, hasPytorchChannel}
"""

import re
from typing import List, Dict, Tuple, Optional
from app.core.logger import logger

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False
    logger.warning("PyYAML not installed; environment.yml parsing will fall back to regex-based parser")


def parse_environment_yml(content: str, file_path: str = "environment.yml") -> Tuple[List[Dict], Dict]:
    """
    解析 environment.yml。

    Returns: (dependencies, metadata)
        metadata: {pythonVersion, cudaVersion, channels, hasNvidiaChannel, hasPytorchChannel}
    """
    if _HAS_YAML:
        return _parse_with_yaml(content, file_path)
    else:
        logger.warning(f"environment_yml_parser: PyYAML unavailable, using regex fallback for {file_path}")
        return _parse_legacy(content, file_path)


def _parse_with_yaml(content: str, file_path: str) -> Tuple[List[Dict], Dict]:
    """使用 PyYAML 解析"""
    deps: List[Dict] = []
    metadata: Dict = {
        "pythonVersion": None,
        "cudaVersion": None,
        "channels": [],
        "hasNvidiaChannel": False,
        "hasPytorchChannel": False,
    }

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"environment_yml_parser: YAML parse error for {file_path}: {e}")
        return _parse_legacy(content, file_path)

    if not isinstance(data, dict):
        logger.warning(f"environment_yml_parser: unexpected YAML structure in {file_path}")
        return deps, metadata

    # ── channels ──
    raw_channels = data.get("channels", [])
    if isinstance(raw_channels, list):
        metadata["channels"] = [str(c).lower() for c in raw_channels]
        for ch in metadata["channels"]:
            if "nvidia" in ch:
                metadata["hasNvidiaChannel"] = True
            if "pytorch" in ch or "conda-forge" in ch:
                metadata["hasPytorchChannel"] = True

    # ── dependencies ──
    dep_list = data.get("dependencies", [])
    if not isinstance(dep_list, list):
        return deps, metadata

    pip_items = []  # pip 子依赖收集

    for item in dep_list:
        # pip 子依赖：{pip: [pkg1, pkg2, ...]}
        if isinstance(item, dict) and "pip" in item:
            pip_raw = item["pip"]
            if isinstance(pip_raw, list):
                for pip_dep in pip_raw:
                    if isinstance(pip_dep, str):
                        pkg, ver = _split_package_version(pip_dep)
                        pip_items.append({
                            "filePath": file_path,
                            "packageName": pkg.lower(),
                            "versionSpec": ver,
                            "source": "pip",
                            "riskLevel": None,
                            "riskReason": None,
                        })
            continue

        # 字符串依赖：package=version
        if isinstance(item, str):
            pkg, ver = _split_conda_version(item)
            if not pkg:
                continue

            pkg_lower = pkg.lower()

            # 跳过 pip 依赖项本身（它会在 pip 子段中解析）
            if pkg_lower == "pip":
                continue

            # 检测 python 版本
            if pkg_lower == "python":
                if ver:
                    metadata["pythonVersion"] = ver

            # 检测 cuda 版本（包括 cudatoolkit 和 cuda-version）
            elif pkg_lower in ("cudatoolkit", "cuda"):
                if ver:
                    metadata["cudaVersion"] = ver
                else:
                    metadata["cudaVersion"] = f"from {pkg_lower}"
            elif pkg_lower == "cuda-version":
                if ver:
                    metadata["cudaVersion"] = ver
                else:
                    metadata["cudaVersion"] = "from cuda-version"

            deps.append({
                "filePath": file_path,
                "packageName": pkg_lower,
                "versionSpec": ver,
                "source": "conda",
                "riskLevel": None,
                "riskReason": None,
            })

    # 如果有 pip 但没有 pip 子项，不追加空依赖
    # pip_items 已在循环中收集
    deps.extend(pip_items)

    logger.info(f"environment_yml_parser: {file_path} → {len(deps)} dependencies "
                f"(conda={len(deps)-len(pip_items)}, pip={len(pip_items)}, "
                f"python={metadata['pythonVersion']}, cuda={metadata['cudaVersion']}, "
                f"channels={metadata['channels']})")
    return deps, metadata


def _split_conda_version(dep_str: str) -> Tuple[Optional[str], Optional[str]]:
    """解析 conda 格式：package=version 或 package==version"""
    # 优先级：== > =
    if "==" in dep_str:
        parts = dep_str.split("==", 1)
        return parts[0].strip(), parts[1].strip()
    if "=" in dep_str:
        parts = dep_str.split("=", 1)
        return parts[0].strip(), parts[1].strip()
    return dep_str.strip(), None


def _split_package_version(dep_str: str) -> Tuple[str, Optional[str]]:
    """解析 pip 格式：package==version 或 package>=version"""
    match = re.split(r'([><!~=]+)', dep_str, maxsplit=1)
    if len(match) > 1:
        return match[0].strip(), "".join(match[1:]).strip()
    return dep_str.strip(), None


# ───────────────────── Legacy parser (no PyYAML) ─────────────────────

def _parse_legacy(content: str, file_path: str) -> Tuple[List[Dict], Dict]:
    """无 PyYAML 时的正则版后备解析器"""
    deps: List[Dict] = []
    metadata: Dict = {
        "pythonVersion": None,
        "cudaVersion": None,
        "channels": [],
        "hasNvidiaChannel": False,
        "hasPytorchChannel": False,
    }
    in_deps = False
    in_pip = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # channels
        if line.startswith("- ") and not in_deps:
            ch_line = line[2:].strip().lower()
            if ch_line and "://" not in ch_line and "defaults" not in ch_line:
                # 可能是 channels 列表中的项
                metadata["channels"].append(ch_line)
                if "nvidia" in ch_line:
                    metadata["hasNvidiaChannel"] = True
                if "pytorch" in ch_line:
                    metadata["hasPytorchChannel"] = True

        # 检测 dependencies: 段
        if line.startswith("dependencies:") or line == "dependencies:":
            in_deps = True
            continue

        # pip 子段
        if in_deps and line.strip() in ("- pip:", "- pip"):
            in_pip = True
            continue
        if in_deps and line.startswith("- pip:"):
            in_pip = True
            continue

        if not in_deps:
            continue

        # 顶级非依赖 key → 退出 dependencies 段
        if not line.startswith("-") and not line.startswith(" ") and ":" in line:
            in_deps = False
            in_pip = False
            continue

        dep_line = line.lstrip("- ").strip()
        if not dep_line or dep_line.startswith("#"):
            continue

        if in_pip:
            if dep_line == "pip" or dep_line == "pip:":
                continue
            pkg, ver = _split_package_version(dep_line)
            if pkg:
                deps.append({
                    "filePath": file_path,
                    "packageName": pkg.lower(),
                    "versionSpec": ver,
                    "source": "pip",
                    "riskLevel": None,
                    "riskReason": None,
                })
        else:
            if dep_line.lower() == "pip":
                in_pip = True
                continue
            pkg, ver = _split_conda_version(dep_line)
            if pkg:
                pkg_lower = pkg.lower()
                if pkg_lower == "python" and ver:
                    metadata["pythonVersion"] = ver
                elif pkg_lower in ("cudatoolkit", "cuda", "cuda-version"):
                    metadata["cudaVersion"] = ver or f"from {pkg_lower}"

                deps.append({
                    "filePath": file_path,
                    "packageName": pkg_lower,
                    "versionSpec": ver,
                    "source": "conda",
                    "riskLevel": None,
                    "riskReason": None,
                })

    logger.info(f"environment_yml_parser (legacy): {file_path} → {len(deps)} dependencies")
    return deps, metadata
