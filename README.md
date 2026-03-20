# SAR Literature Demo

## 启动方式

```bash
OPENAI_API_KEY=your_key_here \
OPENAI_BASE_URL=https://once.novai.su/v1 \
OPENAI_MODEL=gpt-5.4 \
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

出于安全考虑，我没有把 API key 直接写进仓库文件，请通过环境变量传入。

如果右上角状态提示显示“未配置 OpenAI Key（导入/浏览可用，分析/问答暂不可用）”，这是**正常现象**：表示后端在线，但当前环境还没有设置 `OPENAI_API_KEY`。这时论文导入、浏览、检索仍可使用，只有依赖 OpenAI 的分析与问答功能会被禁用。

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
