# RepoCheck V1.0 接口设计文档

> 版本：V1.0  
> 更新日期：2025-01  
> 状态：设计阶段，尚未全部实现  
> 范围：前端 ↔ 后端接口 + 后端 ↔ AI 服务内部接口

---

## 一、项目架构说明

### 1.1 整体定位

RepoCheck 是一个 **前后端分离 + AI 服务拆分的 monorepo 多服务项目**，不是传统 Maven 多模块单体项目。

```
Vue3 frontend  ──HTTP──▶  SpringBoot backend  ──HTTP──▶  FastAPI ai-service
  (独立部署)                (单体后端，独立部署)            (独立 AI 分析服务)
                                 │
                                 ├── MySQL
                                 ├── Redis
                                 └── MinIO (V1 占位)
```

### 1.2 各服务说明

| 服务 | 技术栈 | 端口 | 角色 |
|------|--------|------|------|
| `frontend/` | Vue3 + Vite + TypeScript + Element Plus | 3000 | 用户交互界面 |
| `backend/` | SpringBoot 3.x + MyBatis Plus + Sa-Token | 8080 | 业务编排、数据持久化、调用 AI 服务 |
| `ai-service/` | FastAPI + LangChain + LangGraph | 8000 | 独立 AI 分析服务，不可由前端直接访问 |

- **backend** 本身是单体后端，承载用户管理、任务管理、报告管理等所有业务模块。
- **ai-service** 是独立拆分的 AI 分析服务，仅由 backend 通过 HTTP 调用，不对前端暴露。
- **frontend / backend / ai-service** 三者可以独立启动和独立部署。V1 阶段直接本地多进程启动即可。

---

## 二、统一规范

### 2.1 Base URL

| 环境 | 前端 → 后端 | 后端 → AI 服务 |
|------|------------|---------------|
| 开发 | `http://localhost:8080` | `http://localhost:8000` |
| 生产 | 按实际部署配置 | 按实际部署配置 |

### 2.2 统一响应结构 `Result<T>`

所有后端接口均返回以下 JSON 结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `int` | 状态码，`200` 表示成功 |
| `message` | `string` | 提示信息，成功时为 `"success"` |
| `data` | `T`（泛型） | 业务数据，可以是对象、数组、`null` |

### 2.3 分页响应 `PageResult<T>`

列表接口在 `data` 中返回分页结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [],
    "total": 0,
    "page": 1,
    "size": 10
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `records` | `array` | 当前页记录列表 |
| `total` | `long` | 总记录数 |
| `page` | `int` | 当前页码（从 1 开始） |
| `size` | `int` | 每页条数 |

### 2.4 错误码建议

| code | 说明 |
|------|------|
| `200` | 成功 |
| `400` | 请求参数错误 |
| `401` | 未登录 / Token 失效 |
| `403` | 无权限 |
| `404` | 资源不存在 |
| `409` | 业务冲突（如重复操作） |
| `500` | 服务器内部错误 |

### 2.5 时间格式

所有时间字段统一使用 ISO 8601 格式字符串：

```
2025-01-15T10:30:00
```

纯日期字段使用 `YYYY-MM-DD`：

```
2025-01-15
```

### 2.6 枚举格式

枚举值在上层（JSON）统一使用大写字符串，如 `"PENDING"`、`"SUCCESS"`。  
前后端 / AI 服务保持一致，数据库存储同名字符串。

### 2.7 鉴权方式

V1 阶段使用 **Sa-Token** 进行登录鉴权。  
前端在请求头中携带 `Authorization` 字段（值由登录接口返回）。  
V1 初期可暂时放开 `/api/tasks/**` 和 `/api/reports/**` 的鉴权拦截。

---

## 三、用户与认证接口

### 3.1 用户注册

```
POST /api/auth/register
```

**请求参数：**

```json
{
  "username": "string，必填，3-50 字符",
  "password": "string，必填，6-100 字符",
  "email": "string，选填"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "userId": 1,
    "username": "zhangsan"
  }
}
```

**备注：** 密码在后端使用 BCrypt 加密存储，不可明文返回。

---

### 3.2 用户登录

