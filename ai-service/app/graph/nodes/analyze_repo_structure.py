"""
AnalyzeRepoStructureNode — 分析仓库文件结构
"""

from app.graph.state import GraphState
from app.tools.repo_file_tool import fetch_repo_file_tree, analyze_file_presence, summarize_file_matches
from app.core.logger import logger


def analyze_repo_structure_node(state: GraphState) -> GraphState:
    """
    通过 GitHub API 获取文件树，检查关键文件
    """
    repo = state.get("selected_repo")
    task_id = state.get("task_id", "unknown")

    if repo is None:
        logger.warning(f"[task={task_id}] No repo selected, skipping structure analysis")
        return state

    logger.info(f"[task={task_id}] analyze_repo_structure_node: start, repo={repo.get('repoName')}")

    try:
        # 获取文件树
        file_tree = fetch_repo_file_tree(
            owner=repo.get("owner", ""),
            repo_name=repo.get("repoName", ""),
            branch=repo.get("defaultBranch", "main"),
        )

        files = file_tree.get("files", [])

        if file_tree.get("error"):
            logger.warning(f"[task={task_id}] File tree fetch had errors: {file_tree['error']}")
            # 不中断流程，写入空结果
            state["repo_structure"] = file_tree
            state["file_presence"] = {
                "hasReadme": False, "hasRequirements": False,
                "hasEnvironmentYml": False, "hasDockerfile": False,
                "hasLicense": False, "hasTrainCode": False,
                "hasInferenceCode": False, "hasDatasetDoc": False,
                "hasWeightDoc": False,
            }
            state["file_matches"] = {
                "readmeFiles": [], "dependencyFiles": [], "dockerFiles": [],
                "licenseFiles": [], "trainFiles": [], "inferenceFiles": [],
                "datasetRelatedFiles": [], "weightRelatedFiles": [],
            }
        else:
            # 分析文件存在性
            file_presence = analyze_file_presence(files)
            # 汇总匹配详情
            file_matches = summarize_file_matches(files)

            state["repo_structure"] = file_tree
            state["file_presence"] = file_presence
            state["file_matches"] = file_matches

        logger.info(f"[task={task_id}] analyze_repo_structure_node: done ({len(files)} files)")
    except Exception as e:
        logger.error(f"[task={task_id}] analyze_repo_structure_node failed: {e}")
        state["error"] = str(e)

    return state
