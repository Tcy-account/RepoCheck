"""
ScoreRepoNode — 复现可行性综合评分

基于真实仓库文件结构、README 分析结果，生成可信的复现可行性评分。
"""

from typing import List, Tuple
from app.graph.state import GraphState
from app.core.logger import logger


def clamp_score(value: float) -> int:
    """将分数限制在 0-100 内，四舍五入为整数"""
    return max(0, min(100, round(value)))


# ═══════════════════════════════════════════════════════════
# 完整度评分
# ═══════════════════════════════════════════════════════════

_COMPLETENESS_RULES = [
    ("hasReadme", 15, "README 文件存在"),
    ("hasRequirements", 15, "检测到依赖文件"),
    ("hasEnvironmentYml", 10, "检测到 environment/conda 配置文件"),
    ("hasDockerfile", 10, "检测到 Dockerfile"),
    ("hasLicense", 5, "检测到 LICENSE 文件"),
    ("hasTrainCode", 15, "检测到训练入口代码"),
    ("hasInferenceCode", 15, "检测到推理/演示入口代码"),
    ("hasDatasetDoc", 10, "检测到数据集说明"),
    ("hasWeightDoc", 5, "检测到模型权重说明"),
]


def calculate_completeness_score(
    file_presence: dict,
    readme_analysis: dict,
) -> Tuple[int, List[str], List[str]]:
    """
    计算仓库完整度评分 (0-100)。

    dataset/weight 可从 README 分析中补充。
    """
    positives: List[str] = []
    negatives: List[str] = []

    # 用 README 分析补充 dataset 和 weight 检测
    merged = dict(file_presence) if file_presence else {}
    if readme_analysis:
        if readme_analysis.get("hasDatasetSection"):
            merged["hasDatasetDoc"] = True
        if readme_analysis.get("hasWeightSection"):
            merged["hasWeightDoc"] = True

    score = 0
    for key, points, reason in _COMPLETENESS_RULES:
        if merged.get(key):
            score += points
            positives.append(reason)
        elif key in ("hasDatasetDoc", "hasWeightDoc"):
            negatives.append(f"缺少{reason.replace('检测到', '')}")
        else:
            negatives.append(f"未{reason}")

    return clamp_score(score), positives, negatives


# ═══════════════════════════════════════════════════════════
# 环境友好度评分
# ═══════════════════════════════════════════════════════════


def calculate_environment_score(
    file_presence: dict,
    readme_analysis: dict,
    repo_structure: dict,
) -> Tuple[int, List[str], List[str]]:
    """
    计算环境友好度评分 (0-100)。

    越高说明越容易配置环境。
    """
    positives: List[str] = []
    negatives: List[str] = []
    fp = file_presence or {}
    ra = readme_analysis or {}
    rs = repo_structure or {}

    score = 50  # 基础分

    # ── 加分项 ──
    if fp.get("hasRequirements"):
        score += 15
        positives.append("有依赖声明文件，便于安装")
    if fp.get("hasEnvironmentYml"):
        score += 15
        positives.append("有 conda 环境文件，环境配置明确")
    if fp.get("hasDockerfile"):
        score += 20
        positives.append("有 Dockerfile，可容器化部署")
    if ra.get("hasInstallSection"):
        score += 10
        positives.append("README 包含安装说明")
    if ra.get("hasExampleCommands"):
        score += 5
        positives.append("README 包含示例命令")

    # ── 扣分项 ──
    has_any_dep = fp.get("hasRequirements") or fp.get("hasEnvironmentYml") or fp.get("hasDockerfile")
    if not has_any_dep:
        score -= 25
        negatives.append("没有任何依赖文件或 Dockerfile，环境配置困难")

    if not ra.get("hasInstallSection"):
        score -= 15
        negatives.append("README 缺少安装说明")

    total_count = rs.get("total_count", 0)
    if rs.get("truncated"):
        score -= 5
        negatives.append("仓库文件树过大被截断")
    if total_count > 5000:
        score -= 20
        negatives.append(f"仓库文件数量庞大 ({total_count})，结构复杂")
    elif total_count > 2000:
        score -= 10
        negatives.append(f"仓库文件数量较多 ({total_count})")

    return clamp_score(score), positives, negatives


# ═══════════════════════════════════════════════════════════
# 复现可行性评分
# ═══════════════════════════════════════════════════════════


def calculate_reproducibility_score(
    completeness_score: int,
    environment_score: int,
    readme_quality_score: int,
    selected_repo: dict,
    file_presence: dict,
    repo_structure: dict,
) -> Tuple[int, List[str], List[str]]:
    """
    计算复现可行性评分 (0-100)。

    综合加权 + 关键风险扣分。
    """
    positives: List[str] = []
    negatives: List[str] = []
    fp = file_presence or {}

    # 加权计算
    confidence = (selected_repo or {}).get("confidence", 0.0)
    weighted = (
        0.45 * completeness_score
        + 0.25 * environment_score
        + 0.20 * readme_quality_score
        + 0.10 * confidence * 100
    )

    # ── 关键风险扣分 ──
    score = weighted
    has_train_or_infer = fp.get("hasTrainCode") or fp.get("hasInferenceCode")

    if not has_train_or_infer:
        score -= 20
        negatives.append("缺少训练代码和推理代码，无法直接复现")
    if not fp.get("hasDatasetDoc"):
        score -= 10
        negatives.append("缺少数据集说明，复现时可能需要自行寻找数据")
    if not fp.get("hasWeightDoc"):
        score -= 5
        negatives.append("缺少模型权重说明，复现时可能需要自行寻找预训练权重")
    if not fp.get("hasReadme"):
        score -= 20
        negatives.append("无 README 文档，缺乏基本指引")
    if (repo_structure or {}).get("error"):
        score -= 15
        negatives.append("仓库文件树获取失败，评分可信度下降")

    # 正向因素
    if has_train_or_infer:
        positives.append("仓库包含可执行代码（训练/推理）")
    if fp.get("hasDatasetDoc"):
        positives.append("仓库包含数据集说明")
    if fp.get("hasWeightDoc"):
        positives.append("仓库包含模型权重说明")
    if fp.get("hasReadme"):
        positives.append("README 文档提供基本指引")

    return clamp_score(score), positives, negatives