```
POST /api/auth/login
```

**请求参数：**

```json
{
  "username": "string，必填",
  "password": "string，必填"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "sa-token-value",
    "userId": 1,
    "username": "zhangsan"
  }
}
```

**备注：** 登录成功后返回 Sa-Token，前端存储到 localStorage，后续请求在 Header 中携带 `Authorization: <token>`。

---

### 3.3 用户登出

```
POST /api/auth/logout
```

**请求头：** `Authorization: <token>`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 3.4 获取当前用户信息

```
GET /api/auth/me
```

**请求头：** `Authorization: <token>`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "createTime": "2025-01-01T10:00:00"
  }
}
```

---

### 3.5 修改用户信息

```
PUT /api/users/me
```

**请求头：** `Authorization: <token>`

**请求参数：**

```json
{
  "email": "string，选填"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 3.6 修改密码

```
PUT /api/users/me/password
```

**请求头：** `Authorization: <token>`

**请求参数：**

```json
{
  "oldPassword": "string，必填",
  "newPassword": "string，必填，6-100 字符"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 四、论文检测任务接口

### 4.1 任务状态枚举

| 值 | 含义 |
|----|------|
| `PENDING` | 等待处理 |
| `PARSING_PAPER` | 正在解析论文信息 |
| `SEARCHING_REPO` | 正在搜索代码仓库 |
| `ANALYZING_REPO` | 正在分析仓库结构 |
| `GENERATING_REPORT` | 正在生成分析报告 |
| `SUCCESS` | 任务完成 |
| `FAILED` | 任务失败 |
| `CANCELLED` | 任务已取消 |

---

### 4.2 创建检测任务

```
POST /api/tasks
```

**请求参数：**

```json
{
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `paperUrl` | `string` | arXiv 论文链接，必填 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1
  }
}
```

**备注：** 创建后立即返回 `taskId`，后台异步执行分析流程。前端可轮询 `/api/tasks/{taskId}/status` 获取进度。

---

### 4.3 获取任务列表

```
GET /api/tasks
```

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | `int` | 否 | `1` | 页码 |
| `size` | `int` | 否 | `10` | 每页条数（最大 50） |
| `status` | `string` | 否 | - | 按状态筛选，如 `SUCCESS` |
| `keyword` | `string` | 否 | - | 按论文标题模糊搜索 |
| `startTime` | `string` | 否 | - | 创建时间起始，ISO 8601 |
| `endTime` | `string` | 否 | - | 创建时间截止，ISO 8601 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "paperTitle": "Sample Paper Title",
        "paperUrl": "https://arxiv.org/abs/2501.xxxxx",
        "status": "SUCCESS",
        "createTime": "2025-01-15T10:00:00",
        "finishTime": "2025-01-15T10:05:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
}
```

---

### 4.4 获取任务详情

```
GET /api/tasks/{taskId}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `taskId` | `long` | 任务 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "userId": 1,
    "paperUrl": "https://arxiv.org/abs/2501.xxxxx",
    "paperTitle": "Sample Paper Title",
    "status": "SUCCESS",
    "errorMessage": null,
    "createTime": "2025-01-15T10:00:00",
    "updateTime": "2025-01-15T10:05:00",
    "finishTime": "2025-01-15T10:05:00"
  }
}
```

---

### 4.5 获取任务状态（轻量轮询）

```
GET /api/tasks/{taskId}/status
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `taskId` | `long` | 任务 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1,
    "status": "ANALYZING_REPO",
    "errorMessage": null
  }
}
```

**备注：** 设计为轻量接口，前端可 2~3 秒轮询一次。当 `status` 变为 `SUCCESS` 或 `FAILED` 时停止轮询。

---

### 4.6 获取任务时间线

```
GET /api/tasks/{taskId}/timeline
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1,
    "timeline": [
      { "status": "PENDING",      "time": "2025-01-15T10:00:00" },
      { "status": "PARSING_PAPER", "time": "2025-01-15T10:00:01" },
      { "status": "SEARCHING_REPO","time": "2025-01-15T10:00:02" },
      { "status": "SUCCESS",       "time": "2025-01-15T10:05:00" }
    ]
  }
}
```

