"""
分析 API
"""

from fastapi import APIRouter
from app.schemas.request import AnalyzeRequest
from app.schemas.response import AnalyzeResponse, PaperInfoOut, RepoInfoOut, RepoAnalysisOut, ReportOut
from app.graph.workflow import app_workflow
from app.core.logger import logger

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    执行论文分析流程
    """
    logger.info(f"Received analyze request for taskId={request.taskId}")

    # 构建初始状态
    initial_state = {
        "task_id": request.taskId,
        "paper_url": request.paperUrl,
    }

    # 执行 LangGraph 工作流
    result = app_workflow.invoke(initial_state)

    logger.info(f"Analysis complete for taskId={request.taskId}")

    # 检查工作流是否出错
    if result.get("error"):
        err = result["error"]
        logger.error(f"Workflow error for taskId={request.taskId}: {err}")
        # 根据错误类型给出更具体的信息
        if "论文解析失败" in str(err) or "arxiv" in str(err).lower():
            raise RuntimeError(f"论文解析失败：未找到对应 arXiv 论文，请确认链接格式正确 ({err})")
        raise RuntimeError(f"分析流程失败：{err}")

    # 构建响应
    repo = result.get("selected_repo") or {}
    file_presence = result.get("file_presence") or {}

    return AnalyzeResponse(
        taskId=request.taskId,
        paperInfo=PaperInfoOut(
            arxivId=result.get("arxiv_id"),
            title=result.get("title"),
            authors=result.get("authors"),
            abstractText=result.get("abstract_text"),
            publishedAt=result.get("published_at"),
            paperUrl=request.paperUrl,
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
            confidence=repo.get("confidence", 0.0),
            confidenceReason=repo.get("confidenceReason"),
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
            readmeQualityScore=result.get("readme_quality_score", 0),
            dependencyComplexityScore=result.get("dependency_complexity_score", 0),
            structureCompletenessScore=result.get("structure_completeness_score", 0),
            fileMatches=result.get("file_matches"),
            readmeAnalysis=result.get("readme_analysis"),
        ),
        report=ReportOut(
            reproducibilityScore=result.get("reproducibility_score", 0),
            completenessScore=result.get("completeness_score", 0),
            environmentScore=result.get("environment_score", 0),
            riskLevel=result.get("risk_level"),
            summary=result.get("summary"),
            methodSummary=result.get("method_summary"),
            innovationSummary=result.get("innovation_summary"),
            reproduceSteps=result.get("reproduce_steps"),
            riskTips=result.get("risk_tips"),
            finalAdvice=result.get("final_advice"),
        ),
    )
