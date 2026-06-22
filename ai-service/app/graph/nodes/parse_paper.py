"""
ParsePaperNode — 解析 arXiv 论文信息
"""

from app.graph.state import GraphState
from app.tools.arxiv_tool import fetch_paper_info
from app.core.logger import logger


def parse_paper_node(state: GraphState) -> GraphState:
    """
    解析 arXiv 论文链接，提取论文元信息
    """
    task_id = state.get("task_id", "unknown")
    paper_url = state.get("paper_url", "")
    logger.info(f"[task={task_id}] parse_paper_node: start, url={paper_url}")

    try:
        paper_info = fetch_paper_info(paper_url)

        state["arxiv_id"] = paper_info["arxivId"]
        state["title"] = paper_info["title"]
        state["authors"] = paper_info["authors"]
        state["abstract_text"] = paper_info["abstractText"]
        state["published_at"] = paper_info["publishedAt"]

        logger.info(f"[task={task_id}] parse_paper_node: done, title={paper_info['title']}")
    except Exception as e:
        logger.error(f"[task={task_id}] parse_paper_node failed: {e}")
        state["error"] = "论文解析失败：" + str(e)

    return state
