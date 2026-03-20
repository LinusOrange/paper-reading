# 机载高分辨率 SAR 成像文献系统 Demo 实施方案

## 1. Demo 定位

本次 Demo 不再覆盖过多研究方向，而是聚焦一个明确主题：

**机载高分辨率 SAR 成像**。

在这个主题下，优先覆盖两个重点子场景：

1. **高速场景**
2. **大斜视角场景**

这样做的原因是：

- 主题足够聚焦，方便快速做出可用 Demo；
- 机载高分辨率 SAR 成像本身有明确工程背景；
- 高速与大斜视两个子方向都具有代表性的算法挑战；
- 后续如果 Demo 跑通，可以自然扩展到 GMTI、ISAR、联合成像/运动补偿等方向。

这份方案的目标不是“写一个文档”，而是把系统直接收敛成一个 **可在服务器部署、可收集论文、可调用 OpenAI 分析、可在线检索的 Demo 版本**。

---

## 2. 当前约束与已确认前提

根据你最新的反馈，本次 Demo 采用以下约束：

- **模型统一使用 OpenAI API**：当前阶段不再接火山模型，也不做多模型路由。
- **研究主题固定**：以机载高分辨率 SAR 成像为主。
- **重点子主题**：高速场景、大斜视角场景。
- **部署方式**：部署在服务器上，优先推荐 Linux 服务器。
- **历史论文来源**：已有一部分历史论文，可由你后续协助整理与导入。

因此，第一版系统的目标应该非常明确：

> 把“机载高分辨率 SAR 成像”方向的文献采集、元数据整理、PDF 归档、OpenAI 摘要分析、在线查询和专题浏览先做通。

---

## 3. 推荐的 Demo 形态

建议第一版 Demo 做成一个 **单服务器部署的前后端分离系统**。

### 3.1 组成结构

- **前端 Web**：用于查询、浏览、上传、审核、专题管理。
- **后端 API**：负责文献导入、检索、问答、分析、任务管理。
- **任务 Worker**：负责异步解析 PDF、调用 OpenAI、生成 embedding、写回数据库。
- **数据库**：保存论文、标签、笔记、任务状态、分析结果。
- **对象存储**：保存 PDF 与附件。

### 3.2 为什么推荐单服务器 Demo

因为你们当前是要尽快做出一个方向性 Demo，而不是一上来做成复杂微服务平台。单服务器方案有几个好处：

- 部署简单；
- 运维成本低；
- 方便迭代字段、Prompt 和数据流程；
- 适合先导入少量历史论文和持续新增文献；
- 对 OpenAI API 方案来说，不依赖本地 GPU。

---

## 4. 推荐部署方案

你问“部署在服务器上，或者你可以推荐部署在哪里”，我的建议是：

## 4.1 第一选择：实验室或课题组 Linux 服务器

这是最推荐的方案，原因：

- 数据更容易内部管理；
- PDF 与笔记不容易外流；
- 接口服务稳定；
- 便于后续接入更多组员共同使用；
- 方便做定时抓取与长期归档。

### 推荐配置

对于 Demo，推荐最低配置：

- 8 vCPU
- 16~32 GB RAM
- 500 GB SSD
- Ubuntu 22.04 LTS
- Docker + Docker Compose

如果后续论文量上来，建议提升到：

- 16 vCPU
- 32~64 GB RAM
- 1 TB SSD

### 为什么不强制需要 GPU

因为当前分析能力主要走 OpenAI API：

- 摘要生成由 OpenAI 完成；
- 问答由 OpenAI 完成；
- 标签抽取由 OpenAI 完成；
- embedding 也可以直接调用 OpenAI。

因此服务器重点是：

- 网络稳定；
- 磁盘够大；
- 数据库响应稳定；
- 便于长期运行任务队列。

## 4.2 第二选择：学校云主机 / 公有云 ECS

如果实验室没有稳定服务器，可以临时部署在：

- 学校云主机
- 阿里云 / 腾讯云 / 华为云 ECS

