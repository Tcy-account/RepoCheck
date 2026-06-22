# 数据库设计文档

> **版本管理**: 数据库迁移由 [Flyway](https://flywaydb.org/) 统一管理，迁移脚本位于 `backend/src/main/resources/db/migration/`。`docs/sql/init.sql` 仅作为历史参考。
>
> **Flyway 版本**: V1 (user/task) → V2 (paper/repo/analysis/report) → V3 (candidate/timeline/file) → V4 (indexes/seed) → V5 (file_matches_json) → V6 (readme_analysis_json)。当前最新 V6。

## 数据表

### 1. user - 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| username | VARCHAR(50) | 用户名 |
| password | VARCHAR(255) | 密码 (加密) |
| email | VARCHAR(100) | 邮箱 |
| create_time | DATETIME | 创建时间 |
| update_time | DATETIME | 更新时间 |

### 2. paper_task - 论文检测任务表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| user_id | BIGINT | 用户 ID |
| paper_url | VARCHAR(500) | arXiv 论文链接 |
| paper_title | VARCHAR(500) | 论文标题 |
| status | VARCHAR(30) | 任务状态 |
| error_message | TEXT | 错误信息 |
| create_time | DATETIME | 创建时间 |
| update_time | DATETIME | 更新时间 |
| finish_time | DATETIME | 完成时间 |

**任务状态枚举**:
- `PENDING` - 等待处理
- `PARSING_PAPER` - 正在解析论文
- `SEARCHING_REPO` - 正在搜索仓库
- `ANALYZING_REPO` - 正在分析仓库
- `GENERATING_REPORT` - 正在生成报告
- `SUCCESS` - 成功
- `FAILED` - 失败
- `CANCELLED` - 已取消

### 3. paper_info - 论文信息表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| arxiv_id | VARCHAR(50) | arXiv ID |
| title | VARCHAR(500) | 论文标题 |
| authors | TEXT | 作者列表 |
| abstract_text | TEXT | 摘要 |
| published_at | DATE | 发布日期 |
| paper_url | VARCHAR(500) | 论文链接 |

### 4. repo_info - 代码仓库信息表 (最终选中的仓库)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| platform | VARCHAR(20) | 平台: GitHub / GitLab |
| repo_url | VARCHAR(500) | 仓库 URL |
| repo_name | VARCHAR(200) | 仓库名称 |
| owner | VARCHAR(200) | 仓库所有者 |
| stars | INT | Star 数量 |
| forks | INT | Fork 数量 |
| default_branch | VARCHAR(100) | 默认分支 |
| last_updated_at | DATETIME | 最后更新时间 |
| confidence | DECIMAL(5,4) | 置信度 0.0000-1.0000 |
| confidence_reason | VARCHAR(500) | 置信度理由 |

### 5. repo_candidate - 候选仓库表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| platform | VARCHAR(20) | 平台: GitHub / GitLab |
| repo_url | VARCHAR(500) | 仓库 URL |
| repo_name | VARCHAR(200) | 仓库名称 |
| owner | VARCHAR(200) | 仓库所有者 |
| stars | INT | Star 数量 |
| forks | INT | Fork 数量 |
| default_branch | VARCHAR(100) | 默认分支 |
| last_updated_at | DATETIME | 最后更新时间 |
| confidence | DECIMAL(5,4) | 置信度 |
| confidence_reason | VARCHAR(500) | 置信度理由 |
| source | VARCHAR(50) | 来源: arxiv_page / github_search / gitlab_search |
| selected | TINYINT | 是否被选中: 0=否 1=是 |
| create_time | DATETIME | 创建时间 |

### 6. repo_analysis - 仓库分析结果表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| has_readme | TINYINT | 是否有 README |
| has_requirements | TINYINT | 是否有 requirements.txt |
| has_environment_yml | TINYINT | 是否有 environment.yml |
| has_dockerfile | TINYINT | 是否有 Dockerfile |
| has_license | TINYINT | 是否有 LICENSE |
| has_train_code | TINYINT | 是否有训练代码 |
| has_inference_code | TINYINT | 是否有推理代码 |
| has_dataset_doc | TINYINT | 是否有数据集说明 |
| has_weight_doc | TINYINT | 是否有模型权重说明 |
| readme_quality_score | INT | README 质量评分 (0-100) |
| dependency_complexity_score | INT | 依赖复杂度评分 (0-100) |
| structure_completeness_score | INT | 结构完整度评分 (0-100) |
| file_matches_json | JSON | 匹配文件明细 (V5 新增) |
| readme_analysis_json | JSON | README 章节分析结果 (V6 新增) |

### 7. report - 报告表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| reproducibility_score | INT | 复现难度评分 (0-100) |
| completeness_score | INT | 仓库完整度评分 (0-100) |
| environment_score | INT | 环境复杂度评分 (0-100) |
| risk_level | VARCHAR(10) | 风险等级: LOW / MEDIUM / HIGH |
| summary | TEXT | AI 总结报告 |
| method_summary | TEXT | 方法总结 |
| innovation_summary | TEXT | 创新点总结 |
| reproduce_steps | TEXT | 复现步骤 |
| risk_tips | TEXT | 风险提示 |
| final_advice | TEXT | 最终建议 |
| create_time | DATETIME | 创建时间 |

### 8. file_info - 文件信息表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| file_id | VARCHAR(64) | 文件 UUID |
| file_name | VARCHAR(255) | 原始文件名 |
| file_size | BIGINT | 文件大小 (字节) |
| file_type | VARCHAR(30) | 文件类型 |
| minio_path | VARCHAR(500) | MinIO 存储路径 |
| task_id | BIGINT | 关联任务 ID |
| create_time | DATETIME | 创建时间 |

### 9. task_timeline - 任务时间线表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| task_id | BIGINT | 关联任务 ID |
| status | VARCHAR(30) | 状态 |
| message | VARCHAR(500) | 状态变更说明 |
| create_time | DATETIME | 创建时间 |

## ER 图

```
┌──────────┐       ┌──────────────┐       ┌──────────────┐
│   user   │ 1──N │  paper_task   │ 1──N  │ task_timeline│
└──────────┘       └──────┬───────┘       └──────────────┘
                          │ 1
            ┌─────────────┼───────────────┐
            │             │               │
            1             1               1
            │             │               │
    ┌───────┴───────┐ ┌───┴────┐ ┌───────┴───────┐
    │  paper_info   │ │repo_info│ │ repo_analysis │
    └───────────────┘ └────────┘ └───────────────┘
            │             │               │
            └───────── N ─┼─── N ────────┘
                          │
                    ┌─────┴─────┐
                    │  1    repo_candidate
                    │
                    1
              ┌─────┴─────┐
              │   report  │
              └───────────┘
              ┌─────┴─────┐
              │  file_info │
              └───────────┘
```

## 外键与唯一约束策略

V1 阶段不加数据库外键约束，仅通过索引保证查询性能。

**唯一约束**（V2 migration 创建）：
- `paper_info.task_id` — UNIQUE INDEX
- `repo_info.task_id` — UNIQUE INDEX
- `repo_analysis.task_id` — UNIQUE INDEX
- `report.task_id` — UNIQUE INDEX
- `repo_candidate` 与 `task_timeline` 支持多条记录，无 UNIQUE 约束。

逻辑关系如下：

| 子表 | 逻辑外键 | 父表 |
|------|---------|------|
| paper_task | user_id | user.id |
| paper_info | task_id | paper_task.id |
| repo_info | task_id | paper_task.id |
| repo_candidate | task_id | paper_task.id |
| repo_analysis | task_id | paper_task.id |
| report | task_id | paper_task.id |
| file_info | task_id | paper_task.id |
| task_timeline | task_id | paper_task.id |
