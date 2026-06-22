# RepoCheck AI Service

FastAPI + LangChain + LangGraph

## 启动

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务运行在 `http://localhost:8000`，API 文档见 `http://localhost:8000/docs`。

## 目录结构

```
app/
├── main.py                     # FastAPI 入口
├── api/
│   └── analyze.py              # 分析接口
├── graph/
│   ├── state.py                # LangGraph 状态定义
│   ├── workflow.py             # 工作流定义
│   └── nodes/
│       ├── parse_paper.py      # 解析论文
│       ├── find_repo.py        # 搜索仓库
│       ├── select_best_repo.py # 选择最佳仓库
│       ├── analyze_repo_structure.py # 分析仓库结构
│       ├── analyze_docs.py     # 分析文档
│       ├── score_repo.py       # 评分
│       └── generate_report.py  # 生成报告
├── tools/
│   ├── arxiv_tool.py           # arXiv 工具
│   ├── github_tool.py          # GitHub 工具
│   ├── gitlab_tool.py          # GitLab 工具
│   ├── repo_file_tool.py       # 仓库文件工具
│   └── llm_tool.py             # LLM 工具
├── schemas/
│   ├── request.py              # 请求模型
│   └── response.py             # 响应模型
└── core/
    ├── config.py               # 配置
    └── logger.py               # 日志
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/analyze | 执行论文分析 |
| GET | / | 服务信息 |
| GET | /health | 健康检查 |

## V1 范围

- 所有外部 API 调用为 mock 实现
- LangGraph 7 节点全部可运行
- 不 clone 仓库，不运行代码
- LLM 调用封装在 llm_tool.py，V1 返回模板化文本
