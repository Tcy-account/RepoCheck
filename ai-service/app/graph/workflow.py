"""
LangGraph 工作流定义

定义 7 个节点的执行顺序：
ParsePaper → FindRepo → SelectBestRepo → AnalyzeRepoStructure → AnalyzeDocs → ScoreRepo → GenerateReport
"""

from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes.parse_paper import parse_paper_node
from app.graph.nodes.find_repo import find_repo_node
from app.graph.nodes.select_best_repo import select_best_repo_node
from app.graph.nodes.analyze_repo_structure import analyze_repo_structure_node
from app.graph.nodes.analyze_docs import analyze_docs_node
from app.graph.nodes.score_repo import score_repo_node
from app.graph.nodes.generate_report import generate_report_node
from app.core.logger import logger


def should_continue(state: GraphState) -> str:
    """判断是否继续执行"""
    task_id = state.get("task_id", "unknown")
    if state.get("error"):
        logger.warning(f"[task={task_id}] Workflow stopped due to error: {state['error']}")
        return END
    return "continue"


def build_workflow() -> StateGraph:
    """
    构建 LangGraph 工作流
    """
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("parse_paper", parse_paper_node)
    workflow.add_node("find_repo", find_repo_node)
    workflow.add_node("select_best_repo", select_best_repo_node)
    workflow.add_node("analyze_repo_structure", analyze_repo_structure_node)
    workflow.add_node("analyze_docs", analyze_docs_node)
    workflow.add_node("score_repo", score_repo_node)
    workflow.add_node("generate_report", generate_report_node)

    # 设置入口
    workflow.set_entry_point("parse_paper")

    # 定义边 (使用 conditional_edges 可以在出错时提前结束)
    workflow.add_conditional_edges(
        "parse_paper",
        should_continue,
        {"continue": "find_repo", END: END},
    )
    workflow.add_conditional_edges(
        "find_repo",
        should_continue,
        {"continue": "select_best_repo", END: END},
    )
    workflow.add_conditional_edges(
        "select_best_repo",
        should_continue,
        {"continue": "analyze_repo_structure", END: END},
    )
    workflow.add_conditional_edges(
        "analyze_repo_structure",
        should_continue,
        {"continue": "analyze_docs", END: END},
    )
    workflow.add_conditional_edges(
        "analyze_docs",
        should_continue,
        {"continue": "score_repo", END: END},
    )
    workflow.add_conditional_edges(
        "score_repo",
        should_continue,
        {"continue": "generate_report", END: END},
    )
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# 全局工作流实例
app_workflow = build_workflow()
