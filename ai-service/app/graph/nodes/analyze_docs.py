"""
AnalyzeDocsNode — 分析 README 内容

通过 GitHub API 读取真实 README 内容，并用规则判断文档各部分的完整性。
"""

from app.graph.state import GraphState
from app.tools.repo_file_tool import fetch_readme_content
from app.core.logger import logger

# ───────────────────── 关键词规则 ─────────────────────

_INSTALL_KEYWORDS = [
    "install", "installation", "setup", "environment",
    "requirements", "conda", "pip install", "dependencies",
]

_TRAIN_KEYWORDS = [
    "train", "training", "finetune", "fine-tune",
    "pretrain", "pre-training",
]

_INFERENCE_KEYWORDS = [
    "inference", "infer", "predict", "prediction", "demo",
    "evaluation", "eval", "test", "quick start", "usage",
]

_DATASET_KEYWORDS = [
    "dataset", "data preparation", "prepare data", "download data",
    "benchmark", "coco", "imagenet", "cityscapes", "glue", "squad",
]

_WEIGHT_KEYWORDS = [
    "checkpoint", "checkpoints", "pretrained", "pre-trained",
    "weights", "model zoo", "download model", "ckpt", ".pth",
]

_CITATION_KEYWORDS = ["citation", "bibtex", "cite"]

_EXAMPLE_COMMAND_KEYWORDS = [
    "```bash", "```sh", "```python",
    "python ", "pip ", "conda ",
    "cuda_visible_devices", "torchrun",
]


def _contains_any(text: str, keywords: list) -> bool:
    """检查文本中是否包含任一关键词（忽略大小写）"""
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def analyze_readme_sections(content: str) -> dict:
    """
    基于关键词规则分析 README 各部分说明的完整性。

    Returns:
        dict 包含各 section 是否存在及 README 长度
    """
    if not content:
        return {
            "hasInstallSection": False,
            "hasTrainSection": False,
            "hasInferenceSection": False,
            "hasDatasetSection": False,
            "hasWeightSection": False,
            "hasCitationSection": False,
            "hasExampleCommands": False,
            "readmeLength": 0,
        }

    return {
        "hasInstallSection": _contains_any(content, _INSTALL_KEYWORDS),
        "hasTrainSection": _contains_any(content, _TRAIN_KEYWORDS),
        "hasInferenceSection": _contains_any(content, _INFERENCE_KEYWORDS),
        "hasDatasetSection": _contains_any(content, _DATASET_KEYWORDS),
        "hasWeightSection": _contains_any(content, _WEIGHT_KEYWORDS),
        "hasCitationSection": _contains_any(content, _CITATION_KEYWORDS),
        "hasExampleCommands": _contains_any(content, _EXAMPLE_COMMAND_KEYWORDS),
        "readmeLength": len(content),
    }


def _calc_readme_quality_score(analysis: dict) -> int:
    """
    根据 README 分析结果计算 0-100 质量分。

    基础分 20，如果 README 为空则为 0。
    """
    readme_length = analysis.get("readmeLength", 0)
    if readme_length == 0:
        return 0

    score = 20  # 基础分

    if analysis.get("hasInstallSection"):
        score += 15
    if analysis.get("hasTrainSection"):
        score += 15
    if analysis.get("hasInferenceSection"):
        score += 15
    if analysis.get("hasDatasetSection"):
        score += 15
    if analysis.get("hasWeightSection"):
        score += 10
    if analysis.get("hasExampleCommands"):
        score += 10
    if analysis.get("hasCitationSection"):
        score += 5
    if readme_length >= 1000:
        score += 5

    return min(score, 100)


def analyze_docs_node(state: GraphState) -> GraphState:
    """
    分析 README 等文档内容，判断各部分说明的完整性。

    通过 GitHub API 读取真实 README 内容，用规则分析。
    """
    task_id = state.get("task_id", "unknown")
    logger.info(f"[task={task_id}] analyze_docs_node: start")

    try:
        repo = state.get("selected_repo")
        if repo is None:
            logger.warning(f"[task={task_id}] No repo selected, skipping docs analysis")
            state["readme_quality_score"] = 0
            return state

        owner = repo.get("owner", "")
        repo_name = repo.get("repoName", "")
        branch = repo.get("defaultBranch", "main")

        # 从 repo_structure 获取文件列表
        repo_structure = state.get("repo_structure", {})
        files = repo_structure.get("files") if isinstance(repo_structure, dict) else None

        # 读取真实 README
        readme_result = fetch_readme_content(owner, repo_name, branch, files)
        readme_content = readme_result.get("content", "")
        readme_path = readme_result.get("path") or ""
        readme_size = readme_result.get("size", 0)
        readme_error = readme_result.get("error")

        # 无 README 内容 → 全部 false，score 0
        if readme_error and not readme_content:
            logger.warning(f"[task={task_id}] README not available for {owner}/{repo_name}: {readme_error}")
            empty_analysis = analyze_readme_sections("")
            state["readme"] = {"path": None, "size": 0, "excerpt": ""}
            state["readme_analysis"] = empty_analysis
            state["readme_quality_score"] = 0
            return state

        # 规则分析 README 内容
        analysis = analyze_readme_sections(readme_content)
        score = _calc_readme_quality_score(analysis)

        # file_presence 联动：README 中检测到数据集/权重说明
        file_presence = state.get("file_presence", {})
        if isinstance(file_presence, dict):
            if analysis.get("hasDatasetSection"):
                file_presence["hasDatasetDoc"] = True
            if analysis.get("hasWeightSection"):
                file_presence["hasWeightDoc"] = True
            state["file_presence"] = file_presence

        # 写入 state
        state["readme"] = {
            "path": readme_path,
            "size": readme_size,
            "excerpt": readme_content[:2000],
        }
        state["readme_analysis"] = analysis
        state["readme_quality_score"] = score

        logger.info(f"[task={task_id}] analyze_docs_node: done, quality_score={score}, "
                     f"install={analysis['hasInstallSection']}, "
                     f"train={analysis['hasTrainSection']}, "
                     f"inference={analysis['hasInferenceSection']}")
    except Exception as e:
        logger.error(f"[task={task_id}] analyze_docs_node failed: {e}")
        state["error"] = str(e)

    return state
