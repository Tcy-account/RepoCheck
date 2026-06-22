"""
仓库文件分析工具 — 通过 GitHub REST API 获取真实文件树结构及文件内容
"""

import os
import re
import base64
import requests
from typing import List, Dict, Optional
from app.core.logger import logger

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 15
MAX_README_CHARS = 20000

# ───────────────────── 文件匹配规则 ─────────────────────

# README 文件名（忽略大小写）
_README_NAMES = {"readme.md", "readme.rst", "readme.txt", "readme"}

# 依赖文件关键词（匹配完整文件名的尾部分）
_DEPENDENCY_PATTERNS = [
    r"(^|/)requirements\.txt$",
    r"(^|/)requirements-dev\.txt$",
    r"(^|/)requirements/.*\.txt$",
    r"(^|/)pyproject\.toml$",
    r"(^|/)setup\.py$",
    r"(^|/)setup\.cfg$",
    r"(^|/)Pipfile$",
    r"(^|/)poetry\.lock$",
]

# 环境配置文件名
_ENV_YML_NAMES = {"environment.yml", "environment.yaml", "conda.yml", "conda.yaml"}

# Dockerfile 模式
_DOCKERFILE_PATTERN = r"(^|/)Dockerfile([.\-_].*)?$"

# LICENSE 文件名
_LICENSE_NAMES = {"license", "license.md", "license.txt", "copying"}

# 训练代码关键词（匹配路径尾部文件名）
_TRAIN_NAMES = {"train.py", "training.py", "main.py", "run_train.py"}
_TRAIN_PATH_PATTERNS = [r"(^|/)scripts/train\.[a-z]+$", r"(^|/)tools/train\.py$"]

# 推理/演示代码关键词
_INFERENCE_NAMES = {
    "demo.py", "infer.py", "inference.py", "predict.py",
    "eval.py", "evaluate.py", "test.py",
    "app.py", "web_demo.py", "gradio_app.py",
}

# 数据集相关路径关键词
_DATASET_KEYWORDS = ["data", "dataset", "datasets", "download_data", "prepare_data"]

# 权重/模型文件路径关键词
_WEIGHT_KEYWORDS = ["checkpoint", "checkpoints", "weight", "weights", "pretrained", "model_zoo", "ckpt", ".pth"]


def _build_headers() -> dict:
    """构造 GitHub API 请求头"""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RepoCheck-AI-Service",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("GITHUB_TOKEN is not set; using unauthenticated GitHub API requests (rate limit: 60/hr)")
    return headers


def _request_tree(owner: str, repo_name: str, branch: str) -> tuple:
    """请求 GitHub git/trees API，返回 (data, error)"""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/git/trees/{branch}"
    params = {"recursive": "1"}
    headers = _build_headers()

    logger.info(f"Fetching file tree: {owner}/{repo_name} branch={branch}")
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        return None, f"Network error: {e}"

    if resp.status_code == 404:
        return None, f"Branch or repo not found: {branch}"
    if resp.status_code in (401, 403):
        detail = resp.text[:200]
        return None, f"GitHub API auth error ({resp.status_code}): {detail}"
    if not resp.ok:
        return None, f"GitHub API returned status {resp.status_code}"

    try:
        data = resp.json()
    except ValueError as e:
        return None, f"Failed to parse JSON response: {e}"

    return data, None


def _extract_files(tree_data: dict) -> list:
    """从 GitHub tree 数据中提取文件列表，只保留 blob 类型的 path"""
    files = []
    for item in tree_data.get("tree", []):
        if item.get("type") == "blob":
            files.append(item["path"])
    return files


def fetch_repo_file_tree(owner: str, repo_name: str, branch: str = "main") -> dict:
    """
    获取仓库文件树。

    优先用传入 branch，404 时 fallback main -> master。

    Returns:
        {"files": [...], "total_count": N, "truncated": bool}
        失败时 files=[], total_count=0, 附加 "error" 字段
    """
    if not owner or not repo_name:
        return {"files": [], "total_count": 0, "truncated": False, "error": "owner or repo_name is empty"}

    # 尝试请求：传入 branch -> main -> master
    branches_to_try = list(dict.fromkeys([branch, "main", "master"]))  # 去重保持顺序
    data = None
    last_error = ""

    for br in branches_to_try:
        data, err = _request_tree(owner, repo_name, br)
        if data is not None:
            logger.info(f"Successfully fetched tree for {owner}/{repo_name} on branch '{br}'")
            break
        last_error = err
        logger.warning(f"Tree request failed for branch '{br}': {err}")

    if data is None:
        logger.error(f"Failed to fetch tree for {owner}/{repo_name}: {last_error}")
        return {"files": [], "total_count": 0, "truncated": False, "error": last_error}

    files = _extract_files(data)
    truncated = data.get("truncated", False)

    if truncated:
        logger.warning(f"Tree for {owner}/{repo_name} is truncated; analyzing {len(files)} files")

    result = {"files": files, "total_count": len(files), "truncated": truncated}
    logger.info(f"Fetched {len(files)} files from {owner}/{repo_name}")
    return result