但这类部署要额外注意：

- PDF 与数据库的访问权限；
- API Key 的安全；
- 出口网络对 OpenAI API 的可用性；
- 成本持续性。

## 4.3 不建议作为正式 Demo 的方案

- 本地电脑长期运行
- 用个人笔记本充当服务器
- 多人共享一个手工维护目录而没有数据库

这些方式可以临时试验，但不适合你们后续持续积累论文资产。

---

## 5. Demo 范围收敛建议

第一版 Demo 请只做下面 6 件事：

1. **支持导入历史 PDF / DOI / BibTeX**
2. **支持围绕 SAR 子方向自动采集新论文**
3. **支持 PDF 在线预览与归档**
4. **支持 OpenAI 生成结构化摘要**
5. **支持按照主题/方法/场景在线检索**
6. **支持专题页展示“高速场景”和“大斜视场景”**

先不要做的内容：

- 复杂权限体系
- 多模型路由
- 大规模推荐系统
- 自动综述全文生成
- 很复杂的可视化知识图谱

Demo 阶段的原则是：

> 先把一个主题做深、做稳、做通，再考虑扩展到其他雷达方向。

---

## 6. Demo 的前后端拆分

## 6.1 前端页面

建议 Demo 前端只保留 6 个页面：

### A. 首页 Dashboard

显示：

- 当前论文总数
- 已解析论文数
- 待审核论文数
- 高速场景论文数
- 大斜视场景论文数
- 最近新增论文

### B. 文献列表页

支持筛选：

- 主题：机载高分辨率 SAR
- 子主题：高速场景 / 大斜视场景
- 年份
- 方法
- 是否有 PDF
- 是否已摘要

### C. 文献详情页

展示：

- 标题、作者、年份、来源
- PDF 预览
- OpenAI 摘要
- 关键贡献
- 适用场景
- 方法类型
- 速度/斜视相关信息
- 组内笔记
- 相似论文

### D. 采集任务页

展示：

- 当前采集任务
- 抓取来源
- 成功数 / 重复数 / 失败数
- 待补传 PDF 的记录

### E. 专题页

Demo 只做两个专题：

- 高速场景 SAR 成像
- 大斜视角 SAR 成像

每个专题页显示：

- 代表论文
- 时间线
- 方法分类
- 组内备注

### F. 管理页

用于维护：

- OpenAI Key 配置
- 采集关键词模板
- 标签体系
- Prompt 模板

---

## 6.2 后端 API 模块

Demo 只保留 5 组核心 API：

- `Paper API`
- `Ingestion API`
- `Search API`
- `Analysis API`
- `Admin API`

### 推荐接口清单

#### 导入相关

- `POST /api/papers/import/pdf`
- `POST /api/papers/import/doi`
- `POST /api/papers/import/bibtex`
- `POST /api/papers/import/url`

#### 文献查询

- `GET /api/papers`
- `GET /api/papers/{paper_id}`
- `PATCH /api/papers/{paper_id}`

#### 检索相关

- `POST /api/search/filter`
- `POST /api/search/fulltext`
- `POST /api/search/semantic`
- `GET /api/papers/{paper_id}/similar`

#### 分析相关

- `POST /api/analysis/{paper_id}/summary`
- `POST /api/analysis/{paper_id}/extract`
- `POST /api/analysis/{paper_id}/tags`
- `POST /api/qa/ask`

#### 任务与配置

- `GET /api/tasks`
- `POST /api/collectors/run`
- `GET /api/config/prompts`
- `PATCH /api/config/prompts`

---

## 7. 面向机载高分辨率 SAR 的文献采集设计

这里是 Demo 最关键的部分之一：**如何围绕 SAR 成像方向持续收集论文。**

## 7.1 Demo 采集源

第一版建议只接下面 5 种来源：

1. **arXiv**：跟踪预印本最新工作
2. **Crossref**：补 DOI 与元数据
3. **OpenAlex**：补引用关系与相似文献候选
4. **Semantic Scholar**：补被引、相似文献信息
5. **手工导入**：历史 PDF、BibTeX、导师推荐论文

