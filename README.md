# RepoCheck

论文代码可用性检测器 — 输入 arXiv 论文链接，自动解析论文信息，寻找对应代码仓库，进行静态分析，生成复现可行性报告。

## 技术架构

| 层级 | 技术栈 |
|------|--------|
| 前端 | Vue3 + Vite + TypeScript + Pinia + Axios + Element Plus |
| 后端 | SpringBoot 3.x + MyBatis Plus + MySQL + Redis + MinIO + Sa-Token |
| AI 服务 | FastAPI + LangChain + LangGraph |

## 服务调用链路

```
Vue3 → SpringBoot → FastAPI → LangGraph → Tools
```

## 项目结构

```
RepoCheck/
├── frontend/          # Vue3 前端 (8 个 API 模块)
├── backend/           # SpringBoot 后端 (11 个业务模块)
│   └── src/main/java/com/repocheck/modules/
│       ├── auth/      ├── user/     ├── task/
│       ├── paper/     ├── repo/     ├── analysis/
│       ├── report/    ├── ai/       ├── file/
│       ├── system/    └── admin/
├── ai-service/        # FastAPI AI 服务
├── docs/              # 文档
│   ├── api-design-v1.md   # V1.0 完整接口设计 (40+ 接口)
│   ├── architecture.md    # 总体架构
│   ├── api.md             # API 快速参考
│   ├── database.md        # 数据库设计
│   ├── workflow.md        # LangGraph 工作流
│   ├── roadmap.md         # 演进路线
│   └── sql/init.sql       # 建表脚本
├── docker-compose.yml
└── README.md
```

## 快速启动

### 1. 启动基础设施

```bash
docker-compose up -d
```

### 2. 初始化数据库

数据库由 Flyway 自动迁移管理，启动后端后自动建表。无需手动执行任何 SQL。

### 3. 启动 AI 服务

```bash
cd ai-service
cp .env.example .env
# 编辑 .env 填入 API Key
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动后端

```bash
cd backend
mvn spring-boot:run
```

### 5. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

## V1.0 范围

- 静态分析，不运行代码
- 不 git clone
- 不 pip install
- 不下载数据集/模型权重