**备注：** 数据来源于 `task_timeline` 表，在 `TaskTimelineService` 中统一维护。

---

### 4.7 重试任务

```
POST /api/tasks/{taskId}/retry
```

**说明：** 仅当任务状态为 `FAILED` 或 `CANCELLED` 时可调用，将状态重置为 `PENDING` 并重新触发分析。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 4.8 取消任务

```
POST /api/tasks/{taskId}/cancel
```

**说明：** 仅当任务状态非终态（非 SUCCESS/FAILED/CANCELLED）时可调用，将状态置为 `CANCELLED`。终态任务调用返回业务错误。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 4.9 删除任务

```
DELETE /api/tasks/{taskId}
```

**说明：** 删除任务及其关联的论文信息、仓库信息、分析结果、报告。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 五、论文信息接口

### 5.1 获取论文信息

```
GET /api/tasks/{taskId}/paper
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "arxivId": "2501.xxxxx",
    "title": "Sample Paper Title",
    "authors": "Author One, Author Two",
    "abstractText": "This paper proposes...",
    "publishedAt": "2025-01-15",
    "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `arxivId` | `string` | arXiv ID |
| `title` | `string` | 论文标题 |
| `authors` | `string` | 作者列表（逗号分隔） |
| `abstractText` | `string` | 论文摘要全文 |
| `publishedAt` | `string`（日期） | 发布日期 |
| `paperUrl` | `string` | 论文链接 |

---

### 5.2 刷新论文信息

```
POST /api/tasks/{taskId}/paper/refresh
```

**说明：** 重新从 arXiv API 拉取论文元信息并更新数据库。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 六、仓库信息接口

### 6.1 获取仓库信息

```
GET /api/tasks/{taskId}/repo
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "platform": "GitHub",
    "repoUrl": "https://github.com/user/repo",
    "repoName": "repo",
    "owner": "user",
    "stars": 128,
    "forks": 32,
    "defaultBranch": "main",
    "lastUpdatedAt": "2025-01-10T00:00:00",
    "confidence": 0.95,
    "confidenceReason": "Found on paper page"
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `platform` | `string` | 平台：`GitHub` / `GitLab` |
| `repoUrl` | `string` | 仓库完整 URL |
| `repoName` | `string` | 仓库名称 |
| `owner` | `string` | 仓库所有者 |
| `stars` | `int` | Star 数量 |
| `forks` | `int` | Fork 数量 |
| `defaultBranch` | `string` | 默认分支名 |
| `lastUpdatedAt` | `string`（日期时间） | 仓库最后更新时间 |
| `confidence` | `float` | 匹配置信度，范围 0.00 ~ 1.00 |
| `confidenceReason` | `string` | 置信度判断理由 |

---

### 6.2 获取候选仓库列表

```
GET /api/tasks/{taskId}/repo/candidates
```

