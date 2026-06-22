# RepoCheck Backend

SpringBoot 3.x + MyBatis Plus + MySQL + Redis + MinIO + Sa-Token

## 启动

### 前置条件

1. 启动 MySQL/Redis/MinIO (`docker-compose up -d`)
2. 初始化数据库：执行 `docs/sql/init.sql`

### 运行

```bash
mvn spring-boot:run
```

服务运行在 `http://localhost:8080`。

## 目录结构

```
src/main/java/com/repocheck/
├── RepoCheckApplication.java   # 启动类
├── common/                     # 通用类
│   ├── Result.java             # 统一响应
│   ├── PageResult.java         # 分页对象
│   └── ErrorCode.java          # 错误码枚举
├── config/                     # 配置类
│   ├── AsyncConfig.java
│   ├── MinioConfig.java
│   ├── MyBatisPlusConfig.java
│   ├── MyMetaObjectHandler.java
│   ├── RedisConfig.java
│   ├── RestTemplateConfig.java
│   ├── SaTokenConfig.java
│   └── WebMvcConfig.java
├── exception/                  # 异常处理
│   ├── BusinessException.java
│   └── GlobalExceptionHandler.java
├── modules/                    # 业务域模块 (按接口域分包)
│   ├── auth/                   # 认证
│   │   ├── controller/AuthController.java
│   │   ├── service/ (AuthService + impl/)
│   │   ├── dto/ (LoginRequest, RegisterRequest)
│   │   └── vo/ (LoginVO, CurrentUserVO)
│   ├── user/                   # 用户
│   │   ├── controller/UserController.java
│   │   ├── service/ (UserService + impl/)
│   │   ├── entity/User.java
│   │   ├── mapper/UserMapper.java
│   │   ├── dto/ (UpdateUserRequest, UpdatePasswordRequest)
│   │   └── vo/UserVO.java
│   ├── task/                   # 任务管理
│   │   ├── controller/TaskController.java
│   │   ├── service/ (TaskService + impl/)
│   │   ├── entity/PaperTask.java
│   │   ├── mapper/PaperTaskMapper.java
│   │   ├── dto/ (CreateTaskRequest, TaskQueryRequest)
│   │   ├── vo/ (TaskVO, TaskDetailVO, TaskStatusVO, TaskTimelineVO)
│   │   └── enums/TaskStatus.java
│   ├── paper/                  # 论文信息
│   │   ├── controller/PaperController.java
│   │   ├── service/ (PaperService + impl/)
│   │   ├── entity/PaperInfo.java
│   │   ├── mapper/PaperInfoMapper.java
│   │   └── vo/PaperInfoVO.java
│   ├── repo/                   # 仓库信息
│   │   ├── controller/RepoController.java
│   │   ├── service/ (RepoService + impl/)
│   │   ├── entity/RepoInfo.java
│   │   ├── mapper/RepoInfoMapper.java
│   │   ├── dto/UpdateRepoRequest.java
│   │   └── vo/ (RepoInfoVO, RepoCandidateVO)
│   ├── analysis/               # 仓库分析
│   │   ├── controller/AnalysisController.java
│   │   ├── service/ (AnalysisService + impl/)
│   │   ├── entity/RepoAnalysis.java
│   │   ├── mapper/RepoAnalysisMapper.java
│   │   └── vo/ (RepoAnalysisVO, ReadmeAnalysisVO)
│   ├── report/                 # 报告
│   │   ├── controller/ReportController.java
│   │   ├── service/ (ReportService + impl/)
│   │   ├── entity/Report.java
│   │   ├── mapper/ReportMapper.java
│   │   └── vo/ (ReportVO, ReportScoreVO)
│   ├── ai/                     # AI 调用
│   │   ├── service/ (AiService + impl/)
│   │   └── dto/ (AnalyzeRequest, AnalyzeResponse)
│   ├── file/                   # 文件管理 (MinIO 占位)
│   │   ├── controller/FileController.java
│   │   ├── service/ (FileService + impl/)
│   │   ├── entity/FileInfo.java
│   │   ├── mapper/FileInfoMapper.java
│   │   └── vo/ (FileUploadVO, FileDownloadVO)
│   ├── system/                 # 系统接口
│   │   ├── controller/SystemController.java
│   │   └── service/ (SystemService + impl/)
│   └── admin/                  # 管理员 (V1 预留)
│       ├── controller/AdminController.java
│       └── service/ (AdminService + impl/)
└── resources/
    └── application.yml
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/tasks | 创建检测任务 |
| GET | /api/tasks | 任务列表 (支持 page/size/status/keyword) |
| GET | /api/tasks/{id} | 任务详情 |
| GET | /api/tasks/{id}/status | 任务状态 (轻量轮询) |
| GET | /api/tasks/{id}/timeline | 任务时间线 |
| POST | /api/tasks/{id}/retry | 重试任务 |
| POST | /api/tasks/{id}/cancel | 取消任务 |
| DELETE | /api/tasks/{id} | 删除任务 |
| GET | /api/tasks/{id}/paper | 论文信息 |
| POST | /api/tasks/{id}/paper/refresh | 刷新论文信息 |
| GET | /api/tasks/{id}/repo | 仓库信息 |
| GET | /api/tasks/{id}/repo/candidates | 候选仓库列表 |
| PUT | /api/tasks/{id}/repo | 人工指定仓库 |
| POST | /api/tasks/{id}/repo/search | 重新搜索仓库 |
| GET | /api/tasks/{id}/analysis | 仓库分析结果 |
| POST | /api/tasks/{id}/analysis/rebuild | 重建分析 |
| GET | /api/tasks/{id}/analysis/files | 仓库文件列表 |
| GET | /api/tasks/{id}/analysis/readme | README 原文 |
| GET | /api/reports/{taskId} | 报告详情 |
| GET | /api/reports/{taskId}/scores | 评分摘要 |
| POST | /api/reports/{taskId}/regenerate | 重新生成报告 |
| GET | /api/reports/{taskId}/export/markdown | 导出 Markdown |
| GET | /api/reports/{taskId}/export/pdf | 导出 PDF (V1 预留) |
| POST | /api/files/upload | 上传文件 |
| GET | /api/files/{fileId}/download-url | 获取下载链接 |
| DELETE | /api/files/{fileId} | 删除文件 |
| GET | /api/system/health | 后端健康检查 |
| GET | /api/system/ai-health | AI 服务健康检查 |
| GET | /api/system/config | 系统配置 |

详细接口设计文档见 `docs/api-design-v1.md`。
