"""
requirements.txt 解析器

解析 pip requirements 格式，提取包名和版本声明。

支持：
  - torch==2.1.0
  - numpy>=1.23
  - opencv-python
  - transformers>=4.30,<5
  - 行内注释 (# ...)
  - 空行和纯注释跳过
  - extras: uvicorn[standard]>=0.23
  - git 依赖: git+https://github.com/user/repo.git
  - -r / --requirement 引用（不递归，生成元条目）
  - --extra-index-url / --index-url / -f / --find-links（生成元条目）
  - editable 安装: -e .
  - 本地路径依赖: ./src, ../package

输出 dependency list。
"""

import re
from typing import List, Dict
from app.core.logger import logger

# 版本声明正则
_VERSION_SPEC = re.compile(r'([><!~=]+\s*[\d*][\d.*]*(?:\*|\.\*)?)')

# git 依赖正则
_GIT_PATTERN = re.compile(r'^git\+https?://')

# extras 正则：package[extra1,extra2]
_EXTRAS_PATTERN = re.compile(r'^([\w.\-]+)\[(.+?)\]')

# 本地路径正则
_LOCAL_PATH_PATTERN = re.compile(r'^(\.\.?/|file://)')

# pip option 前缀
_PIP_OPTIONS = ("--index-url", "--extra-index-url", "--find-links",
                "-f", "-i", "--trusted-host", "--no-deps",
                "--upgrade", "--upgrade-strategy", "--no-cache-dir",
                "--force-reinstall", "--ignore-installed",
                "--no-deps", "--no-build-isolation",
                "--config-settings", "--progress-bar",
                "-U", "--user", "--target", "--root",
                "--constraint", "-c", "--pre", "--require-hashes",
                "--only-binary", "--no-binary",
                "--proxy", "--retries", "--timeout",
                "--cert", "--client-cert", "--key",
                "--global-option", "--install-option",
                "--src", "--no-clean", "--no-compile", "--compile",
                "--no-warn-script-location", "--no-warn-conflicts")


def parse_requirements(content: str, file_path: str = "requirements.txt") -> List[Dict]:
    """
    解析 requirements.txt 内容。

    Args:
        content: 文件内容
        file_path: 文件路径

    Returns:
        依赖列表，每个元素含 packageName/versionSpec/source/filePath/riskLevel/riskReason
    """
    deps: List[Dict] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过纯注释
        if line.startswith("#"):
            continue

        # ── 处理行内注释（提前去掉）──
        # 匹配 空格+#  或  ; #
        comment_pos = -1
        # 不能误删 URL 中的 #，所以只匹配开头非 URL 的情况
        for m in re.finditer(r'\s+#\s*', line):
            if m.start() > 0:
                comment_pos = m.start()
                break
        if comment_pos > 0:
            line = line[:comment_pos].strip()

        if not line:
            continue

        # ── editable 安装 (-e ...) ──
        if line.startswith("-e ") or line.startswith("--editable "):
            src = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else line[3:]
            src = src.strip()
            _handle_editable(src, file_path, deps)
            continue

        # ── pip option 行 ──
        if line.startswith("-") or line.startswith("--"):
            handled = _handle_option_line(line, file_path, deps)
            if handled:
                continue
            # 未识别的 option 跳过
            continue

        # ── 普通依赖解析 ──
        _parse_regular_dep(line, file_path, deps)

    logger.info(f"requirements_parser: {file_path} → {len(deps)} entries")
    return deps


