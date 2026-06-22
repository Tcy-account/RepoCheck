from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    """分析请求"""
    taskId: int
    paperUrl: str


class AnalyzeStructureRequest(BaseModel):
    """基于指定仓库分析结构"""
    taskId: int
    repoInfo: dict
    paperInfo: Optional[dict] = None


class GenerateReportRequest(BaseModel):
    """基于已有数据生成报告"""
    taskId: int
    paperInfo: Optional[dict] = None
    repoInfo: Optional[dict] = None
    repoAnalysis: Optional[dict] = None
    scoreDetails: Optional[dict] = None
