"""
FindRepoNode — 搜索代码仓库
"""

from app.graph.state import GraphState
from app.tools.github_tool import search_github_repos
from app.tools.gitlab_tool import search_gitlab_repos
from app.core.logger import logger


def find_repo_node(state: GraphState) -> GraphState:
    """
    根据论文信息搜索对应的代码仓库。

    GitHub 搜索失败不会导致整个 workflow 失败，
    而是返回空 candidates，后续生成高风险报告。
    """
    title = state.get("title", "")
    arxiv_id = state.get("arxiv_id", "")
    abstract = state.get("abstract_text", "")
    task_id = state.get("task_id", "unknown")

    logger.info(f"[task={task_id}] find_repo_node: start, searching for title='{title}'")

    candidate_repos = []

    try:
        github_repos = search_github_repos(title, arxiv_id, abstract)
        candidate_repos.extend(github_repos)
    except Exception as e:
        logger.warning(f"[task={task_id}] find_repo_node: GitHub search failed: {e}")

    try:
        gitlab_repos = search_gitlab_repos(title, arxiv_id)
        candidate_repos.extend(gitlab_repos)
    except Exception as e:
        logger.warning(f"[task={task_id}] find_repo_node: GitLab search failed: {e}")

    state["candidate_repos"] = candidate_repos
    logger.info(f"[task={task_id}] find_repo_node: done, found {len(candidate_repos)} candidates")
    return state
