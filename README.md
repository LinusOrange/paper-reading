# SAR Literature Demo

## 启动方式

```bash
OPENAI_API_KEY=your_key_here docker compose up --build
```

启动后：

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/healthz

## 当前组成

- `frontend/`：静态前端页面，通过 Nginx 代理 `/api` 和 `/healthz`
- `backend/`：FastAPI 接口骨架，已支持 PDF 上传与 OpenAI 分析任务排队入口
- `database/schema.sql`：PostgreSQL 初始化表结构
- `configs/sar-airborne-demo-collection.yaml`：SAR 方向采集配置

## 本轮新增能力

- 支持通过 `POST /api/papers/import/pdf` 上传 PDF
- 支持通过 `POST /api/analysis/{paper_id}/enqueue` 创建 OpenAI 分析任务
- `backend` 容器新增 `uploads_data` 卷用于保存上传文件

## 502 排查建议

如果前端页面能打开，但顶部显示 `502 Bad Gateway`，优先检查下面两件事：

1. backend 容器是否真的启动成功：

```bash
docker compose ps
docker compose logs backend
```

2. 服务器 `3000` 端口是否对外放通；如果 VSCode 端口转发能访问、但 `服务器IP:3000` 不能访问，通常是服务器防火墙或安全组没有放行 `3000` 端口。
