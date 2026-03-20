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
