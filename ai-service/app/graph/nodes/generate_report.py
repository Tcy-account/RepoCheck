"""
GenerateReportNode — 基于规则生成结构化中文报告

不依赖 LLM，根据 state 中的论文信息、仓库分析结果和评分细节，
生成稳定、保守的中文报告。
"""

from app.graph.state import GraphState
from app.core.logger import logger


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def _build_summary(
    has_repo: bool,
    repo_name: str,
    completeness_score: int,
    environment_score: int,
    reproducibility_score: int,
    risk_level: str,
    file_presence: dict,
    readme_quality_score: int,
) -> str:
    """生成综合摘要"""

    if not has_repo:
        return (
            "系统未能找到可信代码仓库，因此当前不建议直接投入复现。"
            "建议用户手动提供官方仓库链接后重新分析。"
        )

    fp = file_presence or {}

    # 仓库概况
    parts = [f"系统已找到疑似代码仓库 {repo_name}。"]

    # 评分概况
    parts.append(
        f"仓库完整度评分为 {completeness_score}，"
        f"环境友好度评分为 {environment_score}，"
        f"综合复现可行性评分为 {reproducibility_score}，"
        f"风险等级为 {risk_level}。"
    )

    # 补充细节
    has_readme = fp.get("hasReadme", False)
    has_deps = fp.get("hasRequirements") or fp.get("hasEnvironmentYml") or fp.get("hasDockerfile")
    has_data = fp.get("hasDatasetDoc", False)
    has_weight = fp.get("hasWeightDoc", False)

    if has_readme:
        parts.append(f"该仓库具备 README 文档（质量评分 {readme_quality_score} 分）。")
    else:
        parts.append("该仓库缺少 README 文档，使用门槛较高。")

    if has_deps:
        parts.append("仓库提供了依赖声明，环境配置有据可循。")
    else:
        parts.append("仓库未提供明确的依赖声明，环境配置可能困难。")

    if risk_level == "HIGH":
        if not has_data and not has_weight:
            parts.append("数据集和模型权重说明均不完整，建议在投入复现前优先确认数据与权重获取方式。")
        elif not has_data:
            parts.append("数据集说明不完整，建议在投入复现前确认数据获取方式。")
        elif not has_weight:
            parts.append("模型权重说明不完整，建议在投入复现前确认权重获取方式。")

    if risk_level == "MEDIUM":
        parts.append(
            "部分关键文件或说明可能不完整，建议先确认环境和数据后，从小规模 demo/推理入手。"
        )

    if risk_level == "LOW":
        parts.append(
            "仓库文档和关键文件较为齐全，复现条件较为成熟，但仍建议锁定依赖版本后逐步复现。"
        )

    return " ".join(parts)


def _build_method_summary(title: str, abstract_text: str) -> str:
    """根据摘要生成方法描述"""
    if not abstract_text or not abstract_text.strip():
        return "未获取到论文摘要，暂无法总结核心方法。"

    excerpt = abstract_text.strip()[:500]

    return (
        f"根据论文摘要，该论文《{title}》的主要内容如下：{excerpt}"
        f"{'…（摘要已截断）' if len(abstract_text) > 500 else ''} "
        "由于当前 V1 阶段未接入深度论文理解模型，以上方法总结仅基于摘要文本生成，仅供参考。"
    )


def _build_innovation_summary(title: str, abstract_text: str) -> str:
    """生成保守的创新点总结"""
    if not abstract_text or not abstract_text.strip():
        return "未获取到论文摘要，暂无法分析创新点。"

    text_lower = abstract_text.lower()
    signals = []

    keyword_map = {
        "novel": "novel",
        "propose": "propose",
        "state-of-the-art": "state-of-the-art",
        "outperform": "outperform",
        "efficient": "efficient",
        "framework": "framework",
        "first": "first",
    }

    for kw, cn in keyword_map.items():
        if kw in text_lower:
            signals.append(cn)

    base = (
        "V1 阶段暂不对创新点做强判断，建议结合论文正文进一步确认。"
    )

    if signals:
        base += (
            f"从摘要中出现 {'、'.join(signals)} 等表述来看，"
            "作者强调了方法或框架层面的改进。"
        )
    else:
        base += "从摘要看，论文的创新点可能体现在方法设计、实验验证或任务设定上。"

    base += "该部分仅作为初步参考，不构成对论文创新性的正式评估。"

    return base


