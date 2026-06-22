# V2.0 环境分析

## 目标

RepoCheck V2.0 定位为**论文复现环境风险诊断器**。

V1 已完成论文解析、GitHub 仓库搜索、仓库结构分析、README 分析、报告生成、人工指定仓库等能力。

V2.0 第一阶段在 V1 基础上新增**静态环境依赖分析**能力，目标是：当用户完成基础分析并获得报告后，可以手动触发环境分析，了解复现该论文所需的环境配置风险和依赖清单。

## 当前阶段（第一阶段）

当前阶段**不做**：

- 不运行代码
- 不 `git clone`
- 不 `pip install`
- 不下载数据集
- 不下载模型权重
- 不进入 Docker 沙箱
- 不接入 LLM
- 不重构 V1
- 不把环境分析自动嵌入任务创建主流程

当前阶段**只做**：

1. 手动触发环境分析 → `POST /api/tasks/{taskId}/environment/rebuild`
2. 后端调用 ai-service → `POST /api/environment/analyze`
3. ai-service 通过 GitHub API 读取依赖文件
4. 解析 requirements.txt / environment.yml / pyproject.toml / Dockerfile
5. 识别 Python 版本、CUDA 版本、主深度学习框架
6. 生成环境风险分析报告
7. 后端保存结果到数据库
8. 提供查询接口

## 分析的文件

通过 GitHub Contents API 读取以下文件（不 clone、不下载 zip）：

| 文件 | 解析工具 | 提取内容 |
|------|---------|---------|
| requirements.txt | `requirements_parser.py` | pip 包名和版本声明 |
| requirements-dev.txt | 同上 | dev 依赖 |
| environment.yml | `environment_yml_parser.py` | Python/CUDA 版本、conda+pip 依赖 |
| pyproject.toml | `pyproject_parser.py` | project.dependencies、requires-python、Poetry deps |
| setup.py | 同上（正则后备） | install_requires（通过正则提取） |
| Dockerfile | `dockerfile_parser.py` | 基础镜像、CUDA 版本、apt/pip/conda 安装包 |

## 输出字段

### 依赖清单（每项）

```json
{
  "fileType": "requirements | environment_yml | pyproject | dockerfile",
  "filePath": "requirements.txt",
  "packageName": "torch",
  "versionSpec": "==2.1.0",
  "source": "pip | conda | apt | docker",
  "riskLevel": "LOW | MEDIUM | HIGH",
  "riskReason": "解释为什么有这个风险等级"
}
```

### 环境分析汇总

```json
{
  "pythonVersion": "3.10",
  "cudaVersion": "11.8",
  "mainFramework": "PyTorch",
  "frameworkVersion": "2.1.0",
  "requiresGpu": true,
  "hasDocker": true,
  "dockerBaseImage": "nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04",
  "dependencyRiskScore": 65,
  "cudaRiskScore": 50,
  "dockerReadinessScore": 80,
  "environmentScore": 70,
  "riskLevel": "MEDIUM",
  "riskSummary": "...",
  "installAdvice": "..."
}
```

### 评分说明

| 评分项 | 范围 | 含义 |
|--------|------|------|
| dependencyRiskScore | 0-100 | 越高依赖安装风险越高 |
| cudaRiskScore | 0-100 | 越高 CUDA 配置难度越大 |
| dockerReadinessScore | 0-100 | 越高 Docker 支持越好 |
| environmentScore | 0-100 | 综合环境复现难度（越高越容易） |
| riskLevel | LOW/MEDIUM/HIGH | 综合风险等级 |

## 风险评估规则

### 框架识别

- PyTorch: torch / torchvision / torchaudio
- TensorFlow: tensorflow / tensorflow-gpu
- JAX: jax / jaxlib
- PaddlePaddle: paddlepaddle
- MindSpore: mindspore

### GPU 线索

- CUDA 直接依赖: cuda, cudatoolkit, cudnn, nccl
- Docker 基础镜像: nvidia/cuda:xx.x
- GPU 包: bitsandbytes, xformers, flash-attn, deepspeed, cupy
- 框架 GPU 版本: tensorflow-gpu, paddlepaddle-gpu

### 高风险依赖

深度学习框架、CUDA 工具包、编译型依赖（opencv-python、detectron2、mmcv）等可能引起版本冲突和环境问题。

## 已知限制

1. **不递归解析依赖**：-r other.txt、--extra-index-url 等引用不会被展开，风险提示中标注
2. **不分析 setup.py**：setup.py 通过正则提取，可能遗漏复杂的 install_requires
3. **不分析 Pipfile/poetry.lock**：当前不支持
4. **不检测操作系统依赖**：apt-get 安装的包会被列出但不评估版本兼容性
5. **不验证版本冲突**：只做静态文本解析，不运行 pip check 或依赖解析
6. **不跟踪间接依赖**：只分析直接声明的包，不分析传递依赖
7. **GitHub API 限流**：未配置 GITHUB_TOKEN 时每小时 60 次请求
8. **环境评分是静态预估**：基于规则而非实际运行结果，仅供初步参考
