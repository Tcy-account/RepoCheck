"""
解析器 + 风险评分工具 本地函数级测试

测试用例：
  1. requirements.txt → flash-attn HIGH, torchvision 匹配风险, numpy 未固定提示
  2. environment.yml → pythonVersion=3.10, cudaVersion=11.8, PyTorch, xformers HIGH
  3. Dockerfile → hasDocker, cudaVersion=11.8, deepspeed HIGH
  4. 综合风险评分
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tools.requirements_parser import parse_requirements
from app.tools.environment_yml_parser import parse_environment_yml
from app.tools.pyproject_parser import parse_pyproject
from app.tools.dockerfile_parser import parse_dockerfile
from app.tools.environment_risk_tool import assess_dependency_risks, assess_environment_risk


# ═══════════════════════════════════════════════════════════════
# 用例 1: requirements.txt
# ═══════════════════════════════════════════════════════════════

REQUIREMENTS_CONTENT = """\
torch==2.1.0
torchvision
flash-attn
numpy
"""


def test_requirements():
    print("=" * 60)
    print("TEST 1: requirements_parser")
    print("=" * 60)

    deps = parse_requirements(REQUIREMENTS_CONTENT, "requirements.txt")
    print(f"Parsed {len(deps)} entries:")
    for d in deps:
        print(f"  {d['packageName']:20s} ver={d.get('versionSpec') or '(none)':15s} src={d['source']}")

    # 评分
    deps = assess_dependency_risks(deps)
    print(f"\nAfter risk assessment:")
    for d in deps:
        print(f"  {d['packageName']:20s} riskLevel={d.get('riskLevel','?')} reason={d.get('riskReason','')}")

    # 验证
    flash_attn = next(d for d in deps if d["packageName"] == "flash-attn")
    assert flash_attn["riskLevel"] == "HIGH", f"flash-attn should be HIGH, got {flash_attn['riskLevel']}"
    print("\n  PASS: flash-attn → HIGH ✓")

    torchvision_dep = next(d for d in deps if d["packageName"] == "torchvision")
    assert torchvision_dep["riskLevel"] == "MEDIUM", f"torchvision should be MEDIUM, got {torchvision_dep['riskLevel']}"
    assert "should match" in torchvision_dep.get("riskReason", ""), f"unexpected riskReason: {torchvision_dep.get('riskReason')}"
    print("  PASS: torchvision version mismatch → MEDIUM ✓")

    numpy_dep = next(d for d in deps if d["packageName"] == "numpy")
    assert numpy_dep["riskLevel"] == "MEDIUM", f"numpy should be MEDIUM (unpinned), got {numpy_dep['riskLevel']}"
    assert "Unpinned" in numpy_dep.get("riskReason", ""), f"unexpected riskReason: {numpy_dep.get('riskReason')}"
    print("  PASS: numpy unpinned → MEDIUM ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 2: environment.yml
# ═══════════════════════════════════════════════════════════════

ENVIRONMENT_YML_CONTENT = """\
name: test-env
channels:
  - pytorch
  - nvidia
dependencies:
  - python=3.10
  - pytorch=2.1.0
  - torchvision
  - cudatoolkit=11.8
  - pip
  - pip:
      - transformers>=4.30
      - xformers
