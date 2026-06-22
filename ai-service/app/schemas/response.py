from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class PaperInfoOut(BaseModel):
    arxivId: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    abstractText: Optional[str] = None
    publishedAt: Optional[date] = None
    paperUrl: Optional[str] = None


class RepoInfoOut(BaseModel):
    platform: Optional[str] = None
    repoUrl: Optional[str] = None
    repoName: Optional[str] = None
    owner: Optional[str] = None
    stars: Optional[int] = 0
    forks: Optional[int] = 0
    defaultBranch: Optional[str] = None
    lastUpdatedAt: Optional[datetime] = None
    confidence: Optional[float] = 0.0
    confidenceReason: Optional[str] = None


class RepoAnalysisOut(BaseModel):
    hasReadme: bool = False
    hasRequirements: bool = False
    hasEnvironmentYml: bool = False
    hasDockerfile: bool = False
    hasLicense: bool = False
    hasTrainCode: bool = False
    hasInferenceCode: bool = False
    hasDatasetDoc: bool = False
    hasWeightDoc: bool = False
    readmeQualityScore: int = 0
    dependencyComplexityScore: int = 0
    structureCompletenessScore: int = 0
    fileMatches: Optional[dict] = None
    readmeAnalysis: Optional[dict] = None


class ReportOut(BaseModel):
    reproducibilityScore: int = 0
    completenessScore: int = 0
    environmentScore: int = 0
    riskLevel: Optional[str] = None
    summary: Optional[str] = None
    methodSummary: Optional[str] = None
    innovationSummary: Optional[str] = None
    reproduceSteps: Optional[str] = None
    riskTips: Optional[str] = None
    finalAdvice: Optional[str] = None


class AnalyzeResponse(BaseModel):
    taskId: int
    paperInfo: Optional[PaperInfoOut] = None
    repoInfo: Optional[RepoInfoOut] = None
    repoAnalysis: Optional[RepoAnalysisOut] = None
    report: Optional[ReportOut] = None
