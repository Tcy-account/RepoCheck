# API 接口文档 (速查)

> **完整接口设计请查看 [api-design-v1.md](api-design-v1.md)**，包含 40+ 接口的详细请求/响应示例、字段说明、错误码、团队分工建议。本文档仅保留前后端核心接口与 AI 服务接口的快速参考。

## 一、鉴权说明

所有 `/api/tasks/**`、`/api/reports/**`、`/api/users/**` 接口需要登录。

请求头携带：`Authorization: <token>`

（token 由登录/注册接口返回，Sa-Token 默认格式，无需 `Bearer` 前缀。）

公开接口（无需认证）：
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/system/**`

## 二、鉴权接口

### 注册

**POST** `/api/auth/register`

Request:
```json
{
  "username": "test",
  "password": "123456",
  "email": "test@example.com"
}
```

### 登录

**POST** `/api/auth/login`

Request:
```json
{
  "username": "test",
  "password": "123456"
}
```

Response: 同注册

### 登出

**POST** `/api/auth/logout`

需要携带 `Authorization` header。

### 当前用户

**GET** `/api/auth/me`

需要携带 `Authorization` header。

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "test",
    "email": "test@example.com",
    "createTime": "2025-01-01T00:00:00"
  }
}
```

## 三、核心业务接口

### 1. 创建检测任务

**POST** `/api/tasks`

Request:
```json
{
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1
  }
}
```

---

### 2. 获取任务列表

**GET** `/api/tasks`

查询参数：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| page | int | 否 | 1 | 页码，最小 1 |
| size | int | 否 | 10 | 每页条数，最大 100 |
| status | string | 否 | — | 任务状态（PENDING/PARSING_PAPER/.../FAILED/CANCELLED） |
| keyword | string | 否 | — | 模糊匹配论文标题或链接 |
| startTime | string | 否 | — | 创建时间起始，ISO 格式例 `2026-06-01T00:00:00` |
| endTime | string | 否 | — | 创建时间截止，ISO 格式例 `2026-06-20T23:59:59` |
| sortField | string | 否 | createTime | 排序字段白名单：createTime / updateTime / finishTime / status |
| sortOrder | string | 否 | desc | asc 或 desc |

示例：
```
GET /api/tasks?page=1&size=10&status=SUCCESS&keyword=attention&startTime=2026-06-01T00:00:00&endTime=2026-06-20T23:59:59&sortField=createTime&sortOrder=desc
```

Response:
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
        "createTime": "2025-01-01T00:00:00",
        "finishTime": "2025-01-01T00:05:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10
  }
}
```

---

### 3. 获取任务详情

**GET** `/api/tasks/{id}`

Response:
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
    "createTime": "2025-01-01T00:00:00",
    "updateTime": "2025-01-01T00:05:00",
    "finishTime": "2025-01-01T00:05:00"
  }
}
```

---

### 4. 删除任务（逻辑删除）

**DELETE** `/api/tasks/{taskId}`

Requires: `Authorization` header.

Constraints:
- 只能删除终态任务（SUCCESS / FAILED / CANCELLED）
- 进行中的任务返回错误："任务正在分析中，请取消后再删除"
- 删除后 `deleted=1`，任务从列表消失，关联数据保留

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### 4b. 批量删除任务

**POST** `/api/tasks/batch-delete`

Requires: `Authorization` header.

Request:
```json
{
  "taskIds": [1, 2, 3]
}
```
Constraints: 最多 50 个，只删除当前用户终态任务。

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "successCount": 2,
    "failedCount": 1,
    "results": [
      { "taskId": 1, "success": true, "message": "删除成功" },
      { "taskId": 2, "success": false, "message": "任务正在分析中，请取消后再删除" }
    ]
  }
}
```

---

### 5. 获取报告详情

**GET** `/api/reports/{taskId}`

Response:
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
      "stars": 100,
      "forks": 20,
      "defaultBranch": "main",
      "lastUpdatedAt": "2025-01-10",
      "confidence": 0.95,
      "confidenceReason": "Found in paper page"
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
      "summary": "该论文提供了较完整的代码仓库...",
      "methodSummary": "本文提出了...",
      "innovationSummary": "主要创新点包括...",
      "reproduceSteps": "1. 安装依赖\n2. 下载数据\n...",
      "riskTips": "注意：缺少数据集说明和模型权重说明。",
      "finalAdvice": "建议优先使用 Docker 环境复现。"
    }
  }
}
```

---

### 6. 获取 README 分析

**GET** `/api/tasks/{taskId}/analysis/readme`

Response:
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

---

### 6a. 导出 Markdown 报告（单任务）

**GET** `/api/reports/{taskId}/export/markdown`

Response: `Content-Type: text/markdown; charset=utf-8`，文件名为 `repocheck-report-{taskId}.md`。

报告包含 11 个章节，其中「十、环境诊断」会展示 V2 环境分析结果。如果任务尚未生成环境分析，则提示"尚未进行 V2 环境诊断"。

### 6b. 批量导出 Markdown 报告

**POST** `/api/reports/export/markdown/batch`

Requires: `Authorization` header.

Request:
```json
{
  "taskIds": [1, 2, 3]
}
```
Constraints: 最多 20 个，只导出当前用户已生成报告的任务。

Response: `Content-Type: application/zip`，文件名 `repocheck-reports.zip`。

ZIP 内容:
- `repocheck-report-{taskId}.md` — 每个成功任务一个 Markdown 文件
- `summary.md` — 跳过任务的说明（如有）

---

### 7. 重试任务

**POST** `/api/tasks/{id}/retry`

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 四、后端 → AI 服务接口

Base URL: `http://localhost:8000`

### 分析论文

**POST** `/api/analyze`

Request:
```json
{
  "taskId": 1,
  "paperUrl": "https://arxiv.org/abs/2501.xxxxx"
}
```

Response:
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
    "stars": 100,
    "forks": 20,
    "defaultBranch": "main",
    "lastUpdatedAt": "2025-01-10",
    "confidence": 0.95,
    "confidenceReason": "Found in paper page"
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
    "summary": "该论文提供了较完整的代码仓库...",
    "methodSummary": "本文提出了...",
    "innovationSummary": "主要创新点包括...",
    "reproduceSteps": "1. 安装依赖\n2. 下载数据\n...",
    "riskTips": "注意：缺少数据集说明和模型权重说明。",
    "finalAdvice": "建议优先使用 Docker 环境复现。"
  }
}
```

## 六、V2.0 环境分析接口

> 需登录，所有接口加 `Authorization: <token>` 请求头。

### 6.1 查询环境分析汇总

**GET** `/api/tasks/{taskId}/environment`

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1,
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
}
```

未生成时返回：
```json
{
  "code": 2001,
  "message": "环境分析尚未生成",
  "data": null
}
```

### 6.2 查询依赖列表

**GET** `/api/tasks/{taskId}/dependencies`

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "taskId": 1,
      "fileType": "requirements",
      "filePath": "requirements.txt",
      "packageName": "torch",
      "versionSpec": "==2.1.0",
      "source": "pip",
      "riskLevel": "MEDIUM",
      "riskReason": "PyTorch may require matching CUDA runtime"
    }
  ]
}
```

### 6.3 重新执行环境分析

**POST** `/api/tasks/{taskId}/environment/rebuild`

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": 1,
    "environmentAnalysis": { ... },
    "dependencies": [ ... ]
  }
}
```

### 6.4 AI 服务环境分析

**POST** `ai-service:/api/environment/analyze`

Request:
```json
{
  "taskId": 1,
  "repoInfo": {
    "platform": "GitHub",
    "repoUrl": "https://github.com/owner/repo",
    "repoName": "repo",
    "owner": "owner",
    "defaultBranch": "main"
  }
}
```

Response: 同 `EnvironmentReport` 结构（dependencies + environmentAnalysis）。
