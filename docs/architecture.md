# RepoCheck 总体架构

## 系统概述

RepoCheck 是一个 **前后端分离 + AI 服务拆分的 monorepo 多服务项目**。用户输入 arXiv 论文链接后，系统自动解析论文信息，寻找对应 GitHub/GitLab 代码仓库，对仓库进行静态分析，并生成复现可行性报告。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                              │
│                    (Vue3 + Element Plus)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (Axios)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     SpringBoot 后端                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐  │
│  │ auth │ │ user │ │ task │ │paper │ │ repo │ │ report │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └────────┘  │
│  ┌──────────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────────┐  │
│  │ analysis │ │  ai  │ │ file │ │ system │ │  admin   │  │
│  └──────────┘ └──────┘ └──────┘ └────────┘ └──────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         数据持久化层 (MyBatis Plus / 11 个模块)        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (RestTemplate)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI AI 服务                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    LangGraph 工作流                    │   │
│  │  ParsePaper → FindRepo → SelectBestRepo               │   │
│  │       → AnalyzeRepoStructure → AnalyzeDocs            │   │
│  │              → ScoreRepo → GenerateReport             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ arXiv工具 │ │GitHub工具│ │GitLab工具│ │ LLM 工具  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      基础设施                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  MySQL   │  │  Redis   │  │  MinIO   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 模块职责

### 前端 (frontend/)

- **技术栈**: Vue3 + Vite + TypeScript + Pinia + Axios + Element Plus
- **API 模块**: auth / user / task / paper / repo / analysis / report / file (8 个模块)
- **页面**: 首页 / 任务列表 / 报告详情 / 个人中心
- **职责**: 用户交互界面，任务提交、列表查看、报告展示

### 后端 (backend/)

- **技术栈**: SpringBoot 3.x + MyBatis Plus + Sa-Token
- **分包策略**: 按业务域分包 `modules/`，内部再分 controller / service / entity / mapper / dto / vo
- **业务模块**: auth / user / task / paper / repo / analysis / report / ai / file / system / admin (11 个模块)

| 模块 | 职责 |
|------|------|
| `auth` | 用户注册、登录、登出、当前用户信息 |
| `user` | 用户信息修改、密码修改 |
| `task` | 任务 CRUD、状态管理、时间线、重试/取消/删除，含 `TaskTimelineService` 统一状态写入 |
| `paper` | 论文信息查询和刷新 |
| `repo` | 仓库信息、候选仓库、人工指定仓库、重新搜索 |
| `analysis` | 仓库静态分析结果、文件列表、README 内容 |
| `report` | 报告详情、评分摘要、报告重新生成、Markdown/PDF 导出 |
| `ai` | 调用 FastAPI 分析服务，保存分析结果 |
| `file` | 文件上传/下载/删除 (MinIO 占位) |
| `system` | 健康检查、AI 服务状态、系统配置 |
| `admin` | 管理员接口 (V1 预留，返回 501) |

### AI 服务 (ai-service/)

- **技术栈**: FastAPI + LangChain + LangGraph
- **职责**:
  - 解析 arXiv 论文信息
  - 搜索对应代码仓库
  - 静态分析仓库结构
  - 生成复现可行性报告

### 基础设施

| 服务 | 用途 |
|------|------|
| MySQL | 主数据存储 |
| Redis | 缓存 / Session (Sa-Token) |
| MinIO | 文件存储 (V1 占位) |

## 服务调用链路

```
用户输入 arXiv 链接
    │
    ▼
Vue3 前端 ──POST /api/tasks──▶ SpringBoot 后端 (TaskController)
                                    │
                          创建任务 (PENDING)
                          写入 task_timeline
                          返回 taskId 给前端
                                    │
                          异步调用 analyzeTask() (AiServiceImpl)
                          状态: PARSING_PAPER
                                    │
                          调用 POST /api/analyze (AI Service)
                                    │
                                    ▼
                              FastAPI AI 服务
                                    │
                          执行 LangGraph 7 节点工作流:
                            ParsePaper → FindRepo → SelectBestRepo
                            → AnalyzeRepoStructure → AnalyzeDocs
                            → ScoreRepo → GenerateReport
                                    │
                          返回结构化分析结果
                           (含 readmeAnalysis, fileMatches)
                                    │
                                    ▼
                         SpringBoot 后端 (AiServiceImpl)
                    ┌──检查 CANCELLED 状态防覆盖
                    ├──幂等 upsert paper_info/repo_info/repo_analysis/report
                    ├──序列化 fileMatches → file_matches_json
                    ├──序列化 readmeAnalysis → readme_analysis_json
                    ├──更新 paper_task 标题
                    └──状态 → SUCCESS + finishTime + timeline
                                    │
                                    ▼
Vue3 前端 (轮询 2s) ──GET /api/tasks/{id}/status──▶ 获取进度
Vue3 前端 ──GET /api/reports/{taskId}──▶ 展示报告 (含 README 分析卡片)
Vue3 前端 ──GET /api/tasks/{taskId}/analysis/readme──▶ README 分析详情
Vue3 前端 ──GET /api/reports/{taskId}/export/markdown──▶ 下载 Markdown
```

### 人工指定仓库流程

```
前端输入 GitHub 链接
    │
    ▼
PUT /api/tasks/{taskId}/repo  → 覆盖 repo_info + repo_candidate
    │
POST /api/tasks/{taskId}/analysis/rebuild  → 重新分析
    │
    ▼
AiServiceImpl.analyzeStructure() → POST /api/repo/analyze-structure
    │
AiServiceImpl.saveOrUpdateResults() → 幂等 upsert repo_info/repo_analysis/report
    │
状态: SUCCESS + timeline
    │
    ▼
前端刷新报告
```

### 失败重试流程

```
前端点击"重试"
    │
POST /api/tasks/{taskId}/retry
    │
状态: PENDING + 清除错误信息
    │
triggerAnalysis() → analyzeTask() → 尝试 AI 调用
    │
成功 → SUCCESS | 失败 → FAILED + errorMessage
```

### 取消防覆盖机制

```
用户取消任务 → TaskTimelineService.updateTaskStatus(CANCELLED)
    │
AI 分析完成返回 → analyzeTask()
    │
paperTaskMapper.selectById(taskId)
    │
status == CANCELLED ? → return (丢弃结果，不覆盖状态)
                   : → 正常保存 (SUCCESS)
```

## 数据流

```
PaperTask ────1:1───▶ PaperInfo
PaperTask ────1:1───▶ RepoInfo
PaperTask ────1:1───▶ RepoAnalysis (含 file_matches_json, readme_analysis_json)
PaperTask ────1:1───▶ Report
PaperTask ────1:N───▶ RepoCandidate
PaperTask ────1:N───▶ TaskTimeline
User ────────1:N───▶ PaperTask
FileInfo ────N:1──▶ PaperTask (可选关联)
```

## 相关文档

| 文档 | 内容 |
|------|------|
| [api-design-v1.md](api-design-v1.md) | V1.0 完整接口设计文档 (40+ 接口) |
| [api.md](api.md) | 前后端 ↔ AI 服务接口快速参考 |
| [workflow.md](workflow.md) | LangGraph 7 节点工作流说明 |
| [database.md](database.md) | 数据库表设计 |
| [roadmap.md](roadmap.md) | V1.0 ~ V4.0 演进路线 |