def analyze_file_presence(files: List[str]) -> dict:
    """
    分析文件存在性，返回检查结果。
    """
    result = {
        "hasReadme": False,
        "hasRequirements": False,
        "hasEnvironmentYml": False,
        "hasDockerfile": False,
        "hasLicense": False,
        "hasTrainCode": False,
        "hasInferenceCode": False,
        "hasDatasetDoc": False,
        "hasWeightDoc": False,
    }

    for path in files:
        name = path.split("/")[-1].lower()
        path_lower = path.lower()

        # README（根目录权重高，子目录也算）
        if name in _README_NAMES:
            result["hasReadme"] = True

        # 依赖文件
        for pat in _DEPENDENCY_PATTERNS:
            if re.search(pat, path):
                result["hasRequirements"] = True
                break

        # environment.yml
        if name in _ENV_YML_NAMES:
            result["hasEnvironmentYml"] = True

        # Dockerfile
        if re.search(_DOCKERFILE_PATTERN, path):
            result["hasDockerfile"] = True

        # LICENSE
        if name in _LICENSE_NAMES:
            result["hasLicense"] = True

        # 训练代码
        if name in _TRAIN_NAMES:
            result["hasTrainCode"] = True
        else:
            for pat in _TRAIN_PATH_PATTERNS:
                if re.search(pat, path_lower):
                    result["hasTrainCode"] = True
                    break

        # 推理代码
        if name in _INFERENCE_NAMES:
            result["hasInferenceCode"] = True

        # 数据集相关
        for kw in _DATASET_KEYWORDS:
            if kw in path_lower:
                result["hasDatasetDoc"] = True
                break

        # 权重/模型文件
        for kw in _WEIGHT_KEYWORDS:
            if kw in path_lower:
                result["hasWeightDoc"] = True
                break

        # 如果全部 true 了可以提前退出
        if all(result.values()):
            break

    logger.info(f"File presence analysis: {result}")
    return result


def summarize_file_matches(files: List[str]) -> dict:
    """
    按类别汇总匹配到的文件列表，供 state["file_matches"] 使用。
    """
    matches: Dict[str, List[str]] = {
        "readmeFiles": [],
        "dependencyFiles": [],
        "dockerFiles": [],
        "licenseFiles": [],
        "trainFiles": [],
        "inferenceFiles": [],
        "datasetRelatedFiles": [],
        "weightRelatedFiles": [],
    }

    for path in files:
        name = path.split("/")[-1].lower()
        path_lower = path.lower()

        # README
        if name in _README_NAMES:
            matches["readmeFiles"].append(path)

        # 依赖文件
        for pat in _DEPENDENCY_PATTERNS:
            if re.search(pat, path):
                matches["dependencyFiles"].append(path)
                break

        # environment（归入 dependencyFiles）
        if name in _ENV_YML_NAMES:
            if path not in matches["dependencyFiles"]:
                matches["dependencyFiles"].append(path)

        # Dockerfile
        if re.search(_DOCKERFILE_PATTERN, path):
            matches["dockerFiles"].append(path)

        # LICENSE
        if name in _LICENSE_NAMES:
            matches["licenseFiles"].append(path)

        # 训练代码
        if name in _TRAIN_NAMES:
            matches["trainFiles"].append(path)
        else:
            for pat in _TRAIN_PATH_PATTERNS:
                if re.search(pat, path_lower):
                    matches["trainFiles"].append(path)
                    break

        # 推理代码
        if name in _INFERENCE_NAMES:
            matches["inferenceFiles"].append(path)

        # 数据集
        for kw in _DATASET_KEYWORDS:
            if kw in path_lower:
                matches["datasetRelatedFiles"].append(path)
                break

        # 权重
        for kw in _WEIGHT_KEYWORDS:
            if kw in path_lower:
                matches["weightRelatedFiles"].append(path)
                break

    return matches


# ───────────────────── README 读取 ─────────────────────