def _parse_regular_dep(line: str, file_path: str, deps: List[Dict]):
    """解析普通依赖行：pkg[extras] version_spec"""
    # 先分离可能的前缀（git+、路径）
    if _GIT_PATTERN.match(line):
        _handle_git_dep(line, file_path, deps)
        return

    if _LOCAL_PATH_PATTERN.match(line):
        name = line.rstrip("/").split("/")[-1] or "local-package"
        deps.append({
            "filePath": file_path,
            "packageName": name,
            "versionSpec": None,
            "source": "local",
            "riskLevel": "HIGH",
            "riskReason": "Local path dependency may not be reproducible outside repository context",
        })
        return

    # 提取 extras：package[extra]...
    extras = None
    extras_match = _EXTRAS_PATTERN.match(line)
    working = line
    if extras_match:
        extras = extras_match.group(2)
        # 去掉 extras 部分继续解析版本
        working = line[extras_match.end():].strip()
        # 如果 working 为空，使用包名继续
        if not working:
            # 整行就是 package[extras]
            pkg = extras_match.group(1).lower()
            deps.append({
                "filePath": file_path,
                "packageName": pkg,
                "versionSpec": f"[{extras}]" if extras else None,
                "source": "pip",
                "riskLevel": None,
                "riskReason": None,
            })
            return
    else:
        pkg = None

    # 用版本声明切分
    parts = _VERSION_SPEC.split(working, maxsplit=1)
    if len(parts) == 1:
        pkg = parts[0].strip().lower() if not extras_match else extras_match.group(1).lower()
        version_spec = f"[{extras}]" if extras else None
    else:
        pkg = parts[0].strip().lower() if not extras_match else extras_match.group(1).lower()
        version_spec = "".join(p for p in parts[1:] if p).strip()
        if extras:
            version_spec = f"[{extras}]{version_spec}"

    if not pkg:
        return

    deps.append({
        "filePath": file_path,
        "packageName": pkg,
        "versionSpec": version_spec or None,
        "source": "pip",
        "riskLevel": None,
        "riskReason": None,
    })


def _handle_git_dep(line: str, file_path: str, deps: List[Dict]):
    """处理 git+https://... 依赖"""
    # 提取仓库名
    repo_name = "git-package"
    # 尝试从 URL 中提取最后一段作为名称
    url_match = re.search(r'/([^/@]+?)(?:\.git)?(?:@|$)', line)
    if url_match:
        repo_name = url_match.group(1)

    # 提取 egg 名称
    egg_match = re.search(r'#egg=([\w.\-]+)', line)
    if egg_match:
        repo_name = egg_match.group(1)

    deps.append({
        "filePath": file_path,
        "packageName": repo_name,
        "versionSpec": None,
        "source": "git",
        "riskLevel": "MEDIUM",
        "riskReason": "Git dependency may be harder to reproduce because it depends on remote repository state",
    })


def _handle_editable(src: str, file_path: str, deps: List[Dict]):
    """处理 -e 可编辑安装"""
    if _GIT_PATTERN.match(src):
        repo_name = "git-package"
        egg_match = re.search(r'#egg=([\w.\-]+)', src)
        if egg_match:
            repo_name = egg_match.group(1)
        deps.append({
            "filePath": file_path,
            "packageName": repo_name,
            "versionSpec": None,
            "source": "editable",
            "riskLevel": "MEDIUM",
            "riskReason": "Editable git dependency depends on remote repository state",
        })
        return

    if src == ".":
        name = "editable-local-root"
    elif _LOCAL_PATH_PATTERN.match(src):
        name = src.rstrip("/").split("/")[-1] or "editable-local"
    else:
        name = src

    deps.append({
        "filePath": file_path,
        "packageName": name,
        "versionSpec": None,
        "source": "editable",
        "riskLevel": "MEDIUM",
        "riskReason": "Editable installation may not be reproducible outside development environment",
    })


def _handle_option_line(line: str, file_path: str, deps: List[Dict]) -> bool:
    """处理 pip option 行，返回 True 表示已处理"""
    parts = line.split(None, 1)
    option = parts[0]
    value = parts[1] if len(parts) > 1 else ""

    # -r / --requirement
    if option in ("-r", "--requirement"):
        ref_file = value.strip()
        deps.append({
            "filePath": file_path,
            "packageName": ref_file,
            "versionSpec": None,
            "source": "include",
            "riskLevel": "MEDIUM",
            "riskReason": "References another requirements file; dependency list may be incomplete",
        })
        return True

    # --index-url / --extra-index-url / -i / -f / --find-links
    if option in ("--index-url", "--extra-index-url", "-i") or option == "--index-url":
        deps.append({
            "filePath": file_path,
            "packageName": "custom-package-index",
            "versionSpec": value,
            "source": "pip-index",
            "riskLevel": "MEDIUM",
            "riskReason": "Uses custom package index or find-links; installation may depend on external availability",
        })
        return True

    if option in ("-f", "--find-links"):
        deps.append({
            "filePath": file_path,
            "packageName": "custom-package-index",
            "versionSpec": value,
            "source": "pip-index",
            "riskLevel": "MEDIUM",
            "riskReason": "Uses custom package index or find-links; installation may depend on external availability",
        })
        return True

    # 其他已识别的 pip options 直接跳过
    if option in _PIP_OPTIONS:
        return True

    return False