"""


def test_environment_yml():
    print("=" * 60)
    print("TEST 2: environment_yml_parser")
    print("=" * 60)

    deps, meta = parse_environment_yml(ENVIRONMENT_YML_CONTENT, "environment.yml")
    print(f"Metadata: {meta}")
    print(f"Parsed {len(deps)} entries:")
    for d in deps:
        print(f"  {d['packageName']:20s} ver={d.get('versionSpec') or '(none)':15s} src={d['source']}")

    # 验证 metadata
    assert meta["pythonVersion"] == "3.10", f"pythonVersion should be 3.10, got {meta['pythonVersion']}"
    print("  PASS: pythonVersion=3.10 ✓")

    assert meta["cudaVersion"] == "11.8", f"cudaVersion should be 11.8, got {meta['cudaVersion']}"
    print("  PASS: cudaVersion=11.8 ✓")

    assert "nvidia" in meta["channels"], f"channels should contain nvidia, got {meta['channels']}"
    print(f"  PASS: channels={meta['channels']} ✓")

    assert meta["hasNvidiaChannel"] is True, "hasNvidiaChannel should be True"
    print("  PASS: hasNvidiaChannel=True ✓")

    assert meta["hasPytorchChannel"] is True, "hasPytorchChannel should be True"
    print("  PASS: hasPytorchChannel=True ✓")

    # 评分
    deps = assess_dependency_risks(deps)
    print(f"\nAfter risk assessment:")
    for d in deps:
        print(f"  {d['packageName']:20s} riskLevel={d.get('riskLevel','?')} src={d.get('source','')}")

    # 验证 PyTorch 框架识别
    env_report = assess_environment_risk(deps, meta)
    print(f"\nEnvironment Analysis:")
    for k, v in env_report.items():
        print(f"  {k}: {v}")

    assert env_report["mainFramework"] == "PyTorch", f"mainFramework should be PyTorch, got {env_report['mainFramework']}"
    print("  PASS: mainFramework=PyTorch ✓")

    assert env_report["requiresGpu"] is True, "requiresGpu should be True"
    print("  PASS: requiresGpu=True ✓")

    assert env_report["pythonVersion"] == "3.10", f"pythonVersion should be 3.10"
    print("  PASS: pythonVersion preserved ✓")

    # xformers HIGH
    xformers_dep = next(d for d in deps if d["packageName"] == "xformers")
    assert xformers_dep["riskLevel"] == "HIGH", f"xformers should be HIGH, got {xformers_dep['riskLevel']}"
    print("  PASS: xformers → HIGH ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 3: Dockerfile
# ═══════════════════════════════════════════════════════════════

DOCKERFILE_CONTENT = """\
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
RUN pip install torch==2.1.0 deepspeed
"""


def test_dockerfile():
    print("=" * 60)
    print("TEST 3: dockerfile_parser")
    print("=" * 60)

    deps, meta = parse_dockerfile(DOCKERFILE_CONTENT, "Dockerfile")
    print(f"Metadata: {meta}")
    print(f"Parsed {len(deps)} entries:")
    for d in deps:
        print(f"  {d['packageName']:50s} src={d['source']}")

    # 验证 metadata
    assert meta["hasDocker"] is True, "hasDocker should be True"
    print("  PASS: hasDocker=True ✓")

    cuda_ver = meta["cudaVersion"]
    assert cuda_ver == "11.8", f"cudaVersion should be 11.8, got {cuda_ver}"
    print("  PASS: cudaVersion=11.8 ✓")

    assert "nvidia/cuda:11.8.0" in meta["dockerBaseImage"], f"baseImage wrong: {meta['dockerBaseImage']}"
    print(f"  PASS: dockerBaseImage={meta['dockerBaseImage']} ✓")

    # 评分
    deps = assess_dependency_risks(deps)
    print(f"\nAfter risk assessment:")
    for d in deps:
        print(f"  {d['packageName']:50s} riskLevel={d.get('riskLevel','?')} reason={d.get('riskReason','')}")

    # 验证 deepspeed HIGH
    deepspeed_dep = next(d for d in deps if d["packageName"] == "deepspeed")
    assert deepspeed_dep["riskLevel"] == "HIGH", f"deepspeed should be HIGH, got {deepspeed_dep['riskLevel']}"
    assert "compiler" in deepspeed_dep.get("riskReason", "").lower()
    print("  PASS: deepspeed → HIGH ✓")

    env_report = assess_environment_risk(deps, meta)
    assert env_report["requiresGpu"] is True, "requiresGpu should be True"
    print("  PASS: requiresGpu=True ✓")

    print(f"\nEnvironment Analysis:")
    for k, v in env_report.items():
        print(f"  {k}: {v}")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 4: 综合 (requirements + environment.yml + Dockerfile 合并)
# ═══════════════════════════════════════════════════════════════

def test_combined():
    """模拟 api/environment.py 合并所有解析器的输出"""
    print("=" * 60)
    print("TEST 4: Combined (simulating api/environment.py merge)")
    print("=" * 60)

    all_deps = []
    metadata = {
        "pythonVersion": None,
        "cudaVersion": None,
        "dockerBaseImage": None,
        "hasDocker": False,
        "channels": [],
        "hasNvidiaChannel": False,
        "hasPytorchChannel": False,
    }

    # 1. requirements
    req_deps = parse_requirements(REQUIREMENTS_CONTENT, "requirements.txt")
    for d in req_deps:
        d["fileType"] = "requirements"
    all_deps.extend(req_deps)

    # 2. environment.yml
    yml_deps, yml_meta = parse_environment_yml(ENVIRONMENT_YML_CONTENT, "environment.yml")
    for d in yml_deps:
        d["fileType"] = "environment_yml"
    all_deps.extend(yml_deps)
    if yml_meta.get("pythonVersion"):
        metadata["pythonVersion"] = yml_meta["pythonVersion"]
    if yml_meta.get("cudaVersion"):
        metadata["cudaVersion"] = yml_meta["cudaVersion"]
    if yml_meta.get("channels"):
        metadata["channels"].extend(yml_meta["channels"])
    if yml_meta.get("hasNvidiaChannel"):
        metadata["hasNvidiaChannel"] = True
    if yml_meta.get("hasPytorchChannel"):
        metadata["hasPytorchChannel"] = True

    # 3. Dockerfile
    docker_deps, docker_meta = parse_dockerfile(DOCKERFILE_CONTENT, "Dockerfile")
    for d in docker_deps:
        d["fileType"] = "dockerfile"
    all_deps.extend(docker_deps)
    metadata["hasDocker"] = True
    if docker_meta.get("cudaVersion"):
        metadata["cudaVersion"] = docker_meta.get("cudaVersion")
    if docker_meta.get("dockerBaseImage"):
        metadata["dockerBaseImage"] = docker_meta.get("dockerBaseImage")

    # 风险评估
    assess_dependency_risks(all_deps)
    report = assess_environment_risk(all_deps, metadata)

    print(f"Total dependencies: {len(all_deps)}")
    print(f"\nAggregate Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")

    # 验证综合结果
    assert report["mainFramework"] == "PyTorch"
    assert report["requiresGpu"] is True
    assert report["hasDocker"] is True
    assert report["cudaVersion"] == "11.8"
    assert report["pythonVersion"] == "3.10"
    print("\n  PASS: Combined report assertions ✓")

    # 验证 xformers 和 deepspeed 都是 HIGH
    high_deps = [d for d in all_deps if d.get("riskLevel") == "HIGH"]
    high_names = {d["packageName"] for d in high_deps}
    print(f"  HIGH-risk packages: {high_names}")
    assert "flash-attn" in high_names, "flash-attn should be HIGH"
    assert "xformers" in high_names, "xformers should be HIGH"
    assert "deepspeed" in high_names, "deepspeed should be HIGH"
    print("  PASS: All HIGH-risk packages detected ✓")

    # riskSummary 不应胡编 CUDA 版本
    assert report.get("riskSummary"), "riskSummary should not be empty"
    print(f"  riskSummary: {report['riskSummary']}")
    print("  PASS: riskSummary generated ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 5: 无 CUDA 的 pyproject (仅 CPU)
# ═══════════════════════════════════════════════════════════════

PYPROJECT_CONTENT = """\
[project]
name = "test-lib"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.23",
    "scipy",
]

