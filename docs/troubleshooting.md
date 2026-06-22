# RepoCheck V1 常见问题排查

## 1. AI 服务调用失败

**现象**：创建任务后立即失败，`paper_task.error_message` 显示 "AI 服务暂时不可用，请确认 ai-service 已启动"

**原因**：ai-service 未启动或端口错误。

**解决**：

```bash
cd ai-service
uvicorn app.main:app --reload --port 8000
```

检查 ai-service 是否正常运行：

```bash
curl http://localhost:8000/health
# 应返回: {"status": "ok"}
```

**后端日志**：搜索 `AI service connect failed` 可确认连接失败。

---

## 2. AI 服务调用超时

**现象**：任务执行一段时间后失败，`error_message` 显示 "AI 服务调用超时，请稍后重试"

**原因**：GitHub API 响应慢、大仓库文件树过大，或网络不稳定。

**解决**：

1. 稍后重试任务（在任务详情页点击"重试任务"）
2. 配置 GITHUB_TOKEN 可提升 API 速率：

   ```bash
   # ai-service/.env
   GITHUB_TOKEN=ghp_xxxxxxxxxxxx
   ```

**后端日志**：搜索 `AI service timeout` 可确认超时。

---

## 3. GitHub API 限流

**现象**：分析结果中未找到仓库，`risk_level` 为 HIGH，报告说明"系统未能找到可信代码仓库"

**原因**：未配置 GITHUB_TOKEN，GitHub API 对未认证请求有严格限流（60次/小时）。

**解决**：

```bash
# 在 ai-service/.env 中配置
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

**ai-service 日志**：搜索 `GitHub search failed` 可确认限流。

**注意**：GitHub 搜索失败不会导致任务整体失败，而是生成高风险报告并提示未找到仓库。

---

## 4. arXiv 论文解析失败

**现象**：任务失败，`error_message` 显示 "论文解析失败：未找到对应 arXiv 论文"

**原因**：arXiv ID 不合法、链接格式错误，或 arXiv API 暂时不可用。

**解决**：

1. 确认链接格式为：`https://arxiv.org/abs/XXXX.XXXXX` 或 `https://arxiv.org/pdf/XXXX.XXXXX.pdf`
2. 确认 arXiv ID 对应的论文真实存在
3. 如确认链接正确，可能是 arXiv API 暂时不可用，稍后重试

**后端日志**：搜索 `parse_paper_node failed` 可确认解析失败原因。

---

## 5. 报告不存在

**现象**：前端显示"报告尚未生成或任务分析失败"

**原因**：
- 任务尚未运行完成（状态为 PENDING / PARSING_PAPER / SEARCHING_REPO / ANALYZING_REPO / GENERATING_REPORT）
- 任务执行失败（状态为 FAILED）
- 任务已取消（状态为 CANCELLED）
- 任务已被删除

**解决**：

1. 检查任务状态是否正确（查看任务详情页状态标签）
2. 如任务为 FAILED，查看 `errorMessage` 了解失败原因
3. 如任务仍在运行中，等待分析完成后刷新页面
4. 查看任务时间线了解当前执行到哪一步

**后端日志**：搜索 `taskId=<你的任务ID>` 可追踪任务完整流程。

---

## 6. 后端返回 401 未登录

**现象**：前端自动跳转到登录页

**原因**：Token 过期或未登录。

**解决**：重新登录即可。

---

## 7. 服务暂时不可用

**现象**：前端显示"服务暂时不可用，请检查后端是否启动"

**原因**：后端 Spring Boot 服务未启动或端口冲突。

**解决**：

```bash
cd backend
mvn spring-boot:run
```

检查后端是否运行：访问 `http://localhost:8080`

---

## 8. 请求超时

**现象**：前端显示"请求超时，请稍后重试"

**原因**：前端请求 30 秒未收到响应。

**解决**：

1. 检查网络连接
2. 确认后端和 ai-service 均正常运行
3. 如大文件分析耗时较长，可重新提交任务

---

## 9. 任务一直处于运行中状态

**现象**：任务状态长时间停留在 RUNNING 但不更新

**原因**：ai-service 工作流未正常完成或后端线程异常。

**解决**：

1. 查看 ai-service 日志是否有异常（搜索对应 `taskId`）
2. 查看后端日志是否有保存失败的错误
3. 可尝试取消任务后重新提交

---

## 日志排查指南

### 后端日志

搜索 `taskId=<数字>` 查看任务的完整生命周期：

```
# 正常流程
Task <taskId> created
Calling AI service: http://localhost:8000/api/analyze with taskId=<taskId>
Task <taskId> results saved, status=SUCCESS

# 失败流程
Task <taskId> AI call failed
Business exception: [4002] AI 服务调用超时 [POST /api/tasks]
```

### AI 服务日志

搜索 `task=<taskId>` 查看分析流程各节点：

```
# 正常流程
[task=<taskId>] parse_paper_node: start, url=...
[task=<taskId>] find_repo_node: start, searching for title='...'
[task=<taskId>] analyze_repo_structure_node: start, repo=...
[task=<taskId>] analyze_docs_node: start
[task=<taskId>] score_repo_node: start
[task=<taskId>] generate_report_node: start

# 异常流程
[task=<taskId>] parse_paper_node failed: ...
[task=<taskId>] find_repo_node: GitHub search failed: ...
```
