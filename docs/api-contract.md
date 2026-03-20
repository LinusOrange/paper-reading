# SAR Demo API Contract

## 1. 目标

本文件把机载高分辨率 SAR 文献系统 Demo 的第一版接口固定下来，便于后端开发、前端联调和后续数据库落地。

## 2. 核心资源

- `papers`
- `analysis`
- `search`
- `tasks`
- `config/prompts`

## 3. 接口列表

### 3.1 Paper API

- `POST /api/papers/import/pdf`
- `POST /api/papers/import/doi`
- `POST /api/papers/import/bibtex`
- `POST /api/papers/import/url`
- `GET /api/papers`
- `GET /api/papers/{paper_id}`
- `PATCH /api/papers/{paper_id}`

### 3.2 Search API

- `POST /api/search/filter`
- `POST /api/search/fulltext`
- `POST /api/search/semantic`
- `GET /api/papers/{paper_id}/similar`

### 3.3 Analysis API

- `POST /api/analysis/{paper_id}/summary`
- `POST /api/analysis/{paper_id}/extract`
- `POST /api/analysis/{paper_id}/tags`
- `POST /api/qa/ask`

### 3.4 Admin API

- `GET /api/tasks`
- `POST /api/collectors/run`
- `GET /api/config/prompts`
- `PATCH /api/config/prompts`

## 4. 前端联调优先顺序

1. `GET /healthz`
2. `GET /api/papers`
3. `GET /api/papers/{paper_id}`
4. `POST /api/search/filter`
5. `POST /api/analysis/{paper_id}/summary`
6. `POST /api/qa/ask`

## 5. 返回结构约定

### 文献详情

```json
{
  "id": 1,
  "title": "Large-Squint Airborne SAR Imaging Demo Paper",
  "year": 2024,
  "venue": "Demo Venue",
  "status": "analyzed",
  "tags": ["airborne-sar", "high-resolution", "large-squint"],
  "summary": {
    "problem": "...",
    "method": "...",
    "scenario": "...",
    "contributions": ["..."],
    "speed_related_issue": "...",
    "squint_related_issue": "..."
  }
}
```

### 问答响应

```json
{
  "question": "大斜视场景下哪些方法适合高分辨成像？",
  "answer": "...",
  "citations": [1]
}
```
