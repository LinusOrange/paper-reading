# SAR Literature Demo

## 启动方式

```bash
docker compose up --build
```

启动后：

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/healthz

## 当前组成

- `frontend/`：静态前端页面，通过 Nginx 代理 `/api` 和 `/healthz`
- `backend/`：FastAPI 接口骨架
- `database/schema.sql`：PostgreSQL 初始化表结构
- `configs/sar-airborne-demo-collection.yaml`：SAR 方向采集配置
