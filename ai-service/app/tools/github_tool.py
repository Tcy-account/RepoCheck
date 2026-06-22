"""
GitHub 工具 — 搜索代码仓库

通过 GitHub REST API 根据论文信息搜索相关开源仓库。
"""

import os
import re
import requests
from typing import List, Tuple
from app.core.logger import logger

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
REQUEST_TIMEOUT = 10

# 停用词
_STOP_WORDS = {
    "the", "and", "for", "with", "from", "using", "based", "via",
    "paper", "model", "method", "approach", "a", "an", "of", "in",
    "on", "to", "by", "is", "are", "we", "this", "that", "it",
    "as", "or", "not", "its", "can", "has", "have", "been",
    "which", "more", "than", "also", "such",
}


def extract_title_keywords(title: str) -> set:
    """从论文标题中提取关键词"""
    if not title:
        return set()
    # 转小写、去标点、拆分
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]?", title.lower())
    return {w for w in words if len(w) >= 3 and w not in _STOP_WORDS}


def _build_headers() -> dict:
    """构造请求头"""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RepoCheck-AI-Service",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.debug("Using GITHUB_TOKEN for authenticated requests")
    else:
        logger.warning("GITHUB_TOKEN is not set; using unauthenticated GitHub API requests (rate limit: 10/min)")
    return headers


def _do_search_query(query: str) -> List[dict]:
    """执行一次 GitHub repo 搜索，返回 items 列表，失败返回 []"""
    headers = _build_headers()
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 5}
    logger.info(f"GitHub search query: {query}")

    try:
        resp = requests.get(GITHUB_SEARCH_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        logger.error(f"GitHub API request failed: {e}")
        return []

    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        logger.error("GitHub API rate limit exceeded")
        return []
    if resp.status_code in (401, 403):
        logger.error(f"GitHub API returned {resp.status_code}: {resp.text[:200]}")
        return []
    if not resp.ok:
        logger.error(f"GitHub API returned status {resp.status_code}")
        return []

    try:
        data = resp.json()
    except ValueError as e:
        logger.error(f"Failed to parse GitHub API JSON response: {e}")
        return []

    items = data.get("items", [])
    logger.info(f"GitHub search returned {len(items)} results")
    return items


def calculate_repo_confidence(repo: dict, paper_title: str, arxiv_id: str) -> Tuple[float, str]:
    """
    根据规则计算仓库与论文的匹配置信度。

    Returns:
        (confidence, reason)
    """
    name = (repo.get("name") or "").lower()
    desc = (repo.get("description") or "").lower()
    stars = repo.get("stargazers_count", 0)
    pushed = repo.get("pushed_at") or ""
    title_lower = (paper_title or "").lower()
    keywords = extract_title_keywords(paper_title)

    score = 0.3
    reasons = []

    # arxiv_id 匹配
    arxiv_lower = arxiv_id.lower()
    if arxiv_lower in name:
        score += 0.3
        reasons.append("仓库名称中包含 arXiv ID")
    elif arxiv_lower in desc:
        score += 0.2
        reasons.append("描述中包含 arXiv ID")

    # 关键词匹配
    name_keyword_hits = sum(1 for kw in keywords if kw in name)
    desc_keyword_hits = sum(1 for kw in keywords if kw in desc)

    if name_keyword_hits >= 3:
        score += 0.2
        reasons.append("仓库名称与论文标题关键词匹配较多")
    elif name_keyword_hits >= 1:
        score += 0.1

    if desc_keyword_hits >= 3:
        score += 0.1
        reasons.append("描述与论文标题关键词匹配较多")

    # stars 加分
    if stars >= 1000:
        score += 0.2
        reasons.append("star 数超过 1000")
    elif stars >= 100:
        score += 0.1
        reasons.append("star 数超过 100")

    # 最近一年更新
    if pushed and pushed >= "2025-":
        score += 0.1
        reasons.append("最近一年有更新")
    elif pushed and pushed >= "2024-":
        score += 0.05

    score = min(score, 1.0)
    reason = "；".join(reasons) if reasons else "GitHub 搜索结果靠前，但缺少明确论文标识"
    return round(score, 2), reason


def _map_repo_item(item: dict, paper_title: str, arxiv_id: str) -> dict:
    """把 GitHub API item 映射为系统统一格式"""
    confidence, reason = calculate_repo_confidence(item, paper_title, arxiv_id)
    return {
        "platform": "GitHub",
        "repoUrl": item.get("html_url", ""),
        "repoName": item.get("name", ""),
        "owner": item.get("owner", {}).get("login", "") if item.get("owner") else "",
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "defaultBranch": item.get("default_branch", "main"),
        "lastUpdatedAt": item.get("pushed_at") or item.get("updated_at", ""),
        "description": item.get("description") or "",
        "confidence": confidence,
        "confidenceReason": reason,
    }


def search_github_repos(
    paper_title: str,
    arxiv_id: str,
    abstract: str = "",
) -> List[dict]:
    """
    在 GitHub 搜索相关仓库。

    优先用 arxiv_id 搜索，无结果则用论文标题搜索。

    Args:
        paper_title: 论文标题
        arxiv_id: arXiv ID
        abstract: 论文摘要（暂未使用，保留接口）

    Returns:
        List[dict]: 候选仓库列表（最多 5 个），按置信度降序。网络错误或限流时返回 []
    """
    logger.info(f"Searching GitHub for: arxiv_id={arxiv_id}, title={paper_title[:60]}")

    # 第一轮：用 arxiv_id 搜索
    items = _do_search_query(f"{arxiv_id} in:name,description,readme")

    # 第二轮：用标题搜索（截断到合理长度）
    if not items and paper_title:
        clean_title = re.sub(r"[^\w\s\-]", "", paper_title)[:120].strip()
        if clean_title:
            items = _do_search_query(f"{clean_title} in:name,description,readme")

    if not items:
        logger.info("No GitHub repositories found")
        return []

    # 映射 + 计算置信度
    repos = [_map_repo_item(item, paper_title, arxiv_id) for item in items]

    # 按置信度降序排列
    repos.sort(key=lambda r: r["confidence"], reverse=True)

    # 最多 5 个
    result = repos[:5]
    logger.info(f"GitHub search complete: {len(result)} candidates returned")
    return result