[project.optional-dependencies]
dev = ["pytest", "ruff"]

[tool.poetry.dependencies]
python = ">=3.9,<3.12"
requests = "^2.31"
"""


def test_pyproject_no_cuda():
    print("=" * 60)
    print("TEST 5: pyproject.toml (no CUDA / no framework)")
    print("=" * 60)

    deps, meta = parse_pyproject(PYPROJECT_CONTENT, "pyproject.toml")
    print(f"Metadata: {meta}")
    print(f"Parsed {len(deps)} entries:")
    for d in deps:
        print(f"  {d['packageName']:20s} ver={d.get('versionSpec') or '(none)':15s} src={d['source']} "
              f"reason={d.get('riskReason','')}")

    assess_dependency_risks(deps)
    metadata = {
        "pythonVersion": meta.get("pythonVersion"),
        "cudaVersion": None,
        "dockerBaseImage": None,
        "hasDocker": False,
        "channels": [],
        "hasNvidiaChannel": False,
        "hasPytorchChannel": False,
    }
    report = assess_environment_risk(deps, metadata)

    print(f"\nEnvironment Analysis:")
    for k, v in report.items():
        print(f"  {k}: {v}")

    # 无 CUDA 时不应该胡编 CUDA 版本
    assert report["cudaVersion"] is None, f"cudaVersion should be None, got {report['cudaVersion']}"
    print("  PASS: cudaVersion=None ✓")

    assert report["requiresGpu"] is False, "requiresGpu should be False"
    print("  PASS: requiresGpu=False ✓")

    assert report["riskLevel"] in ("LOW", "MEDIUM"), f"riskLevel should be LOW/MEDIUM, got {report['riskLevel']}"
    print(f"  PASS: riskLevel={report['riskLevel']} ✓")

    # riskSummary 应提及未发现 CUDA
    if "CUDA" in report.get("riskSummary", "") or "cuda" in report.get("riskSummary", "").lower():
        print("  PASS: riskSummary mentions CUDA absence ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 6: 边缘测试 — extras / git / editable / index / local
# ═══════════════════════════════════════════════════════════════

EXTRAS_REQUIREMENTS = """\
uvicorn[standard]>=0.23.1
torch==2.1.0 # cuda 11.8
git+https://github.com/user/repo.git
--extra-index-url https://download.pytorch.org/whl/cu118
-e .
./src/mylib
"""


def test_edge_cases():
    print("=" * 60)
    print("TEST 6: Edge cases (extras, git, editable, index, local)")
    print("=" * 60)

    deps = parse_requirements(EXTRAS_REQUIREMENTS, "requirements.txt")
    for d in deps:
        print(f"  {d['packageName']:30s} ver={d.get('versionSpec') or '(none)':20s} src={d['source']:12s} risk={d.get('riskLevel','-')}")

    # 验证 extras
    uvicorn_dep = next(d for d in deps if d["packageName"] == "uvicorn")
    assert "[standard]" in (uvicorn_dep.get("versionSpec") or ""), f"should preserve extras: {uvicorn_dep.get('versionSpec')}"
    print("  PASS: extras [standard] preserved ✓")

    # 验证 git
    git_dep = next(d for d in deps if d["source"] == "git")
    assert git_dep["riskLevel"] == "MEDIUM"
    print(f"  PASS: git dep → {git_dep['packageName']} (M) ✓")

    # 验证 custom index
    idx_dep = next(d for d in deps if d["source"] == "pip-index")
    assert idx_dep["riskLevel"] == "MEDIUM"
    print("  PASS: custom index → MEDIUM ✓")

    # 验证 editable
    edit_dep = next(d for d in deps if d["source"] == "editable")
    assert edit_dep["riskLevel"] == "MEDIUM"
    print("  PASS: editable → editable-local-root (M) ✓")

    # 验证 local
    local_dep = next(d for d in deps if d["source"] == "local")
    assert local_dep["riskLevel"] == "HIGH"
    print("  PASS: local path → HIGH ✓")

    # 行内注释不应出现在 versionSpec
    torch_dep = next(d for d in deps if d["packageName"] == "torch")
    assert "cuda" not in (torch_dep.get("versionSpec") or "").lower(), f"comment leaked into versionSpec: {torch_dep.get('versionSpec')}"
    print("  PASS: inline comment stripped ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# 用例 7: Dockerfile 多行续行
# ═══════════════════════════════════════════════════════════════

DOCKERFILE_MULTILINE = r"""\
FROM python:3.10-slim
RUN pip install \
    torch==2.1.0 \
    numpy \
    transformers
