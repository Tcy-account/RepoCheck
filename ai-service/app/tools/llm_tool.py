"""
LLM 工具 — 封装 LLM 调用

V1: mock 实现，返回模板化文本
TODO: 接入 LangChain + OpenAI
"""

from app.core.config import settings
from app.core.logger import logger


def generate_report_content(
    paper_title: str,
    paper_abstract: str,
    repo_analysis: dict,
    risk_level: str,
) -> dict:
    """
    调用 LLM 生成报告内容

    V1: 基于规则生成（mock）
    """
    logger.info(f"Generating report for: {paper_title}")

    # TODO: 真实 LLM 调用
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(
    #     api_key=settings.OPENAI_API_KEY,
    #     base_url=settings.OPENAI_BASE_URL,
    #     model=settings.LLM_MODEL,
    # )
    # prompt = f"..."
    # response = llm.invoke(prompt)
    # ...

    has_readme = repo_analysis.get("hasReadme", False)
    has_deps = repo_analysis.get("hasRequirements", False)
    has_docker = repo_analysis.get("hasDockerfile", False)

    return {
        "summary": f"该论文《{paper_title}》的代码仓库进行了静态分析。"
                   f"仓库结构完整度{'较高' if has_readme else '一般'}，"
                   f"依赖管理{'较为完善' if has_deps else '需要加强'}。"
                   f"整体复现风险为 {risk_level}。",
        "methodSummary": f"从论文摘要分析，本文提出了一种创新方法。"
                         f"核心思路：{paper_abstract[:200]}...",
        "innovationSummary": "1. 提出新的方法框架\n2. 在多个基准测试上取得改进\n3. 开源代码实现",
        "reproduceSteps": "1. 克隆代码仓库\n2. 安装依赖：pip install -r requirements.txt\n"
                          "3. 准备数据集\n4. 运行训练：python train.py\n"
                          "5. 运行推理：python infer.py",
        "riskTips": f"{'缺少 README 文档说明' if not has_readme else 'README 文档齐全'}\n"
                   f"{'缺少依赖文件' if not has_deps else '依赖文件齐全'}\n"
                   f"{'缺少 Docker 环境' if not has_docker else 'Docker 环境可用'}\n"
                   "建议：在复现前确认数据集和预训练权重是否可用。",
    }


def analyze_readme_quality(readme_text: str) -> int:
    """
    分析 README 质量 (0-100)

    V1: 关键词匹配
    """
    if not readme_text:
        return 30

    score = 50
    keywords = ["install", "train", "inference", "dataset", "model", "result"]
    readme_lower = readme_text.lower()

    for kw in keywords:
        if kw in readme_lower:
            score += 10

    return min(score, 100)
