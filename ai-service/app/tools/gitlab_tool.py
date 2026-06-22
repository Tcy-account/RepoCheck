"""
GitLab 工具 — 搜索代码仓库

V1: mock 实现
TODO: 接入 GitLab API
"""

from typing import List
from app.core.logger import logger


def search_gitlab_repos(
    paper_title: str,
    arxiv_id: str,
) -> List[dict]:
    """
    在 GitLab 搜索相关仓库

    V1: 返回空列表（占位）
    """
    logger.info(f"Searching GitLab for: {paper_title}")

    # TODO: 调用 GitLab API
    # headers = {"PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN")}
    # ...

    return []