## 7.2 采集关键词模板

建议把采集分成 3 组关键词。

### A. 主方向基础词

- `airborne SAR high resolution imaging`
- `airborne synthetic aperture radar imaging`
- `high resolution SAR imaging`
- `airborne radar imaging motion compensation`

### B. 高速场景词

- `high speed airborne SAR imaging`
- `high speed platform SAR imaging`
- `motion compensation airborne SAR`
- `high dynamic SAR imaging`
- `range cell migration airborne SAR`
- `high-speed SAR autofocus`

### C. 大斜视场景词

- `high squint SAR imaging`
- `large squint angle SAR imaging`
- `high squint airborne SAR`
- `squinted SAR motion compensation`
- `high-resolution high-squint SAR`
- `azimuth-variant SAR imaging`

这些词应该放到可编辑配置里，不写死在代码中。

---

## 7.3 采集调度建议

### 每周自动采集

- 跑一次基础词
- 跑一次高速场景词
- 跑一次大斜视词
- 自动生成新增候选列表

### 每月专题补采

由你们人工指定：

- 年份区间
- 特定作者
- 特定会议/期刊
- 某篇代表论文的引用扩展

### 首次冷启动导入

建议第一批优先导入：

- 你们已有历史论文
- 导师常引用的代表论文
- 高速场景经典论文
- 大斜视场景经典论文

这样可以更快形成一个“种子库”。

---

## 7.4 采集后的处理链

论文采集完成后统一走下面流程：

1. 建立候选记录
2. DOI / 标题判重
3. 拉基础元数据
4. 关联 PDF 或等待补传 PDF
5. 提取全文
6. 调用 OpenAI 做摘要
7. 调用 OpenAI 提取标签与场景信息
8. 构建 embedding
9. 写入检索索引
10. 等待人工审核

---

## 8. OpenAI API 在 Demo 中的使用方式

你已经确认：**当前 OpenAI 的开销可以接受，因此这一版 Demo 可以全部使用 OpenAI API。**

那我建议就不要在 Demo 里引入多模型复杂度，统一使用 OpenAI 完成：

- 摘要
- 结构化信息抽取
- 标签推荐
- 问答
- embedding
- 相似论文检索辅助

这样做的优势：

- 架构更简单；
- 输出风格统一；
- Prompt 更容易维护；
- 便于后续评估“纯 OpenAI 版本”到底效果有多好；
- 后面如果要降成本，再替换 query rewrite 或 embedding 部分即可。

---

## 8.1 建议的 OpenAI 任务拆分

### 任务 1：单篇论文结构化摘要

输出字段建议固定：

- `problem`
- `method`
- `scenario`
- `contributions`
- `speed_related_issue`
- `squint_related_issue`
- `datasets_or_simulation`
- `metrics`
- `limitations`

### 任务 2：场景标签抽取

抽取：

- 是否属于高速场景
- 是否属于大斜视场景
- 是否涉及运动补偿
- 是否涉及距离徙动校正
- 是否涉及自聚焦
- 是否涉及成像几何建模

### 任务 3：专题问答

例如回答：

- “高速机载 SAR 成像常见难点有哪些？”
- “大斜视场景下哪些方法适合高分辨成像？”
- “哪些论文同时讨论了运动补偿和高斜视成像？”

### 任务 4：相似论文推荐解释

不只是返回“相似论文列表”，还返回：

- 相似点在哪里；
- 是成像模型相似，还是场景相似；
- 是高速问题相似，还是大斜视问题相似。

---

## 8.2 OpenAI Prompt 模板建议

Demo 建议至少配置 4 类 Prompt：

1. `sar_paper_summary_prompt`
2. `sar_entity_extract_prompt`
3. `sar_topic_tag_prompt`
4. `sar_qa_prompt`

Prompt 输出尽量固定成 JSON，方便直接入库。

---

## 9. Demo 数据模型建议

为了快速落地，第一版数据表不需要太多，但建议至少有以下内容。