def _select_readme_path(files: Optional[List[str]]) -> Optional[str]:
    """从文件列表中按优先级选择 README 文件路径"""
    if not files:
        return None

    # 优先级：根目录 README.md > .rst > .txt > readme.md > 子目录 README
    candidates = []
    for f in files:
        name = f.split("/")[-1].lower()
        depth = f.count("/")
        if name == "readme.md":
            candidates.append((0 if depth == 0 else 4, depth, f))
        elif name == "readme.rst":
            candidates.append((1 if depth == 0 else 5, depth, f))
        elif name == "readme.txt":
            candidates.append((2 if depth == 0 else 6, depth, f))
        elif name == "readme":
            candidates.append((3 if depth == 0 else 7, depth, f))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def _fetch_file_content_via_api(owner: str, repo_name: str, path: str, branch: str) -> dict:
    """通过 GitHub Contents API 读取单个文件内容"""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/contents/{path}"
    params = {"ref": branch}
    headers = _build_headers()

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        return {"path": path, "content": "", "size": 0, "error": f"Network error: {e}"}

    if resp.status_code == 404:
        return {"path": path, "content": "", "size": 0, "error": f"File not found: {path} on branch {branch}"}
    if resp.status_code in (401, 403):
        detail = resp.text[:200]
        return {"path": path, "content": "", "size": 0, "error": f"GitHub API auth error ({resp.status_code}): {detail}"}
    if not resp.ok:
        return {"path": path, "content": "", "size": 0, "error": f"GitHub API returned status {resp.status_code}"}

    try:
        data = resp.json()
    except ValueError as e:
        return {"path": path, "content": "", "size": 0, "error": f"Failed to parse JSON: {e}"}

    content_raw = data.get("content", "")
    encoding = data.get("encoding", "")
    size = data.get("size", 0)

    if encoding == "base64" and content_raw:
        try:
            decoded = base64.b64decode(content_raw).decode("utf-8", errors="replace")
        except Exception as e:
            return {"path": path, "content": "", "size": size, "error": f"Base64 decode failed: {e}"}
        # 截断
        if len(decoded) > MAX_README_CHARS:
            decoded = decoded[:MAX_README_CHARS]
            logger.info(f"README truncated from {len(decoded)} to {MAX_README_CHARS} chars")
        return {"path": data.get("path", path), "content": decoded, "size": size, "error": None}
    else:
        return {"path": data.get("path", path), "content": "", "size": size, "error": "Unknown or missing encoding"}


def fetch_readme_content(
    owner: str,
    repo_name: str,
    branch: str = "main",
    files: Optional[List[str]] = None,
) -> dict:
    """
    读取仓库 README 文件内容。

    优先从 files 中按优先级选择 README 路径，通过 Contents API 获取。
    如果 files 为空或无 README，则用 GET /repos/{owner}/{repo}/readme 兜底。

    Returns:
        {"path": "...", "content": "...", "size": N, "error": None}  成功
        {"path": None, "content": "", "size": 0, "error": "..."}     失败
    """
    if not owner or not repo_name:
        return {"path": None, "content": "", "size": 0, "error": "owner or repo_name is empty"}

    # 1. 从 files 中选择 README 路径
    readme_path = _select_readme_path(files) if files else None

    if readme_path:
        logger.info(f"Reading README via Contents API: {owner}/{repo_name}/{readme_path} (branch={branch})")
        result = _fetch_file_content_via_api(owner, repo_name, readme_path, branch)
        if result.get("error") is None:
            logger.info(f"README loaded: {result['path']}, {result['size']} bytes")
            return result
        logger.warning(f"Contents API failed for {readme_path}: {result['error']}")

    # 2. 兜底：GET /repos/{owner}/{repo}/readme
    logger.info(f"Falling back to /readme API for {owner}/{repo_name}")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/readme"
    headers = _build_headers()

    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        return {"path": None, "content": "", "size": 0, "error": f"Network error: {e}"}

    if resp.status_code == 404:
        return {"path": None, "content": "", "size": 0, "error": "No README found in repository"}
    if resp.status_code in (401, 403):
        detail = resp.text[:200]
        return {"path": None, "content": "", "size": 0, "error": f"GitHub API auth error ({resp.status_code}): {detail}"}
    if not resp.ok:
        return {"path": None, "content": "", "size": 0, "error": f"GitHub API returned status {resp.status_code}"}

    try:
        data = resp.json()
    except ValueError as e:
        return {"path": None, "content": "", "size": 0, "error": f"Failed to parse JSON: {e}"}

    content_raw = data.get("content", "")
    encoding = data.get("encoding", "")
    size = data.get("size", 0)

    if encoding == "base64" and content_raw:
        try:
            decoded = base64.b64decode(content_raw).decode("utf-8", errors="replace")
        except Exception as e:
            return {"path": data.get("path"), "content": "", "size": size, "error": f"Base64 decode failed: {e}"}
        if len(decoded) > MAX_README_CHARS:
            decoded = decoded[:MAX_README_CHARS]
        logger.info(f"README loaded via /readme API: {data.get('path')}, {size} bytes")
        return {"path": data.get("path"), "content": decoded, "size": size, "error": None}
    else:
        return {"path": data.get("path"), "content": "", "size": size, "error": "Unknown or missing encoding"}