def _build_reproduce_steps(has_repo: bool, repo: dict, file_presence: dict) -> str:
    """根据仓库分析生成复现步骤"""
    if not has_repo:
        return "当前未找到可分析的代码仓库，建议先手动补充仓库链接后再生成复现步骤。"

    repo_url = (repo or {}).get("repoUrl", "")
    fp = file_presence or {}

    steps = [f"1. 克隆仓库：{repo_url}" if repo_url else "1. 获取仓库代码"]

    has_readme = fp.get("hasReadme", False)
    has_docker = fp.get("hasDockerfile", False)
    has_env_yml = fp.get("hasEnvironmentYml", False)
    has_req = fp.get("hasRequirements", False)
    has_train = fp.get("hasTrainCode", False)
    has_infer = fp.get("hasInferenceCode", False)
    has_data = fp.get("hasDatasetDoc", False)
    has_weight = fp.get("hasWeightDoc", False)

    if has_readme:
        steps.append("2. 阅读 README，确认安装方式与运行入口")

    # 环境配置
    env_step = None
    if has_docker:
        env_step = "3. 优先尝试 Docker 环境部署（检测到 Dockerfile）"
    elif has_env_yml:
        env_step = "3. 可优先使用 Conda 环境配置（检测到 environment.yml）"
    elif has_req:
        env_step = "3. 使用 pip 安装依赖：pip install -r requirements.txt"

    if env_step:
        steps.append(env_step)
        step_num = 4
    else:
        step_num = 3

    # 数据集
    if has_data:
        steps.append(f"{step_num}. 根据 README 或项目目录准备数据集")
        step_num += 1
    else:
        steps.append(f"{step_num}. 需要人工确认数据集来源（未检测到数据集说明）")
        step_num += 1

    # 权重
    if has_weight:
        steps.append(f"{step_num}. 如仓库提供权重说明，下载预训练模型权重")
        step_num += 1

    # 运行
    if has_infer:
        steps.append(f"{step_num}. 优先尝试 demo / inference / predict 脚本验证模型")
        step_num += 1

    if has_train:
        steps.append(f"{step_num}. 尝试训练脚本或完整实验复现")
        step_num += 1

    # 缺失提示
    if not has_infer and not has_train:
        steps.append(f"{step_num}. 注意：未检测到训练或推理入口，需自行确认运行方式")
    elif not has_infer:
        steps.append(f"{step_num}. 注意：未检测到推理/demo 入口，需自行寻找验证方法")
    elif not has_train:
        steps.append(f"{step_num}. 注意：未检测到训练入口，可能仅有推理代码")

    return "\n".join(steps)


def _build_risk_tips(risk_level: str, score_details: dict, file_presence: dict) -> str:
    """根据风险等级和评分细节生成风险提示"""
    sd = score_details or {}
    fp = file_presence or {}
    tips = []

    # 风险等级基础说明
    if risk_level == "HIGH":
        tips.append("【高风险】不建议直接投入大量时间复现。")
        tips.append("建议：")
        tips.append("- 优先确认仓库是否为论文官方实现")
        tips.append("- 检查是否有官方提供的替代仓库")
        tips.append("- 确认数据集、模型权重和依赖是否可获得")
        if not fp.get("hasReadme"):
            tips.append("- 手动寻找 README 或相关文档")
    elif risk_level == "MEDIUM":
        tips.append("【中等风险】复现存在一定不确定性，建议谨慎推进。")
        tips.append("建议：")
        tips.append("- 优先运行 demo 或推理脚本验证仓库可用性")
        tips.append("- 检查依赖库版本兼容性")
        if not fp.get("hasDatasetDoc"):
            tips.append("- 提前确认数据集获取方式")
        if not fp.get("hasWeightDoc"):
            tips.append("- 提前确认预训练权重是否可获取")
    else:
        tips.append("【低风险】仓库完整度较好，复现风险较低。")
        tips.append("建议：")
        tips.append("- 锁定 Python / CUDA / 依赖库版本以提升可复现性")
        tips.append("- 先在单卡上验证 demo，再扩展至完整训练")
        tips.append("- 注意不同硬件环境下的性能差异")

    # 合并 score_details 中的风险因素
    risk_factors = sd.get("riskFactors", [])
    if risk_factors:
        tips.append("")
        tips.append("检测到以下风险因素：")
        for factor in risk_factors:
            tips.append(f"- {factor}")

    # 合并负面因素
    negatives = sd.get("negativeFactors", [])
    if negatives:
        tips.append("")
        tips.append("其他待改进项：")
        for item in negatives:
            tips.append(f"- {item}")

    return "\n".join(tips)


