# SAR Literature Demo

## 启动方式

推荐先复制一份 `.env`：

```bash
cp .env.example .env
```

然后按需修改里面的：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（例如 `https://us.novaiapi.com/v1`）
- `OPENAI_MODEL`（例如 `[次]gemini-3-pro-preview`）
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
- OpenAI 连通性检查：http://localhost:8000/healthz/openai

## 当前组成

- `frontend/`：静态多页面前端，按模块拆成总览、论文库、导入、分析页面
- `backend/`：FastAPI 接口骨架，已支持 PDF 上传、自动解析标题/年份、OpenAI 分析任务排队入口
- `database/schema.sql`：PostgreSQL 初始化表结构
- `configs/sar-airborne-demo-collection.yaml`：SAR 方向采集配置

## OpenAI 服务商配置

当前仓库已支持以下运行参数：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（默认 `https://us.novaiapi.com/v1`）
- `OPENAI_MODEL`（默认 `[次]gemini-3-pro-preview`）
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



### 我们当前的 OpenAI 调用方式是否匹配你提供的示例

是的，后端当前就是这种 OpenAI SDK 调用方式：

- `from openai import OpenAI`
- `OpenAI(api_key=..., base_url=...)`
- `client.chat.completions.create(model=..., messages=...)`

你给出的 `base_url=https://us.novaiapi.com/v1` 与 `model=[次]gemini-3-pro-preview` 已经作为默认值写入配置（仍可通过环境变量覆盖）。

另外，仓库中新增了自定义 Provider 的示例配置文件：

- `configs/model-providers.example.json`

该文件内已经包含你要求的 `models.providers.claude` 代码片段，可直接复制到你的模型网关/前端工具配置中。

## OpenAI API 直连检测（8000 端口）

如需单独验证 OpenAI API 调用是否可用，可执行：

```bash
curl http://localhost:8000/healthz/openai
```

返回 `status=ok` 表示后端已经成功完成一次真实的 OpenAI 调用；如果失败会返回 `502` 并附带错误详情。

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


## PDF 上传报 `ERR_CONNECTION_RESET` 的排查

如果浏览器 Network 中看到：

- `POST /api/papers/import/pdf net::ERR_CONNECTION_RESET`
- 前端显示 `PDF 上传失败 / Failed to fetch`

优先检查：

1. `frontend` 与 `backend` 容器是否都在运行：

```bash
docker compose ps
```

2. 后端是否在上传时抛错或重启：

```bash
docker compose logs -f backend
```

3. 前端 Nginx 反向代理是否正常（包括上传体积限制）：

```bash
docker compose logs -f frontend
```

本仓库已把 Nginx 的 `client_max_body_size` 调整为 `100m`，并放宽了 `/api/` 代理超时。修改后请重新构建并启动：

```bash
docker compose up --build -d
```


## 论文分析流水线（正式版起步）

当前 worker 已不再是纯占位符，处理 `processing_tasks` 时按任务类型执行固定流水线：

1. `extract_text`：提取或构建论文可用文本
2. `generate_summary`：优先调用 OpenAI 生成结构化摘要（失败时回退到规则摘要）
3. `extract_entities`：基于摘要/文本提取方法与关键词
4. `recommend_tags`：基于摘要与实体结果推荐方向标签并写入 `paper_tags`

执行结果会写回：

- `paper_analysis.summary_json`
- `paper_analysis.entities_json`
- `paper_tags`

你可以通过 `GET /api/tasks` 观察任务是否从 `queued -> running -> completed/failed`。


## PDF 预览连接失败的排查

如果访问 `http://<host>:3000/api/papers/{id}/pdf` 出现“无法连接/被重置”：

1. 先确认论文对应的 PDF 文件确实存在于 `UPLOAD_DIR`；
2. 执行 `docker compose logs -f backend` 检查 `/api/papers/{id}/pdf` 是否返回 `404 pdf not found`；
3. 执行 `docker compose logs -f frontend` 检查 Nginx 是否有 upstream 连接错误。

本仓库已将 PDF 响应头调整为 `inline`，并把论文库页面的预览改成“手动点击开始预览”，避免进入页面时自动触发下载。
