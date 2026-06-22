"""
pyproject.toml 解析器

使用 Python 3.11+ 标准库 tomllib 解析 pyproject.toml 和 setup.py。

提取：
  - project.requires-python → pythonVersion
  - project.dependencies → PEP 621 依赖列表
  - project.optional-dependencies → 按组解析，source=pyproject-optional
  - tool.poetry.dependencies → Poetry 依赖（含 ^/>=/< 等）
  - tool.poetry.group.*.dependencies → Poetry group 依赖

输出：
  - dependencies (List[Dict])
  - metadata (Dict)：{pythonVersion}
"""

import re
import sys
from typing import List, Dict, Tuple
from app.core.logger import logger

if sys.version_info >= (3, 11):
    import tomllib
    _HAS_TOMLIB = True
else:
    _HAS_TOMLIB = False
    logger.warning("tomllib requires Python 3.11+; pyproject.toml will use regex fallback")


_VERSION_SPEC = re.compile(r'([><!~=]+\s*[\d*][\d.*]*(\*|\.\*)?)')
_PYTHON_REQ_PATTERN = re.compile(r'requires-python\s*=\s*"([^"]+)"', re.IGNORECASE)


def parse_pyproject(content: str, file_path: str = "pyproject.toml") -> Tuple[List[Dict], Dict]:
    """
    解析 pyproject.toml 或 setup.py。

    Returns: (dependencies, metadata)
    """
    if _HAS_TOMLIB and file_path.endswith(".toml"):
        return _parse_toml(content, file_path)
    else:
        return _parse_regex(content, file_path)


def _parse_toml(content: str, file_path: str) -> Tuple[List[Dict], Dict]:
    """使用 tomllib 解析"""
    deps: List[Dict] = []
    metadata: Dict = {"pythonVersion": None}

    try:
        data = tomllib.loads(content)
    except Exception as e:
        logger.error(f"pyproject_parser: TOML parse error for {file_path}: {e}")
        return _parse_regex(content, file_path)

    # ── [project] PEP 621 ──
    project = data.get("project", {})
    if isinstance(project, dict):
        requires_python = project.get("requires-python")
        if requires_python:
            metadata["pythonVersion"] = str(requires_python)

        # project.dependencies
        project_deps = project.get("dependencies", [])
        if isinstance(project_deps, list):
            _extract_pep508_deps(project_deps, file_path, deps, source="pip")

        # project.optional-dependencies
        optional_deps = project.get("optional-dependencies", {})
        if isinstance(optional_deps, dict):
            for group_name, group_deps in optional_deps.items():
                if isinstance(group_deps, list):
                    _extract_pep508_deps(
                        group_deps, file_path, deps,
                        source="pyproject-optional",
                        group=group_name,
                    )

    # ── [tool.poetry] ──
    poetry = data.get("tool", {}).get("poetry", {})
    if isinstance(poetry, dict):
        # tool.poetry.dependencies
        poetry_deps = poetry.get("dependencies", {})
        if isinstance(poetry_deps, dict):
            _extract_poetry_deps(poetry_deps, file_path, deps, metadata, source="pip")

        # tool.poetry.group.*.dependencies
        poetry_groups = poetry.get("group", {})
        if isinstance(poetry_groups, dict):
            for group_name, group_cfg in poetry_groups.items():
                if isinstance(group_cfg, dict):
                    group_deps = group_cfg.get("dependencies", {})
                    if isinstance(group_deps, dict):
                        _extract_poetry_deps(
                            group_deps, file_path, deps, metadata={},
                            source="pyproject-optional",
                            group=group_name,
                        )

    logger.info(f"pyproject_parser: {file_path} → {len(deps)} dependencies "
                f"(python={metadata['pythonVersion']})")
    return deps, metadata


