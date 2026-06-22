"""
依赖文件读取工具 — 从 GitHub 仓库读取所有依赖相关文件

复用 repo_file_tool.py 中的 GitHub API 能力：
  - _build_headers()
  - _fetch_file_content_via_api()
  - fetch_repo_file_tree()

输入：owner, repoName, defaultBranch
输出：[{fileType, filePath, content}, ...]

不 clone、不下载 zip，只用 GitHub Contents API。
单文件最多读取 50000 字符。
GitHub API 失败不抛异常，返回空文件并在风险中体现。
"""

import re
from typing import List, Dict, Optional
from app.tools.repo_file_tool import (
    fetch_repo_file_tree,
    _fetch_file_content_via_api,
)
from app.core.logger import logger

MAX_DEPENDENCY_FILE_CHARS = 50000

# ───────────────────── 目标文件模式 ─────────────────────

# 需要读取的依赖文件列表（路径模式 → fileType）
_TARGET_FILES = [
    # requirements 系列（优先级：根目录 > 子目录）
    (re.compile(r"^requirements\.txt$", re.IGNORECASE), "requirements"),
    (re.compile(r"^requirements-dev\.txt$", re.IGNORECASE), "requirements"),
    (re.compile(r"^requirements/.*\.txt$", re.IGNORECASE), "requirements"),
    # environment 系列
    (re.compile(r"^(environment|conda)\.(yml|yaml)$", re.IGNORECASE), "environment_yml"),
    # pyproject.toml
    (re.compile(r"^pyproject\.toml$", re.IGNORECASE), "pyproject"),
    # setup.py
    (re.compile(r"^setup\.py$", re.IGNORECASE), "pyproject"),
    # Dockerfile（根目录和 docker/ 子目录）
    (re.compile(r"^Dockerfile([.\-_].*)?$", re.IGNORECASE), "dockerfile"),
    (re.compile(r"^docker/Dockerfile([.\-_].*)?$", re.IGNORECASE), "dockerfile"),
]


def fetch_dependency_files(
    owner: str,
    repo_name: str,
    default_branch: str = "main",
    file_list: Optional[List[str]] = None,
) -> List[Dict]:
    """
    读取仓库中所有依赖相关文件。

    Args:
        owner: 仓库 owner
        repo_name: 仓库名
        default_branch: 分支名
        file_list: 已知文件列表（可选，避免重复请求文件树）

    Returns:
        [{fileType, filePath, content}, ...]
        失败时返回空列表，不抛异常
    """
    logger.info(f"dependency_file_tool: scanning {owner}/{repo_name} branch={default_branch}")

    # 获取或使用传入的文件列表
    if file_list is None:
        tree = fetch_repo_file_tree(owner, repo_name, default_branch)
        file_list = tree.get("files", [])
        if tree.get("error"):
            logger.warning(f"dependency_file_tool: file tree error: {tree['error']}")

    if not file_list:
        logger.warning(f"dependency_file_tool: no files found for {owner}/{repo_name}")
        return []

    # 筛选需要读取的依赖文件
    candidates: Dict[str, str] = {}  # fileType -> filePath（每种只取优先级最高的一条）
    for file_path in file_list:
        file_name = file_path.split("/")[-1]
        file_depth = file_path.count("/")

        for pattern, ftype in _TARGET_FILES:
            if pattern.search(file_name):
                key = f"{ftype}:{file_name}"
                # 只保留根目录（深度更浅）的版本
                if key not in candidates or file_depth < candidates[key].count("/"):
                    candidates[key] = file_path
                break

    logger.info(f"dependency_file_tool: found {len(candidates)} candidate files: {list(candidates.values())}")

    # 读取文件内容
    results: List[Dict] = []
    for key, file_path in sorted(candidates.items()):
        ftype = key.split(":", 1)[0]

        logger.info(f"dependency_file_tool: reading {file_path} (type={ftype})")
        result = _fetch_file_content_via_api(owner, repo_name, file_path, default_branch)

        if result.get("error"):
            logger.warning(f"dependency_file_tool: failed to read {file_path}: {result['error']}")
            continue

        content = result.get("content", "")
        if not content:
            logger.warning(f"dependency_file_tool: empty content for {file_path}")
            continue

        # 截断
        if len(content) > MAX_DEPENDENCY_FILE_CHARS:
            logger.info(f"dependency_file_tool: truncating {file_path} from {len(content)} to {MAX_DEPENDENCY_FILE_CHARS} chars")
            content = content[:MAX_DEPENDENCY_FILE_CHARS]

        results.append({
            "fileType": ftype,
            "filePath": file_path,
            "content": content,
        })

    logger.info(f"dependency_file_tool: done, read {len(results)} files")
    return results
