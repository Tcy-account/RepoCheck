# LangGraph 工作流说明

## 工作流概览

```
START
  │
  ▼
┌──────────────┐
│ ParsePaper   │  解析 arXiv 论文信息
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  FindRepo    │  搜索代码仓库
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ SelectBestRepo   │  选择最佳匹配仓库
└──────┬───────────┘
       │
       ▼
┌─────────────────────────┐
│ AnalyzeRepoStructure    │  分析仓库文件结构
└──────┬──────────────────┘
       │
       ▼
┌──────────────┐
│ AnalyzeDocs  │  分析 README 等文档
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  ScoreRepo   │  综合评分
└──────┬───────┘
       │
       ▼
┌───────────────┐
│ GenerateReport│  生成报告
└──────┬────────┘
       │
       ▼
      END
```

## 节点详解

### 1. ParsePaperNode

**职责**: 解析 arXiv 论文链接，提取论文元信息

**输入**: `paperUrl` (arXiv 链接)

**处理逻辑**:
- 从 URL 提取 arXiv ID
- 调用 arXiv API 获取论文元信息
- V1: 若 API 不可用，使用 mock 数据

**输出**:
- `arxivId`, `title`, `authors`, `abstractText`, `publishedAt`

### 2. FindRepoNode

**职责**: 根据论文信息搜索对应的代码仓库

**输入**: 论文标题、arXiv ID、摘要

**搜索策略** (按优先级):
1. 在论文 arXiv 页面查找代码链接
2. GitHub 搜索 (按论文标题)
3. GitLab 搜索

**输出**:
- 候选仓库列表 (platform, repoUrl, repoName, owner, stars, forks)

### 3. SelectBestRepoNode

**职责**: 从候选仓库中选择最可能的官方实现

**选择策略**:
- 按 `github_tool.calculate_repo_confidence()` 计算的置信度排序
- 置信度综合考虑 arXiv ID 匹配、标题关键词匹配、Star 数、更新时间
- 置信度最高的仓库为最终选择

**输出**:
- 最佳仓库信息 + confidence + confidenceReason

### 4. AnalyzeRepoStructureNode

**职责**: 通过 GitHub API 获取仓库文件树，检查关键文件

**检查项**:

| 类别 | 检查文件 |
|------|---------|
| 文档 | README.md, LICENSE |
| 依赖 | requirements.txt, environment.yml, pyproject.toml, setup.py, Dockerfile |
| 训练 | train.py, scripts/train.sh |
| 推理 | demo.py, infer.py, predict.py |

**V1 限制**: 不 git clone，仅通过 API 获取文件列表

**输出**: `file_presence` (9 项布尔检查) + `file_matches` (匹配文件明细，按 8 个类别分组)

### 5. AnalyzeDocsNode

**职责**: 分析 README 内容，判断是否有各部分说明

**分析维度**:
- 安装说明
- 训练说明
- 推理说明
- 数据集说明
- 模型权重说明

**分析方式**: 
- V1: 关键词匹配规则分析，无需 LLM
- 8 组关键词分别检测：安装/训练/推理/数据集/权重/引用/示例命令/README 长度
- 输出 `readme_analysis` 字典 (7 项是/否 + `readmeLength`)
- 联动 `file_presence`：README 中检测到数据集/权重说明时自动补充
- 计算 `readme_quality_score`（基础分 20 + 每项加分，最高 100）

### 6. ScoreRepoNode

**职责**: 综合前面所有分析结果，生成评分

**评分维度**:
- `reproducibilityScore` (0-100): 复现难度
  - 文件完整性 + 文档完整性 + 依赖复杂度
- `completenessScore` (0-100): 仓库完整度
  - 关键文件覆盖率
- `environmentScore` (0-100): 环境复杂度
  - requirements.txt 有则高分，Dockerfile 有则加分
- `riskLevel`: LOW / MEDIUM / HIGH
  - 基于以上三项综合判定

### 7. GenerateReportNode

**职责**: 生成最终的中文分析报告

**报告内容**:
- 论文核心方法总结
- 主要创新点
- 复现步骤建议
- 潜在风险提示
- 最终建议

**V1 实现**: 基于模板 + 分析数据生成结构化报告 (LLM 调用预留)

## State 管理

LangGraph 使用 `GraphState` 在节点间传递数据:

```python
class GraphState(TypedDict):
    task_id: int
    paper_url: str
    error: Optional[str]
    # paper info
    arxiv_id: str
    title: str
    authors: str
    abstract_text: str
    published_at: str
    # repo info
    candidate_repos: List[dict]
    selected_repo: Optional[dict]
    # analysis
    repo_structure: dict
    file_presence: dict               # 9 项布尔检查结果
    file_matches: dict                # 匹配文件明细，按类别分组
    readme: dict                      # README 原文 (path, size, excerpt)
    readme_analysis: dict             # README 章节分析 (7 项是/否 + 长度)
    readme_quality_score: int         # README 质量评分 (0-100)
    docs_analysis: dict               # (兼容字段)
    # scores
    reproducibility_score: int
    completeness_score: int
    environment_score: int
    dependency_complexity_score: int  # 依赖复杂度评分
    structure_completeness_score: int # 结构完整度评分
    risk_level: str
    # report
    summary: str
    method_summary: str
    innovation_summary: str
    reproduce_steps: str
    risk_tips: str
    final_advice: str
```

## 错误处理

每个节点都可以设置 `state["error"]`，工作流会在发现错误后跳过后续节点，直接返回错误信息。