## 9.1 核心表

### `papers`

- `id`
- `title`
- `abstract`
- `year`
- `doi`
- `venue`
- `source_url`
- `pdf_object_key`
- `full_text`
- `status`
- `is_airborne_sar`
- `is_high_resolution`
- `is_high_speed`
- `is_large_squint`
- `created_at`
- `updated_at`

### `paper_analysis`

- `paper_id`
- `summary_json`
- `entities_json`
- `qa_cache`
- `embedding_model`
- `analysis_model`
- `prompt_version`

### `paper_tags`

例如：

- `topic/high-speed`
- `topic/large-squint`
- `method/motion-compensation`
- `method/autofocus`
- `method/range-cell-migration-correction`
- `method/chirp-scaling`
- `method/omega-k`

### `processing_tasks`

记录：

- 导入
- 解析
- 摘要
- embedding
- 标签抽取
- 审核

### `collections`

第一版只做两个专题集合：

- `sar-high-speed`
- `sar-large-squint`

---

## 9.2 推荐标签体系

建议第一版把标签限制在 4 类：

1. **主题**：airborne-sar / high-resolution / high-speed / large-squint
2. **方法**：motion-compensation / autofocus / rcmc / chirp-scaling / omega-k / backprojection
3. **问题**：range-migration / azimuth-variant / phase-error / geometry-distortion
4. **实验**：simulation / measured-data / real-flight-data

这样更利于 Demo 阶段保持一致性。

---

## 10. 用户使用流程

## 10.1 冷启动阶段

1. 你们把已有历史 PDF 和 BibTeX 整理出来；
2. 前端批量导入；
3. 后端异步解析；
4. OpenAI 自动生成摘要与标签；
5. 人工审核关键论文；
6. 建立高速与大斜视两个专题页。

## 10.2 正常运行阶段

1. 系统每周自动抓取新论文；
2. 新论文进入待处理列表；
3. 自动生成摘要和标签；
4. 组内成员做少量审核；
5. 用户通过关键词或自然语言查询；
6. 在专题页中持续积累该方向知识。

---

## 11. 建议的 Demo 开发顺序

建议按 4 周节奏推进。

## 第 1 周：打底

- 确定部署服务器
- 搭 PostgreSQL + MinIO + Redis
- 初始化 FastAPI 后端
- 初始化 Next.js 前端
- 建基本数据表

## 第 2 周：导入与采集

- 支持 PDF / DOI / BibTeX 导入
- 建 arXiv / Crossref / OpenAlex 采集器
- 跑第一批历史论文导入
- 跑第一批 SAR 关键词采集

## 第 3 周：OpenAI 分析与检索

- 接 OpenAI 摘要
- 接 OpenAI 标签抽取
- 接 embedding
- 实现结构化搜索
- 实现语义搜索

## 第 4 周：专题页与验收

- 完成高速专题页
- 完成大斜视专题页
- 完成论文详情页
- 做一次组内试用
- 根据反馈修正 Prompt 和标签

---

## 12. 我建议你下一步提供给我的信息

为了让我下一轮继续把方案推进到“可开发”的粒度，你最好补充下面这些信息：

1. 你们现有历史论文是 PDF 为主，还是 Zotero/BibTeX 为主？
2. 服务器大致配置是什么？
3. 是否希望第一版支持组内多用户登录？
4. 你们更希望界面以中文为主还是中英混合？
5. 历史论文里是否已经有人做过人工笔记？

---

## 13. 我下一步可以继续为你做什么

如果你确认这个 Demo 方向，我下一步最建议继续做的是：

1. **给出 PostgreSQL 表结构 SQL 草案**
2. **给出 FastAPI 路由定义与请求响应 Schema**
3. **给出 OpenAI Prompt 模板（SAR 专用）**
4. **给出前端页面原型结构**
5. **给出首批 SAR 文献采集关键词配置与种子论文整理模板**

也就是说，下一步我可以直接从“方案文档”进入“开发蓝图”阶段。