def _extract_pep508_deps(dep_strings: List[str], file_path: str, deps: List[Dict],
                         source: str = "pip", group: str = None):
    """解析 PEP 508 格式的依赖字符串列表"""
    for raw in dep_strings:
        if not isinstance(raw, str):
            continue
        # 去掉环境标记 "; python_version > '3.7'"
        env_info = None
        if ";" in raw:
            raw, env_info = raw.split(";", 1)
            raw = raw.strip()

        # 处理 extras：package[extra]...
        extras = None
        extras_match = re.match(r'^([\w.\-]+)\[(.+?)\]', raw)
        if extras_match:
            extras = extras_match.group(2)
            raw = raw[extras_match.end():].strip()
            if not raw:
                # 只有 package[extras] 无版本
                deps.append({
                    "filePath": file_path,
                    "packageName": extras_match.group(1).lower(),
                    "versionSpec": f"[{extras}]" if extras else None,
                    "source": source,
                    "riskLevel": None,
                    "riskReason": f"Optional dependency group: {group}" if group else None,
                })
                continue
        else:
            extras_match = None

        parts = _VERSION_SPEC.split(raw, maxsplit=1)
        if len(parts) == 1:
            pkg = parts[0].strip()
            ver = None
        else:
            pkg = parts[0].strip()
            ver = "".join(p for p in parts[1:] if p).strip()

        if extras and pkg and pkg == extras_match.group(1):
            pass  # packageName already correct

        if pkg:
            if extras and ver:
                ver = f"[{extras}]{ver}"
            elif extras:
                ver = f"[{extras}]"

            deps.append({
                "filePath": file_path,
                "packageName": pkg.lower(),
                "versionSpec": ver or None,
                "source": source,
                "riskLevel": None,
                "riskReason": f"Optional dependency group: {group}" if group else None,
            })


def _extract_poetry_deps(poetry_deps: dict, file_path: str, deps: List[Dict],
                         metadata: Dict, source: str = "pip", group: str = None):
    """解析 Poetry 格式依赖"""
    for pkg, spec in poetry_deps.items():
        if pkg.lower() == "python":
            if spec:
                metadata["pythonVersion"] = str(spec).strip('"').strip("'")
            continue

        version_spec = None
        if isinstance(spec, str):
            version_spec = spec.strip('"').strip("'")
        elif isinstance(spec, dict):
            version_spec = spec.get("version")
            if version_spec:
                version_spec = str(version_spec).strip('"').strip("'")

        risk_reason = None
        if group:
            risk_reason = f"Poetry optional dependency group: {group}"

        deps.append({
            "filePath": file_path,
            "packageName": pkg.lower(),
            "versionSpec": version_spec,
            "source": source,
            "riskLevel": None,
            "riskReason": risk_reason,
        })


def _parse_regex(content: str, file_path: str) -> Tuple[List[Dict], Dict]:
    """正则后备解析器"""
    deps: List[Dict] = []
    metadata: Dict = {"pythonVersion": None}

    # 提取 requires-python
    match = _PYTHON_REQ_PATTERN.search(content)
    if match:
        metadata["pythonVersion"] = match.group(1)

    # 提取所有 dependencies = [...] 和 install_requires = [...] 块
    dep_block_pattern = re.compile(
        r'(?:dependencies|install_requires)\s*=\s*\[(.*?)\]',
        re.DOTALL | re.IGNORECASE,
    )
    for dep_block in dep_block_pattern.finditer(content):
        block = dep_block.group(1)
        for m in re.finditer(r'"([^"]*)"', block):
            raw = m.group(1)
            if raw.startswith("#"):
                continue
            if ";" in raw:
                raw = raw.split(";", 1)[0].strip()

            # 处理 extras
            extras_match = re.match(r'^([\w.\-]+)\[(.+?)\]', raw)
            if extras_match:
                pkg = extras_match.group(1).lower()
                extras = extras_match.group(2)
                rest = raw[extras_match.end():].strip()
                if rest:
                    parts = _VERSION_SPEC.split(rest, maxsplit=1)
                    ver = "".join(p for p in parts[1:] if p).strip() if len(parts) > 1 else None
                    ver = f"[{extras}]{ver}" if ver else f"[{extras}]"
                else:
                    ver = f"[{extras}]"
            else:
                parts = _VERSION_SPEC.split(raw, maxsplit=1)
                pkg = parts[0].strip().lower()
                ver = "".join(p for p in parts[1:] if p).strip() if len(parts) > 1 else None

            if pkg:
                deps.append({
                    "filePath": file_path,
                    "packageName": pkg,
                    "versionSpec": ver or None,
                    "source": "pip",
                    "riskLevel": None,
                    "riskReason": None,
                })

    logger.info(f"pyproject_parser (regex): {file_path} → {len(deps)} dependencies")
    return deps, metadata