**说明：** 返回 AI 搜索到的所有候选仓库，包括未被选为最佳的仓库。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "selectedIndex": 0,
    "candidates": [
      {
        "platform": "GitHub",
        "repoUrl": "https://github.com/user/repo",
        "repoName": "repo",
        "owner": "user",
        "stars": 128,
        "forks": 32,
        "defaultBranch": "main",
        "lastUpdatedAt": "2025-01-10T00:00:00",
        "confidence": 0.95,
        "confidenceReason": "Found on paper page"
      }
    ]
  }
}
```

---

### 6.3 人工指定仓库（重要）

```
PUT /api/tasks/{taskId}/repo
```

**说明：** V1 重点接口。自动找仓库可能误判，因此必须预留"人工指定仓库"接口。用户可在前端手动输入正确的仓库 URL，覆盖 AI 自动选择的结果。

**请求参数：**

```json
{
  "repoUrl": "https://github.com/correct-user/correct-repo",
  "platform": "GitHub"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `repoUrl` | `string` | 仓库 URL，必填 |
| `platform` | `string` | 平台，必填，`GitHub` / `GitLab` |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

**备注：** 人工指定仓库后，后端应重新触发仓库结构分析和后续流程。

---

### 6.4 重新搜索仓库

```
POST /api/tasks/{taskId}/repo/search
```

**说明：** 强制重新搜索代码仓库（丢弃当前已选仓库，返回候选列表）。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 七、仓库分析接口

### 7.1 获取仓库分析结果

```
GET /api/tasks/{taskId}/analysis
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "hasReadme": true,
    "hasRequirements": true,
    "hasEnvironmentYml": false,
    "hasDockerfile": true,
    "hasLicense": true,
    "hasTrainCode": true,
    "hasInferenceCode": true,
    "hasDatasetDoc": false,
    "hasWeightDoc": false,
    "readmeQualityScore": 80,
    "dependencyComplexityScore": 60,
    "structureCompletenessScore": 75,
    "fileMatches": {
      "readmeFiles": ["README.md"],
      "dependencyFiles": ["requirements.txt"]
    },
    "readmeAnalysis": {
      "hasInstallSection": true,
      "hasTrainSection": true,
      "hasInferenceSection": false,
      "hasDatasetSection": true,
      "hasWeightSection": false,
      "hasCitationSection": true,
      "hasExampleCommands": true,
      "readmeLength": 4567
    }
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `hasReadme` | `boolean` | 仓库是否有 README.md |
| `hasRequirements` | `boolean` | 是否有 requirements.txt / pyproject.toml / setup.py |
| `hasEnvironmentYml` | `boolean` | 是否有 environment.yml |
| `hasDockerfile` | `boolean` | 是否有 Dockerfile |
| `hasLicense` | `boolean` | 是否有 LICENSE 文件 |
| `hasTrainCode` | `boolean` | 是否包含训练代码（train.py 等） |
| `hasInferenceCode` | `boolean` | 是否包含推理代码（infer.py / demo.py / predict.py） |
| `hasDatasetDoc` | `boolean` | 是否有数据集下载说明 |
| `hasWeightDoc` | `boolean` | 是否有模型权重下载说明 |
| `readmeQualityScore` | `int` | README 质量评分，0-100 |
| `dependencyComplexityScore` | `int` | 依赖复杂度评分，0-100 |
| `structureCompletenessScore` | `int` | 结构完整度评分，0-100 |
| `fileMatches` | `object` | 匹配文件明细，按类别分组为字符串数组 (V5 新增) |
| `readmeAnalysis` | `object` | README 章节分析结果 (V6 新增)，包含 7 项是/否检查 + README 长度 |

---

### 7.2 重建分析

```
POST /api/tasks/{taskId}/analysis/rebuild
```

**说明：** 强制重新对仓库执行静态分析并更新结果。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 7.3 获取仓库文件列表

```
GET /api/tasks/{taskId}/analysis/files
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalCount": 45,
    "files": [
      "README.md",
      "requirements.txt",
      "Dockerfile",
      "LICENSE",
      "train.py",
      "infer.py",
      "src/model.py"
    ]
  }
}
```

---

### 7.4 获取 README 分析

```
GET /api/tasks/{taskId}/analysis/readme
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "hasInstallSection": true,
    "hasTrainSection": true,
    "hasInferenceSection": false,
    "hasDatasetSection": true,
    "hasWeightSection": false,
    "hasCitationSection": true,
    "hasExampleCommands": true,
    "readmeLength": 4567,
    "readmeQualityScore": 80
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `hasInstallSection` | `boolean` | README 是否包含安装说明 |
| `hasTrainSection` | `boolean` | README 是否包含训练说明 |
| `hasInferenceSection` | `boolean` | README 是否包含推理说明 |
| `hasDatasetSection` | `boolean` | README 是否包含数据集说明 |
| `hasWeightSection` | `boolean` | README 是否包含模型权重说明 |
| `hasCitationSection` | `boolean` | README 是否包含引用说明 |
| `hasExampleCommands` | `boolean` | README 是否包含示例命令 |
| `readmeLength` | `int` | README 文件长度（字符数） |
| `readmeQualityScore` | `int` | README 质量评分，0-100 |

**备注：** 基于关键词规则分析 README 各章节完整性，无需 LLM。若 README 不存在则返回全 false、readmeLength=0。

