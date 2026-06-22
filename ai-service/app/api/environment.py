"""
Environment Analysis API — 环境风险诊断

聚合以下工具：
  - dependency_file_tool      → 从 GitHub 读取依赖文件
  - requirements_parser       → 解析 requirements.txt
  - environment_yml_parser    → 解析 environment.yml (PyYAML)
  - pyproject_parser          → 解析 pyproject.toml (tomllib)
  - dockerfile_parser         → 解析 Dockerfile
  - environment_risk_tool     → 综合评分

不 clone、不 pip install、不下载数据/权重。
不接入主 workflow（POST /api/analyze）。
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.tools.dependency_file_tool import fetch_dependency_files
from app.tools.requirements_parser import parse_requirements
from app.tools.environment_yml_parser import parse_environment_yml
from app.tools.pyproject_parser import parse_pyproject
from app.tools.dockerfile_parser import parse_dockerfile
from app.tools.environment_risk_tool import assess_environment_risk, assess_dependency_risks
from app.core.logger import logger

router = APIRouter()


# ───────────────────── 请求/响应模型 ─────────────────────

class RepoInfo(BaseModel):
    platform: str
    repoUrl: str
    repoName: str
    owner: str
    defaultBranch: str


class AnalyzeEnvironmentRequest(BaseModel):
    taskId: int
    repoInfo: RepoInfo


class DependencyItem(BaseModel):
    fileType: str
    filePath: str
    packageName: str
    versionSpec: Optional[str] = None
    source: Optional[str] = None
    riskLevel: Optional[str] = None
    riskReason: Optional[str] = None


class EnvironmentInfo(BaseModel):
    pythonVersion: Optional[str] = None
    cudaVersion: Optional[str] = None
    mainFramework: Optional[str] = None
    frameworkVersion: Optional[str] = None
    requiresGpu: bool = False
    hasDocker: bool = False
    dockerBaseImage: Optional[str] = None
    dependencyRiskScore: int = 0
    cudaRiskScore: int = 0
    dockerReadinessScore: int = 0
    environmentScore: int = 0
    riskLevel: str = "LOW"
    riskSummary: Optional[str] = None
    installAdvice: Optional[str] = None


class AnalyzeEnvironmentResponse(BaseModel):
    taskId: int
    dependencies: List[DependencyItem] = []
    environmentAnalysis: EnvironmentInfo


# ───────────────────── API 入口 ─────────────────────

@router.post("/analyze", response_model=AnalyzeEnvironmentResponse)
async def analyze_environment(request: AnalyzeEnvironmentRequest):
    """
    环境风险分析

    流程：
    1. dependency_file_tool → 读取依赖文件
    2. 各解析器 → 解析依赖清单
    3. environment_risk_tool → 评分 + 汇总
    """
    task_id = request.taskId
    repo = request.repoInfo
    logger.info(f"[task={task_id}] environment/analyze: start, repo={repo.owner}/{repo.repoName}")

    if not repo.owner or not repo.repoName:
        raise RuntimeError("仓库信息不完整：缺少 owner 或 repoName")

    # ═══════════════════════════════════════════════════════
    # 1. 读取依赖文件
    # ═══════════════════════════════════════════════════════
    logger.info(f"[task={task_id}] environment/analyze: fetching dependency files")
    dep_files = fetch_dependency_files(repo.owner, repo.repoName, repo.defaultBranch)
    logger.info(f"[task={task_id}] environment/analyze: got {len(dep_files)} dependency files")

    # ═══════════════════════════════════════════════════════
    # 2. 解析各文件
    # ═══════════════════════════════════════════════════════
    all_deps: list = []
    metadata: dict = {
        "pythonVersion": None,
        "cudaVersion": None,
        "dockerBaseImage": None,
        "hasDocker": False,
        "channels": [],
        "hasNvidiaChannel": False,
        "hasPytorchChannel": False,
    }

    for df in dep_files:
        ftype = df["fileType"]
        fpath = df["filePath"]
        content = df["content"]

        logger.info(f"[task={task_id}] environment/analyze: parsing {fpath} (type={ftype})")

        if ftype == "requirements":
            deps = parse_requirements(content, fpath)
            for d in deps:
                d["fileType"] = ftype
            all_deps.extend(deps)
            logger.info(f"[task={task_id}] environment/analyze: {fpath} → {len(deps)} packages")

        elif ftype == "environment_yml":
            deps, yml_meta = parse_environment_yml(content, fpath)
            for d in deps:
                d["fileType"] = ftype
            all_deps.extend(deps)
            # 合并元数据（优先保留第一个解析到的版本信息）
            if yml_meta.get("pythonVersion") and not metadata["pythonVersion"]:
                metadata["pythonVersion"] = yml_meta["pythonVersion"]
            if yml_meta.get("cudaVersion") and not metadata["cudaVersion"]:
                metadata["cudaVersion"] = yml_meta["cudaVersion"]
            if yml_meta.get("channels"):
                metadata["channels"].extend(yml_meta["channels"])
            if yml_meta.get("hasNvidiaChannel"):
                metadata["hasNvidiaChannel"] = True
            if yml_meta.get("hasPytorchChannel"):
                metadata["hasPytorchChannel"] = True
            logger.info(f"[task={task_id}] environment/analyze: {fpath} → {len(deps)} packages, "
                        f"meta={yml_meta}")

        elif ftype == "pyproject":
            deps, py_meta = parse_pyproject(content, fpath)
            for d in deps:
                d["fileType"] = ftype
            all_deps.extend(deps)
            if py_meta.get("pythonVersion") and not metadata["pythonVersion"]:
                metadata["pythonVersion"] = py_meta["pythonVersion"]
            logger.info(f"[task={task_id}] environment/analyze: {fpath} → {len(deps)} packages, "
                        f"python={py_meta.get('pythonVersion')}")

        elif ftype == "dockerfile":
            deps, docker_meta = parse_dockerfile(content, fpath)
            for d in deps:
                d["fileType"] = ftype
            all_deps.extend(deps)
            # Docker 元数据
            metadata["hasDocker"] = True
            if docker_meta.get("cudaVersion") and not metadata["cudaVersion"]:
                metadata["cudaVersion"] = docker_meta["cudaVersion"]
            if docker_meta.get("pythonVersion") and not metadata["pythonVersion"]:
                metadata["pythonVersion"] = docker_meta["pythonVersion"]
            if docker_meta.get("dockerBaseImage") and not metadata["dockerBaseImage"]:
                metadata["dockerBaseImage"] = docker_meta["dockerBaseImage"]
            if docker_meta.get("channels"):
                metadata["channels"].extend(docker_meta["channels"])
            if docker_meta.get("hasNvidiaChannel"):
                metadata["hasNvidiaChannel"] = True
            if docker_meta.get("hasPytorchChannel"):
                metadata["hasPytorchChannel"] = True
            logger.info(f"[task={task_id}] environment/analyze: {fpath} → {len(deps)} deps, "
                        f"docker_meta={docker_meta}")

    # ═══════════════════════════════════════════════════════
    # 3. 风险评估
    # ═══════════════════════════════════════════════════════
    logger.info(f"[task={task_id}] environment/analyze: assessing risks for {len(all_deps)} dependencies")

    # 为每个依赖评估风险
    assess_dependency_risks(all_deps)

    # 综合评分
    env_analysis = assess_environment_risk(all_deps, metadata)

    logger.info(f"[task={task_id}] environment/analyze: done, risk={env_analysis['riskLevel']}, "
                f"score={env_analysis['environmentScore']}, deps={len(all_deps)}")

    # 过滤掉元标记行（_meta:
    visible_deps = [d for d in all_deps if not d.get("packageName", "").startswith("_meta:")]

    return AnalyzeEnvironmentResponse(
        taskId=task_id,
        dependencies=[DependencyItem(**d) for d in visible_deps],
        environmentAnalysis=EnvironmentInfo(**env_analysis),
    )
