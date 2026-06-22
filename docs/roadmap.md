# RepoCheck 演进路线

## V1.0 - MVP (当前版本)

- [x] 基础框架搭建 (Monorepo)
- [x] arXiv 链接提交与解析
- [x] GitHub/GitLab 仓库搜索 (API)
- [x] 仓库静态结构分析
- [x] 复现可行性评分与报告生成
- [x] 任务管理与报告查看
- [x] 用户注册/登录 (Sa-Token)
- [x] 手动指定仓库 + 重新分析
- [x] 任务重试 (仅 FAILED/CANCELLED)
- [x] 任务取消 + CANCELLED 防覆盖
- [x] 任务状态时间线
- [x] 幂等保存 (upsert 防止 UNIQUE 约束错误)
- [x] 保存事务一致性 (@Transactional)
- [x] RestTemplate 超时配置 (connect 5s / read 60s)
- [x] 分析依据透明化 (fileMatches 匹配文件明细)
- [x] README 文档分析 (7 项关键词检查 + 质量评分)
- [x] Markdown 报告导出
- [x] 冒烟测试计划 (test-plan-v1.md)

**限制**: 不运行代码，不 clone 仓库，不下载数据/模型

## V2.0 - 深度分析

- [ ] 仓库 README LLM 深度分析
- [ ] 代码结构复杂度分析 (AST 解析)
- [ ] 依赖版本兼容性检查
- [ ] Docker 环境可复现性评估
- [ ] 论文-代码一致性对比 (LLM)
- [ ] 批量任务处理队列 (Redis)
- [ ] 报告 PDF 导出

## V3.0 - 自动化复现

- [ ] Docker 容器自动构建与运行
- [ ] 沙箱环境代码执行验证
- [ ] 实验结果复现对比
- [ ] 多仓库交叉验证
- [ ] 社区评价数据整合
- [ ] 实时分析进度推送 (WebSocket)

## V4.0 - 平台化

- [ ] 论文代码排行榜
- [ ] 用户自定义分析规则
- [ ] API 开放平台
- [ ] CI/CD 集成 (GitHub Action)
- [ ] 多语言扩展 (非 Python 项目)
- [ ] 知识图谱构建
- [ ] 复现报告社区共享
