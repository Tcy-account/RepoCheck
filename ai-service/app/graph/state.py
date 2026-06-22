"""
LangGraph 状态定义
"""

from typing import TypedDict, List, Optional, Any


class GraphState(TypedDict, total=False):
    """工作流状态"""
    # 输入
    task_id: int
    paper_url: str

    # 错误
    error: Optional[str]

    # 论文信息 (ParsePaperNode 输出)
    arxiv_id: str
    title: str
    authors: str
    abstract_text: str
    published_at: str

    # 仓库搜索 (FindRepoNode 输出)
    candidate_repos: List[dict]

    # 最佳仓库 (SelectBestRepoNode 输出)
    selected_repo: Optional[dict]

    # 仓库结构分析
    repo_structure: dict
    file_presence: dict
    file_matches: dict

    # 文档分析
    readme: dict
    readme_analysis: dict
    readme_quality_score: int
    dependency_complexity_score: int
    structure_completeness_score: int

    # 评分
    reproducibility_score: int
    completeness_score: int
    environment_score: int
    risk_level: str
    score_details: dict

    # 报告
    summary: str
    method_summary: str
    innovation_summary: str
    reproduce_steps: str
    risk_tips: str
    final_advice: str
