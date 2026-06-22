"""
仓库分析 API — 用于手动指定仓库后重新分析

POST /api/repo/analyze-structure  → 基于指定仓库运行完整分析（跳过论文解析和仓库搜索）
POST /api/report/generate        → 基于已有数据仅生成报告（跳过所有分析）
"""

from fastapi import APIRouter
from app.schemas.request import AnalyzeStructureRequest, GenerateReportRequest
from app.schemas.response import AnalyzeResponse, PaperInfoOut, RepoInfoOut, RepoAnalysisOut, ReportOut
from app.graph.nodes.analyze_repo_structure import analyze_repo_structure_node
from app.graph.nodes.analyze_docs import analyze_docs_node
from app.graph.nodes.score_repo import score_repo_node
from app.graph.nodes.generate_report import generate_report_node
from app.core.logger import logger

router = APIRouter()


@router.post("/repo/analyze-structure", response_model=AnalyzeResponse)
async def analyze_structure(request: AnalyzeStructureRequest):
    """
    基于手动指定的仓库运行分析流程（跳过论文解析和仓库搜索）。

    执行流程：analyze_repo_structure → analyze_docs → score_repo → generate_report
    """
    logger.info(f"analyze-structure: taskId={request.taskId}, repo={request.repoInfo.get('repoName')}")

    repo_info = request.repoInfo or {}
    paper_info = request.paperInfo or {}

    # 构建 state，直接传入仓库信息（已由调用方确认）
    state = {
        "task_id": request.taskId,
        "arxiv_id": paper_info.get("arxivId", ""),
        "title": paper_info.get("title", ""),
        "abstract_text": paper_info.get("abstractText", ""),
        "selected_repo": {
            "platform": repo_info.get("platform", "GitHub"),
            "repoUrl": repo_info.get("repoUrl", ""),
            "repoName": repo_info.get("repoName", ""),
            "owner": repo_info.get("owner", ""),
            "stars": repo_info.get("stars", 0),
            "forks": repo_info.get("forks", 0),
            "defaultBranch": repo_info.get("defaultBranch", "main"),
            "lastUpdatedAt": repo_info.get("lastUpdatedAt"),
            "confidence": repo_info.get("confidence", 1.0),
            "confidenceReason": repo_info.get("confidenceReason", "用户手动指定仓库"),
        },
    }

    # 节点 1: 分析仓库结构
    state = analyze_repo_structure_node(state)

    # 节点 2: 分析文档（README）
    state = analyze_docs_node(state)

    # 节点 3: 评分
    state = score_repo_node(state)

    # 节点 4: 生成报告
    state = generate_report_node(state)

    logger.info(f"analyze-structure complete for taskId={request.taskId}")

    # 检查工作流是否出错
    if state.get("error"):
        logger.error(f"analyze-structure workflow error for taskId={request.taskId}: {state['error']}")
        raise RuntimeError(f"仓库结构分析失败：{state['error']}")

    repo = state.get("selected_repo") or {}
    file_presence = state.get("file_presence") or {}

    return AnalyzeResponse(
        taskId=request.taskId,
        paperInfo=PaperInfoOut(
            arxivId=state.get("arxiv_id"),
            title=state.get("title"),
            authors=state.get("authors"),
            abstractText=state.get("abstract_text"),
            publishedAt=state.get("published_at"),
            paperUrl=paper_info.get("paperUrl"),
        ),
        repoInfo=RepoInfoOut(
            platform=repo.get("platform"),
            repoUrl=repo.get("repoUrl"),
            repoName=repo.get("repoName"),
            owner=repo.get("owner"),
            stars=repo.get("stars", 0),
            forks=repo.get("forks", 0),
            defaultBranch=repo.get("defaultBranch"),
            lastUpdatedAt=repo.get("lastUpdatedAt"),
            confidence=repo.get("confidence", 1.0),
            confidenceReason=repo.get("confidenceReason", "用户手动指定仓库"),
        ),
        repoAnalysis=RepoAnalysisOut(
            hasReadme=file_presence.get("hasReadme", False),
            hasRequirements=file_presence.get("hasRequirements", False),
            hasEnvironmentYml=file_presence.get("hasEnvironmentYml", False),
            hasDockerfile=file_presence.get("hasDockerfile", False),
            hasLicense=file_presence.get("hasLicense", False),
            hasTrainCode=file_presence.get("hasTrainCode", False),
            hasInferenceCode=file_presence.get("hasInferenceCode", False),
            hasDatasetDoc=file_presence.get("hasDatasetDoc", False),
            hasWeightDoc=file_presence.get("hasWeightDoc", False),
            readmeQualityScore=state.get("readme_quality_score", 0),
            dependencyComplexityScore=state.get("dependency_complexity_score", 0),
            structureCompletenessScore=state.get("structure_completeness_score", 0),
            fileMatches=state.get("file_matches"),
        ),
        report=ReportOut(
            reproducibilityScore=state.get("reproducibility_score", 0),
            completenessScore=state.get("completeness_score", 0),
            environmentScore=state.get("environment_score", 0),
            riskLevel=state.get("risk_level"),
            summary=state.get("summary"),
            methodSummary=state.get("method_summary"),
            innovationSummary=state.get("innovation_summary"),
            reproduceSteps=state.get("reproduce_steps"),
            riskTips=state.get("risk_tips"),
            finalAdvice=state.get("final_advice"),
        ),
    )


