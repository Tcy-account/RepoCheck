# RepoCheck Frontend

Vue3 + Vite + TypeScript + Pinia + Axios + Element Plus

## 包管理器

项目使用 **pnpm** 管理依赖（pnpm >= 8）。

```bash
# 安装 pnpm（如未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 首次安装后，批准 esbuild 和 vue-demi 的构建脚本（pnpm v10+）
pnpm approve-builds esbuild vue-demi
```

## 启动

```bash
pnpm dev
```

开发服务器运行在 `http://localhost:3000`，API 请求自动代理到 `http://localhost:8080`。

## 构建

```bash
pnpm build
```

## 目录结构

```
src/
├── api/              # Axios 封装 + 接口模块
│   ├── request.ts    # Axios 实例 + 请求/响应拦截器
│   ├── types.ts      # 全部接口类型定义
│   ├── auth.ts       # 认证 API (register/login/logout/me)
│   ├── user.ts       # 用户 API (me/update/password)
│   ├── task.ts       # 任务 API (create/list/detail/status/timeline/retry/cancel/delete)
│   ├── report.ts     # 报告 API (detail/scores/regenerate/health/ai-health/config)
│   ├── paper.ts      # 论文 API (get/refresh)
│   ├── repo.ts       # 仓库 API (get/candidates/update/search)
│   ├── analysis.ts   # 分析 API (get/rebuild/files/readme)
│   └── file.ts       # 文件 API (upload/download-url/delete)
├── stores/           # Pinia 状态管理
│   ├── task.ts       # 任务状态
│   └── user.ts       # 用户状态
├── router/           # Vue Router
│   └── index.ts
├── views/            # 页面
│   ├── Home.vue       # 首页：输入 arXiv 链接 + 提交
│   ├── TaskList.vue   # 任务列表：分页 + 状态筛选
│   ├── TaskDetail.vue # 报告详情：论文/仓库/评分/AI 报告
│   └── Profile.vue    # 个人中心
├── layouts/          # 布局
│   └── MainLayout.vue
├── mock/             # Mock 数据（开发调试用）
│   └── task.ts
├── App.vue
├── main.ts
└── env.d.ts
```

## 页面说明

| 路由 | 页面 | 说明 |
|------|------|------|
| /home | 首页 | 输入 arXiv 链接，提交检测任务 |
| /tasks | 任务列表 | 分页展示所有任务，支持按状态筛选 |
| /tasks/:id | 报告详情 | 展示论文信息、仓库分析、评分、AI 报告 |
| /profile | 个人中心 | 用户信息占位 + 历史任务入口 |

## 常见问题

### pnpm 安装后构建失败 (ERR_PNPM_IGNORED_BUILDS)

pnpm v10+ 默认不执行第三方构建脚本。运行以下命令手动批准：

```bash
pnpm approve-builds esbuild vue-demi
```

### `__dirname is not defined` 错误

`vite.config.ts` 已使用 `import.meta.url` + `fileURLToPath` 替代 `__dirname`。
如果使用旧版本模板，请确保从 `node:url` 导入 `fileURLToPath`。

### 从 npm 迁移到 pnpm

```bash
# 1. 删除 npm 产物
rm -rf node_modules package-lock.json

# 2. 安装 pnpm（如未安装）
npm install -g pnpm

# 3. 重建依赖
pnpm install

# 4. 批准构建脚本（pnpm v10+）
pnpm approve-builds esbuild vue-demi
```