---

## 八、报告接口

### 8.1 风险等级枚举

| 值 | 含义 |
|----|------|
| `LOW` | 低风险 — 代码完整、文档齐全、环境清晰 |
| `MEDIUM` | 中等风险 — 存在部分缺失但可接受 |
| `HIGH` | 高风险 — 关键文件或文档缺失严重 |

---

### 8.2 获取完整报告

```
GET /api/reports/{taskId}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "paperInfo": {
      "arxivId": "2501.xxxxx",
      "title": "Sample Paper Title",
      "authors": "Author One, Author Two",
      "abstractText": "This paper proposes...",
      "publishedAt": "2025-01-15",
      "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
    },
    "repoInfo": {
      "platform": "GitHub",
      "repoUrl": "https://github.com/user/repo",
      "repoName": "repo",
      "owner": "user",
      "stars": 128,
      "forks": 32,
      "defaultBranch": "main",
      "lastUpdatedAt": "2025-01-10T00:00:00",
      "confidence": 0.95,
      "confidenceReason": "Found on paper page"
    },
    "repoAnalysis": {
      "hasReadme": true,
      "hasRequirements": true,
      "hasEnvironmentYml": false,
      "hasDockerfile": true,
      "hasLicense": true,
      "hasTrainCode": true,
      "hasInferenceCode": true,
      "hasDatasetDoc": false,
      "hasWeightDoc": false,
      "readmeQualityScore": 80,
      "dependencyComplexityScore": 60,
      "structureCompletenessScore": 75,
      "fileMatches": {
        "readmeFiles": ["README.md"],
        "dependencyFiles": ["requirements.txt", "setup.py"]
      },
      "readmeAnalysis": {
        "hasInstallSection": true,
        "hasTrainSection": true,
        "hasInferenceSection": false,
        "hasDatasetSection": true,
        "hasWeightSection": false,
        "hasCitationSection": true,
        "hasExampleCommands": true,
        "readmeLength": 4567
      }
    },
    "report": {
      "reproducibilityScore": 70,
      "completenessScore": 75,
      "environmentScore": 60,
      "riskLevel": "MEDIUM",
      "summary": "该论文提供了较为完整的代码仓库...",
      "methodSummary": "本文提出了...",
      "innovationSummary": "主要创新点包括...",
      "reproduceSteps": "1. 安装依赖\n2. 下载数据\n...",
      "riskTips": "缺少数据集说明和模型权重说明。",
      "finalAdvice": "建议优先使用 Docker 环境复现，注意数据集获取方式。"
    }
  }
}
```

**report 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `reproducibilityScore` | `int` | 复现难度评分，0-100 |
| `completenessScore` | `int` | 仓库完整度评分，0-100 |
| `environmentScore` | `int` | 环境复杂度评分，0-100 |
| `riskLevel` | `string` | 风险等级：`LOW` / `MEDIUM` / `HIGH` |
| `summary` | `string` | AI 总结报告 |
| `methodSummary` | `string` | 论文核心方法总结 |
| `innovationSummary` | `string` | 主要创新点 |
| `reproduceSteps` | `string` | 复现步骤建议 |
| `riskTips` | `string` | 风险提示 |
| `finalAdvice` | `string` | 最终建议（V1 新增字段） |

**备注：** `finalAdvice` 已实现，后端 `Report` 实体、数据库 `report` 表及 AI 服务响应模型均已包含该字段。

---

### 8.3 重新生成报告

```
POST /api/reports/{taskId}/regenerate
```

**说明：** 基于已有分析数据重新调用 LLM 生成报告，不重新分析仓库。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 8.4 获取评分摘要

```
GET /api/reports/{taskId}/scores
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reproducibilityScore": 70,
    "completenessScore": 75,
    "environmentScore": 60,
    "riskLevel": "MEDIUM"
  }
}
```

---

### 8.5 导出 Markdown

```
GET /api/reports/{taskId}/export/markdown
```

**响应：** 返回 Markdown 文本（`Content-Type: text/markdown`），浏览器触发下载。