@router.post("/report/generate", response_model=AnalyzeResponse)
async def generate_report_only(request: GenerateReportRequest):
    """
    基于已有数据仅生成报告（跳过所有分析步骤）。

    不重新搜索仓库、不重新解析论文，只调用 generate_report_node。
    """
    logger.info(f"report/generate: taskId={request.taskId}")

    repo_info = request.repoInfo or {}
    paper_info = request.paperInfo or {}
    repo_analysis = request.repoAnalysis or {}
    score_details = request.scoreDetails or {}

    # 构建 state，包含已有数据
    state = {
        "task_id": request.taskId,
        "arxiv_id": paper_info.get("arxivId", ""),
        "title": paper_info.get("title", ""),
        "abstract_text": paper_info.get("abstractText", ""),
        "authors": paper_info.get("authors", ""),
        "published_at": paper_info.get("publishedAt"),
        "selected_repo": {
            "platform": repo_info.get("platform"),
            "repoUrl": repo_info.get("repoUrl"),
            "repoName": repo_info.get("repoName"),
            "owner": repo_info.get("owner"),
            "stars": repo_info.get("stars", 0),
            "forks": repo_info.get("forks", 0),
            "defaultBranch": repo_info.get("defaultBranch"),
            "lastUpdatedAt": repo_info.get("lastUpdatedAt"),
            "confidence": repo_info.get("confidence", 1.0),
            "confidenceReason": repo_info.get("confidenceReason"),
        },
        "file_presence": {
            "hasReadme": repo_analysis.get("hasReadme", False),
            "hasRequirements": repo_analysis.get("hasRequirements", False),
            "hasEnvironmentYml": repo_analysis.get("hasEnvironmentYml", False),
            "hasDockerfile": repo_analysis.get("hasDockerfile", False),
            "hasLicense": repo_analysis.get("hasLicense", False),
            "hasTrainCode": repo_analysis.get("hasTrainCode", False),
            "hasInferenceCode": repo_analysis.get("hasInferenceCode", False),
            "hasDatasetDoc": repo_analysis.get("hasDatasetDoc", False),
            "hasWeightDoc": repo_analysis.get("hasWeightDoc", False),
        },
        "readme_quality_score": repo_analysis.get("readmeQualityScore", 0),
        "dependency_complexity_score": repo_analysis.get("dependencyComplexityScore", 0),
        "structure_completeness_score": repo_analysis.get("structureCompletenessScore", 0),
        "reproducibility_score": score_details.get("reproducibilityScore", 0),
        "completeness_score": score_details.get("completenessScore", 0),
        "environment_score": score_details.get("environmentScore", 0),
        "risk_level": score_details.get("riskLevel", "HIGH"),
        "score_details": score_details,
    }

    # 只执行报告生成节点
    state = generate_report_node(state)

    logger.info(f"report/generate complete for taskId={request.taskId}")

    return AnalyzeResponse(
        taskId=request.taskId,
        paperInfo=PaperInfoOut(
            arxivId=state.get("arxiv_id"),
            title=state.get("title"),
            authors=state.get("authors"),
            abstractText=state.get("abstract_text"),
            publishedAt=state.get("published_at"),
            paperUrl=paper_info.get("paperUrl"),
        ),
        repoInfo=RepoInfoOut(
            platform=repo_info.get("platform"),
            repoUrl=repo_info.get("repoUrl"),
            repoName=repo_info.get("repoName"),
            owner=repo_info.get("owner"),
            stars=repo_info.get("stars", 0),
            forks=repo_info.get("forks", 0),
            defaultBranch=repo_info.get("defaultBranch"),
            lastUpdatedAt=repo_info.get("lastUpdatedAt"),
            confidence=repo_info.get("confidence", 1.0),
            confidenceReason=repo_info.get("confidenceReason"),
        ),
        repoAnalysis=RepoAnalysisOut(
            hasReadme=repo_analysis.get("hasReadme", False),
            hasRequirements=repo_analysis.get("hasRequirements", False),
            hasEnvironmentYml=repo_analysis.get("hasEnvironmentYml", False),
            hasDockerfile=repo_analysis.get("hasDockerfile", False),
            hasLicense=repo_analysis.get("hasLicense", False),
            hasTrainCode=repo_analysis.get("hasTrainCode", False),
            hasInferenceCode=repo_analysis.get("hasInferenceCode", False),
            hasDatasetDoc=repo_analysis.get("hasDatasetDoc", False),
            hasWeightDoc=repo_analysis.get("hasWeightDoc", False),
            readmeQualityScore=repo_analysis.get("readmeQualityScore", 0),
            dependencyComplexityScore=repo_analysis.get("dependencyComplexityScore", 0),
            structureCompletenessScore=repo_analysis.get("structureCompletenessScore", 0),
        ),
        report=ReportOut(
            reproducibilityScore=state.get("reproducibility_score", 0),
            completenessScore=state.get("completeness_score", 0),
            environmentScore=state.get("environment_score", 0),
            riskLevel=state.get("risk_level"),
            summary=state.get("summary"),
            methodSummary=state.get("method_summary"),
            innovationSummary=state.get("innovation_summary"),
            reproduceSteps=state.get("reproduce_steps"),
            riskTips=state.get("risk_tips"),
            finalAdvice=state.get("final_advice"),
        ),
    )
