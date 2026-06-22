"""
SelectBestRepoNode — 从候选仓库中选择最佳匹配
"""

from app.graph.state import GraphState
from app.core.logger import logger


def select_best_repo_node(state: GraphState) -> GraphState:
    """
    从候选仓库中选择最可能的官方仓库
    """
    candidates = state.get("candidate_repos", [])
    task_id = state.get("task_id", "unknown")

    logger.info(f"[task={task_id}] select_best_repo_node: start, {len(candidates)} candidates")

    try:
        if not candidates:
            logger.warning(f"[task={task_id}] select_best_repo_node: no candidates found")
            state["selected_repo"] = None
            return state

        # V1: 简单策略 — 选置信度最高的（已在 github_tool 中计算）
        best = max(candidates, key=lambda r: r.get("confidence", 0))

        state["selected_repo"] = {
            "platform": best.get("platform", "GitHub"),
            "repoUrl": best.get("repoUrl", ""),
            "repoName": best.get("repoName", ""),
            "owner": best.get("owner", ""),
            "stars": best.get("stars", 0),
            "forks": best.get("forks", 0),
            "defaultBranch": best.get("defaultBranch", "main"),
            "lastUpdatedAt": best.get("lastUpdatedAt", ""),
            "confidence": best.get("confidence", 0.5),
            "confidenceReason": best.get("confidenceReason", f"Selected from {len(candidates)} candidates"),
        }

        logger.info(f"[task={task_id}] select_best_repo_node: done, "
                     f"selected={best.get('repoName')}, confidence={best.get('confidence')}")
    except Exception as e:
        logger.error(f"[task={task_id}] select_best_repo_node failed: {e}")
        state["error"] = "仓库选择失败：" + str(e)

    return state