**备注：** 后端通过 `MarkdownReportBuilder` 工具类生成 Markdown 字符串直接返回，浏览器触发下载。V2 可存储到 MinIO 后返回下载链接。

---

### 8.6 导出 PDF（V1 预留）

```
GET /api/reports/{taskId}/export/pdf
```

**响应：** 返回 PDF 文件流（`Content-Type: application/pdf`）。

**备注：** V1 标记为预留接口，返回 `501 Not Implemented` 即可。V2 实现。

---

## 九、文件接口（MinIO 占位）

V1 阶段文件接口作为 MinIO 占位，用于后续存储报告 PDF、Markdown、用户上传论文 PDF、分析日志等。  
V1 可不实现存储逻辑，返回占位响应。

### 9.1 上传文件

```
POST /api/files/upload
Content-Type: multipart/form-data
```

**请求参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | `file` | 上传的文件 |
| `type` | `string` | 文件类型：`REPORT_PDF` / `REPORT_MD` / `PAPER_PDF` / `LOG` |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "fileId": "uuid-string",
    "fileName": "report-1.md",
    "fileSize": 2048
  }
}
```

---

### 9.2 获取文件下载链接

```
GET /api/files/{fileId}/download-url
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "downloadUrl": "http://localhost:9000/repocheck/xxx?sign=...",
    "expireAt": "2025-01-15T11:00:00"
  }
}
```

**备注：** 生产环境 MinIO 应返回带签名的临时下载链接，有效期建议 10 分钟。

---

### 9.3 删除文件

```
DELETE /api/files/{fileId}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 十、系统接口

### 10.1 后端健康检查

```
GET /api/system/health
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "UP",
    "mysql": "UP",
    "redis": "UP",
    "minio": "UP"
  }
}
```

---

### 10.2 AI 服务健康检查

```
GET /api/system/ai-health
```

**说明：** SpringBoot 收到请求后，转发调用 FastAPI 的 `/api/health`，汇总返回。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "aiServiceStatus": "UP",
    "aiServiceUrl": "http://localhost:8000"
  }
}
```

---

### 10.3 获取系统配置

```
GET /api/system/config
```

**说明：** 返回前端需要的公开配置（不包含密钥）。

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "appName": "RepoCheck",
    "version": "1.0.0",
    "maxTaskPerUser": 10,
    "supportedPlatforms": ["arXiv", "GitHub", "GitLab"]
  }
}
```

---

## 十一、AI 服务内部接口

以下接口是 **SpringBoot 后端 → FastAPI AI 服务** 的内部调用接口，**不由前端直接访问**。

Base URL：`http://localhost:8000`

### 11.1 AI 服务健康检查

```
GET /api/health
```

**说明：** 供 SpringBoot 的 `/api/system/ai-health` 调用的上游接口。

**响应示例：**

```json
{
  "status": "ok"
}
```

---

### 11.2 完整分析（V1 必做）

```
POST /api/analyze
```

**说明：** 执行完整的 7 节点 LangGraph 分析流程。V1 最少必须实现此接口。

**请求参数：**