RUN apt-get install -y \
    libgl1 \
    ffmpeg
"""


def test_dockerfile_multiline():
    print("=" * 60)
    print("TEST 7: Dockerfile multiline continuation")
    print("=" * 60)

    deps, meta = parse_dockerfile(DOCKERFILE_MULTILINE, "Dockerfile")
    print(f"Metadata: {meta}")
    print(f"Parsed {len(deps)} entries:")
    for d in deps:
        print(f"  {d['packageName']:30s} src={d['source']:6s} riskLevel={d.get('riskLevel','-')}")

    # 验证多行合并
    pip_deps = [d for d in deps if d["source"] == "pip"]
    pip_names = {d["packageName"] for d in pip_deps}
    assert "torch" in pip_names, f"torch missing from pip deps: {pip_names}"
    assert "numpy" in pip_names, f"numpy missing from pip deps: {pip_names}"
    assert "transformers" in pip_names, f"transformers missing from pip deps: {pip_names}"
    print(f"  PASS: multiline pip deps → {pip_names} ✓")

    apt_deps = [d for d in deps if d["source"] == "apt"]
    apt_names = {d["packageName"] for d in apt_deps}
    assert "ffmpeg" in apt_names, f"ffmpeg missing: {apt_names}"
    assert "libgl1" in apt_names, f"libgl1 missing: {apt_names}"
    print(f"  PASS: multiline apt deps → {apt_names} ✓")

    # Python version from FROM
    assert meta["pythonVersion"] == "3.10", f"pythonVersion should be 3.10, got {meta['pythonVersion']}"
    print("  PASS: pythonVersion=3.10 from FROM ✓")

    print()


# ═══════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   V2.0 Parser & Risk Tool — Local Unit Tests       ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    failed = 0

    try:
        test_requirements()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_environment_yml()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_dockerfile()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_combined()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_pyproject_no_cuda()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_edge_cases()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    try:
        test_dockerfile_multiline()
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    print()
    print("=" * 60)
    if failed:
        print(f"  {failed} TEST(s) FAILED!")
    else:
        print("  ALL TESTS PASSED!")
    print("=" * 60)
