# SAR Literature Demo

## 启动方式

推荐先复制一份 `.env`：

```bash
cp .env.example .env
```

然后按需修改里面的：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `TASK_WORKER_ENABLED`（默认 `true`）
- `TASK_WORKER_POLL_INTERVAL_SECONDS`（默认 `3` 秒）

最后启动：

```bash
docker compose up --build
```

启动后：

- 总览页：http://localhost:3000/index.html
- 论文库：http://localhost:3000/papers.html
- 文献导入：http://localhost:3000/imports.html
- 分析与问答：http://localhost:3000/analysis.html
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/healthz

## 当前组成

- `frontend/`：静态多页面前端，按模块拆成总览、论文库、导入、分析页面
- `backend/`：FastAPI 接口骨架，已支持 PDF 上传、自动解析标题/年份、OpenAI 分析任务排队入口
- `database/schema.sql`：PostgreSQL 初始化表结构
- `configs/sar-airborne-demo-collection.yaml`：SAR 方向采集配置

## OpenAI 服务商配置

当前仓库已支持以下运行参数：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（默认 `https://once.novai.su/v1`）
- `OPENAI_MODEL`（默认 `gpt-5.4`）
- `TASK_WORKER_ENABLED`（默认 `true`）
- `TASK_WORKER_POLL_INTERVAL_SECONDS`（默认 `3`）

出于安全考虑，我没有把 API key 直接写进仓库文件，请通过环境变量传入。

推荐做法：

1. 执行 `cp .env.example .env`
2. 在项目根目录编辑 `.env`
3. 重新执行 `docker compose up --build`（或至少重启 backend 容器；环境变量只有在进程启动时才会重新读取）

如果你是直接在宿主机运行 backend，而不是通过 Docker Compose，那么现在后端也会自动读取项目根目录下的 `.env` 文件。

如果右上角状态提示显示“未配置 OpenAI Key（导入/浏览可用，分析/问答暂不可用）”，这是**正常现象**：表示后端在线，但当前环境还没有设置 `OPENAI_API_KEY`。这时论文导入、浏览、检索仍可使用，只有依赖 OpenAI 的分析与问答功能会被禁用。

## 如何检查 OpenAI 配置是否真的生效

你可以直接检查 `8000` 端口上的健康检查接口：

```bash
curl http://localhost:8000/healthz
```

重点看这些字段：

- `openai_configured`：后端是否读到了 key
- `analysis_available`：分析功能是否可用
- `openai_base_url`：当前实际使用的 OpenAI base URL
- `openai_model`：当前实际使用的模型
- `openai_key_hint`：已加载 key 的脱敏提示
- `env_file_path` / `env_file_exists`：后端识别到的 `.env` 路径和存在状态
- `task_worker_enabled` / `task_worker_running`：内置任务 worker 是否启用、是否已经启动
- `task_worker_poll_interval_seconds`：worker 当前轮询间隔

如果你走的是 Docker Compose，还可以进入容器再次确认：

```bash
docker compose exec backend python -c "from backend.app.config import settings; print({'configured': bool(settings.openai_api_key), 'base_url': settings.openai_base_url, 'model': settings.openai_model, 'env_file_path': settings.env_file_path, 'env_file_exists': settings.env_file_exists, 'worker_enabled': settings.task_worker_enabled, 'worker_poll_interval_seconds': settings.task_worker_poll_interval_seconds})"
```

## 本轮新增能力

- 支持通过 `POST /api/papers/import/pdf` 上传 PDF
- PDF 上传后自动解析标题与年份
- 支持通过 `POST /api/analysis/{paper_id}/enqueue` 创建 OpenAI 分析任务
- 前端已拆成多页面导航，减少单页面过长导致的滑动问题

## 502 排查建议

如果前端页面能打开，但顶部显示 `502 Bad Gateway`，优先检查下面两件事：

1. backend 容器是否真的启动成功：

```bash
docker compose ps
docker compose logs backend
```

2. 服务器 `3000` 端口是否对外放通；如果 VSCode 端口转发能访问、但 `服务器IP:3000` 不能访问，通常是服务器防火墙或安全组没有放行 `3000` 端口。