```json
{
  "taskId": 1,
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `taskId` | `int` | 关联任务 ID |
| `paperUrl` | `string` | arXiv 论文链接 |

**响应示例：**

```json
{
  "taskId": 1,
  "paperInfo": {
    "arxivId": "2501.xxxxx",
    "title": "Sample Paper Title",
    "authors": "Author One, Author Two",
    "abstractText": "This paper proposes...",
    "publishedAt": "2025-01-15",
    "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
  },
  "repoInfo": {
    "platform": "GitHub",
    "repoUrl": "https://github.com/user/repo",
    "repoName": "repo",
    "owner": "user",
    "stars": 128,
    "forks": 32,
    "defaultBranch": "main",
    "lastUpdatedAt": "2025-01-10T00:00:00",
    "confidence": 0.95,
    "confidenceReason": "Found on paper page"
  },
  "repoAnalysis": {
    "hasReadme": true,
    "hasRequirements": true,
    "hasEnvironmentYml": false,
    "hasDockerfile": true,
    "hasLicense": true,
    "hasTrainCode": true,
    "hasInferenceCode": true,
    "hasDatasetDoc": false,
    "hasWeightDoc": false,
    "readmeQualityScore": 80,
    "dependencyComplexityScore": 60,
    "structureCompletenessScore": 75
  },
  "report": {
    "reproducibilityScore": 70,
    "completenessScore": 75,
    "environmentScore": 60,
    "riskLevel": "MEDIUM",
    "summary": "该论文提供了较为完整的代码仓库...",
    "methodSummary": "本文提出了...",
    "innovationSummary": "主要创新点包括...",
    "reproduceSteps": "1. 安装依赖\n2. 下载数据\n...",
    "riskTips": "缺少数据集说明和模型权重说明。",
    "finalAdvice": "建议优先使用 Docker 环境复现。"
  }
}
```

---

### 11.3 单步：解析论文（调试接口）

```
POST /api/paper/parse
```

**请求参数：**

```json
{
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

**响应示例：**

```json
{
  "arxivId": "2501.xxxxx",
  "title": "Sample Paper Title",
  "authors": "Author One, Author Two",
  "abstractText": "This paper proposes...",
  "publishedAt": "2025-01-15",
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

**备注：** 调试用，允许单独测试论文解析节点。

---

### 11.4 单步：搜索仓库（调试接口）

```
POST /api/repo/search
```

**请求参数：**

```json
{
  "title": "Sample Paper Title",
  "arxivId": "2501.xxxxx",
  "abstractText": "This paper proposes..."
}
```

**响应示例：**

```json
{
  "candidates": [
    {
      "platform": "GitHub",
      "repoUrl": "https://github.com/user/repo",
      "repoName": "repo",
      "owner": "user",
      "stars": 128,
      "forks": 32,
      "defaultBranch": "main",
      "lastUpdatedAt": "2025-01-10T00:00:00"
    }
  ]
}
```

---

### 11.5 单步：分析仓库结构（调试接口）

```
POST /api/repo/analyze-structure
```

**请求参数：**

```json
{
  "owner": "user",
  "repoName": "repo",
  "defaultBranch": "main"
}
```

**响应示例：**

```json
{
  "totalCount": 10,
  "files": ["README.md", "requirements.txt", "train.py", "infer.py"],
  "analysis": {
    "hasReadme": true,
    "hasRequirements": true,
    "hasEnvironmentYml": false,
    "hasDockerfile": true,
    "hasLicense": true,
    "hasTrainCode": true,
    "hasInferenceCode": true,
    "hasDatasetDoc": false,
    "hasWeightDoc": false
  }
}
```

---

### 11.6 单步：分析文档（调试接口）

```
POST /api/repo/analyze-docs
```

**请求参数：**

```json
{
  "owner": "user",
  "repoName": "repo"
}
```

**响应示例：**

```json
{
  "readmeQualityScore": 80,
  "hasInstallGuide": true,
  "hasTrainGuide": true,
  "hasInferenceGuide": true,
  "hasDatasetDoc": false,
  "hasWeightDoc": false
}
```

---

### 11.7 单步：生成评分（调试接口）

```
POST /api/report/score
```

**请求参数：**

```json
{
  "filePresence": {
    "hasReadme": true,
    "hasRequirements": true,
    "hasDockerfile": true,
    "hasLicense": true,
    "hasTrainCode": true,
    "hasInferenceCode": true
  },
  "docsAnalysis": {
    "hasInstallGuide": true,
    "hasTrainGuide": true,
    "hasInferenceGuide": true,
    "hasDatasetDoc": false,
    "hasWeightDoc": false
  },
  "readmeQualityScore": 80
}
```

**响应示例：**

```json
{
  "reproducibilityScore": 70,
  "completenessScore": 75,
  "environmentScore": 60,
  "riskLevel": "MEDIUM"
}
```

---

### 11.8 单步：生成报告（调试接口）

```
POST /api/report/generate
```

**请求参数：**

```json
{
  "title": "Sample Paper Title",
  "abstractText": "This paper proposes...",
  "analysis": {},
  "riskLevel": "MEDIUM"
}
```

**响应示例：**

```json
{
  "summary": "该论文...",
  "methodSummary": "本文提出了...",
  "innovationSummary": "主要创新点包括...",
  "reproduceSteps": "1. ...",
  "riskTips": "...",
  "finalAdvice": "..."
}
```

---

### 11.9 AI 服务接口汇总

| 方法 | 路径 | V1 优先级 | 说明 |
|------|------|----------|------|
| `POST` | `/api/analyze` | **必做** | 完整分析流程 |
| `GET` | `/api/health` | **必做** | 健康检查 |
| `POST` | `/api/paper/parse` | 调试 | 单独解析论文 |
| `POST` | `/api/repo/search` | 调试 | 单独搜索仓库 |
| `POST` | `/api/repo/analyze-structure` | 调试 | 单独分析结构 |
| `POST` | `/api/repo/analyze-docs` | 调试 | 单独分析文档 |
| `POST` | `/api/report/score` | 调试 | 单独评分 |
| `POST` | `/api/report/generate` | 调试 | 单独生成报告 |

---

## 十二、管理员接口（后续预留）

以下接口标记为 **非 V1 必做**，可在后续版本实现。V1 返回 `501 Not Implemented` 即可。

```
GET   /api/admin/tasks        # 查看全平台任务列表
GET   /api/admin/users        # 查看全平台用户列表
GET   /api/admin/tasks/failed # 查看所有失败任务
GET   /api/admin/logs         # 查看系统日志
GET   /api/admin/ai-usages    # AI 调用次数统计
```

---

## 十三、V1.0 MVP 必做接口清单

以下是 V1.0 必须实现的最小接口集：

| 序号 | 方法 | 路径 | 所属模块 |
|------|------|------|----------|
| 1 | `POST` | `/api/tasks` | 任务管理 |
| 2 | `GET` | `/api/tasks` | 任务管理 |
| 3 | `GET` | `/api/tasks/{taskId}` | 任务管理 |
| 4 | `GET` | `/api/tasks/{taskId}/status` | 任务管理 |
| 5 | `POST` | `/api/tasks/{taskId}/retry` | 任务管理 |
| 6 | `GET` | `/api/reports/{taskId}` | 报告 |
| 7 | `GET` | `/api/system/ai-health` | 系统 |
| 8 | `POST` | `/api/analyze` | AI 服务（内部） |
| 9 | `GET` | `/api/health` | AI 服务（内部） |

**说明：** 以上 9 个接口打通后，即可完成"用户提交 arXiv 链接 → 后端创建任务 → 调用 AI 分析 → 保存报告 → 前端查看报告"的完整闭环。

---

## 十四、团队分工建议

按接口域拆分，各模块可并行开发：

| 模块域 | 接口前缀 | 建议负责 |
|--------|---------|----------|
| 用户认证 | `/api/auth/*` `/api/users/*` | 后端-认证工程师 |
| 任务管理 | `/api/tasks/*` | 后端-任务工程师 |
| 论文信息 | `/api/tasks/{id}/paper/*` | 后端-任务工程师 |
| 仓库信息 | `/api/tasks/{id}/repo/*` | 后端-仓库工程师 |
| 仓库分析 | `/api/tasks/{id}/analysis/*` | 后端-分析工程师 |
| 报告 | `/api/reports/*` | 后端-报告工程师 |
| AI 服务 | `/api/analyze` 等 | AI 工程师（Python） |
| 前端联调 | 全部页面 | 前端工程师 |
| 文件存储 | `/api/files/*` | 后端-基础设施（V1 占位） |
| 系统接口 | `/api/system/*` | 后端-基础设施 |
| 基础设施 | MySQL / Redis / MinIO / Docker | DevOps / 全栈 |

**分工原则：**

1. AI 服务工程师优先完成 `POST /api/analyze`，保证后端联调有数据源。
2. 后端任务工程师优先完成 `POST /api/tasks` 和 `GET /api/tasks/{taskId}/status`，打通创建和轮询。
3. 后端报告工程师和前端可并行：后端先返回 mock 报告，前端据此调 UI。
4. 基础设施先启动 `docker-compose up -d` 并执行 `init.sql`，所有人依赖同一套数据库。