# ═══════════════════════════════════════════════════════════
# 风险等级
# ═══════════════════════════════════════════════════════════


def calculate_risk_level(
    reproducibility_score: int,
    file_presence: dict,
    readme_quality_score: int,
    repo_structure: dict,
) -> Tuple[str, List[str]]:
    """
    根据复现可行性分和关键缺失项判定风险等级。
    """
    fp = file_presence or {}
    risk_factors: List[str] = []

    has_readme = fp.get("hasReadme", False)
    has_deps_or_docker = fp.get("hasRequirements") or fp.get("hasDockerfile")
    has_train_or_infer = fp.get("hasTrainCode") or fp.get("hasInferenceCode")
    has_error = bool((repo_structure or {}).get("error"))

    # ── HIGH ──
    if (
        reproducibility_score < 50
        or not has_readme
        or (not has_deps_or_docker and not has_readme)
        or not has_train_or_infer
        or has_error
    ):
        if reproducibility_score < 50:
            risk_factors.append("复现可行性评分过低")
        if not has_readme:
            risk_factors.append("缺少 README 文档")
        if not has_deps_or_docker:
            risk_factors.append("缺少依赖文件或 Dockerfile")
        if not has_train_or_infer:
            risk_factors.append("缺少训练代码和推理代码")
        if has_error:
            risk_factors.append("仓库文件树获取失败")
        return "HIGH", risk_factors

    # ── MEDIUM ──
    if (
        reproducibility_score < 75
        or not fp.get("hasDatasetDoc")
        or not fp.get("hasWeightDoc")
        or readme_quality_score < 60
    ):
        if reproducibility_score < 75:
            risk_factors.append("复现可行性评分中等")
        if not fp.get("hasDatasetDoc"):
            risk_factors.append("缺少数据集说明")
        if not fp.get("hasWeightDoc"):
            risk_factors.append("缺少模型权重说明")
        if readme_quality_score < 60:
            risk_factors.append("README 文档质量较低")
        return "MEDIUM", risk_factors

    # ── LOW ──
    return "LOW", risk_factors


# ═══════════════════════════════════════════════════════════
# 节点入口
# ═══════════════════════════════════════════════════════════


def score_repo_node(state: GraphState) -> GraphState:
    """
    根据文件分析和文档分析生成综合评分。
    """
    task_id = state.get("task_id", "unknown")
    logger.info(f"[task={task_id}] score_repo_node: start")

    try:
        selected_repo = state.get("selected_repo")
        if selected_repo is None:
            logger.warning(f"[task={task_id}] No selected repo, scores default to 0")
            state["completeness_score"] = 0
            state["environment_score"] = 0
            state["reproducibility_score"] = 0
            state["risk_level"] = "HIGH"
            state["structure_completeness_score"] = 0
            state["dependency_complexity_score"] = 0
            state["score_details"] = {
                "positiveFactors": [],
                "negativeFactors": ["未找到代码仓库"],
                "riskFactors": ["未找到代码仓库，无法评估复现可行性"],
                "completenessFactors": [],
                "environmentFactors": [],
            }
            return state

        file_presence = state.get("file_presence", {})
        readme_analysis = state.get("readme_analysis", {})
        readme_quality_score = state.get("readme_quality_score", 0)
        repo_structure = state.get("repo_structure", {})

        # ── 各项评分 ──
        cs, comp_pos, comp_neg = calculate_completeness_score(file_presence, readme_analysis)
        es, env_pos, env_neg = calculate_environment_score(file_presence, readme_analysis, repo_structure)
        rs, rp_pos, rp_neg = calculate_reproducibility_score(
            cs, es, readme_quality_score, selected_repo, file_presence, repo_structure,
        )
        risk_level, risk_factors = calculate_risk_level(rs, file_presence, readme_quality_score, repo_structure)

        # ── 依赖复杂度 (保留给 API 用) ──
        dep_score = 60
        if file_presence.get("hasDockerfile"):
            dep_score += 20
        if file_presence.get("hasRequirements"):
            dep_score += 10
        if file_presence.get("hasEnvironmentYml"):
            dep_score += 10
        dependency_complexity_score = clamp_score(dep_score)

        # ── 写入 state ──
        state["completeness_score"] = cs
        state["environment_score"] = es
        state["reproducibility_score"] = rs
        state["risk_level"] = risk_level
        state["structure_completeness_score"] = cs
        state["dependency_complexity_score"] = dependency_complexity_score
        state["score_details"] = {
            "positiveFactors": comp_pos + env_pos + rp_pos,
            "negativeFactors": comp_neg + env_neg + rp_neg,
            "riskFactors": risk_factors,
            "completenessFactors": comp_pos,
            "environmentFactors": env_pos,
        }

        logger.info(
            f"[task={task_id}] score_repo_node: reproducibility={rs}, "
            f"completeness={cs}, environment={es}, risk={risk_level}"
        )
    except Exception as e:
        logger.error(f"[task={task_id}] score_repo_node failed: {e}")
        state["error"] = str(e)

    return state