def _build_final_advice(risk_level: str, reproducibility_score: int, has_repo: bool) -> str:
    """生成最终建议"""
    if not has_repo:
        return (
            "不建议直接复现。当前未找到可分析代码仓库，建议手动指定官方仓库链接后重新分析。"
            "如有官方代码仓库，提交后系统将自动评估复现可行性。"
        )

    if risk_level == "LOW":
        return (
            "推荐尝试复现。仓库文件齐全、文档较为完整，建议先运行官方 demo 或推理脚本，"
            "确认代码可用后再尝试完整训练流程。复现时注意锁定依赖版本以保证结果一致性。"
        )
    elif risk_level == "MEDIUM":
        return (
            "谨慎复现。仓库结构基本完整，但存在部分缺失项。建议先确认数据集、模型权重和"
            "环境依赖的可获得性，从小规模实验入手，逐步推进到完整复现。"
        )
    else:
        return (
            "不建议直接复现。仓库文档或关键文件缺失较多，复现可行性低。建议先确认仓库"
            "真实性、联系论文作者获取官方实现，或等待社区提供更完整的开源版本后再评估。"
        )


# ═══════════════════════════════════════════════════════════
# 节点入口
# ═══════════════════════════════════════════════════════════


def generate_report_node(state: GraphState) -> GraphState:
    """
    生成中文报告（方法总结、创新点、复现步骤、风险提示、最终建议）。

    基于规则模板，不依赖 LLM。
    """
    task_id = state.get("task_id", "unknown")
    logger.info(f"[task={task_id}] generate_report_node: start")

    try:
        # ── 输入 ──
        title = state.get("title", "未知论文")
        abstract_text = state.get("abstract_text", "")
        arxiv_id = state.get("arxiv_id", "")

        selected_repo = state.get("selected_repo") or {}
        has_repo = bool(selected_repo and selected_repo.get("repoName"))
        repo_name = selected_repo.get("repoName", "")

        file_presence = state.get("file_presence", {})
        readme_quality_score = state.get("readme_quality_score", 0)
        reproducibility_score = state.get("reproducibility_score", 0)
        completeness_score = state.get("completeness_score", 0)
        environment_score = state.get("environment_score", 0)
        risk_level = state.get("risk_level", "HIGH")
        score_details = state.get("score_details", {})

        # ── 生成各部分 ──
        summary = _build_summary(
            has_repo, repo_name, completeness_score, environment_score,
            reproducibility_score, risk_level, file_presence, readme_quality_score,
        )
        method_summary = _build_method_summary(title, abstract_text)
        innovation_summary = _build_innovation_summary(title, abstract_text)
        reproduce_steps = _build_reproduce_steps(has_repo, selected_repo, file_presence)
        risk_tips = _build_risk_tips(risk_level, score_details, file_presence)
        final_advice = _build_final_advice(risk_level, reproducibility_score, has_repo)

        # ── 写入 state ──
        state["summary"] = summary
        state["method_summary"] = method_summary
        state["innovation_summary"] = innovation_summary
        state["reproduce_steps"] = reproduce_steps
        state["risk_tips"] = risk_tips
        state["final_advice"] = final_advice

        logger.info(
            f"[task={task_id}] generate_report_node: done, risk={risk_level}, "
            f"has_repo={has_repo}, reproducibility={reproducibility_score}"
        )
    except Exception as e:
        logger.error(f"[task={task_id}] generate_report_node failed: {e}")
        state["error"] = str(e)

    return state
