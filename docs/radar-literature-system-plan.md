# 雷达信号处理文献系统实施方案（前后端分离 + API 驱动）

## 1. 目标与设计原则

这个系统不是单纯的“论文网盘”，而是一个面向课题组长期使用的 **文献采集、理解、检索、分析、归档平台**。围绕你们的 3~4 个研究方向，系统要解决四个核心问题：

1. **论文从哪里来**：能够持续搜集 arXiv、Crossref、OpenAlex、Semantic Scholar、IEEE Xplore 检索结果，以及组内已有 PDF。
2. **论文怎么整理**：能够把元数据、标签、笔记、方法摘要、复现信息统一结构化存储。
3. **论文怎么理解**：通过 OpenAI API 做高精度摘要、关键点抽取、方法对比和问答。
4. **论文怎么低成本查找**：后期把“高精度分析”和“低成本检索/召回”拆开，查找和粗筛可接入火山模型等更低成本模型。

因此，本次方案明确采用：

- **前后端分离**
- **所有处理流程通过 API 编排**
- **文献处理异步化**
- **模型能力分层路由**
- **人工审核 + AI 辅助结合**

---

## 2. 推荐总体架构

建议拆成 6 个层次：

1. **前端展示层**：Web 管理后台 + 检索页面 + 专题页面。
2. **后端 API 层**：统一提供论文、标签、任务、问答、检索、采集等 REST API。
3. **任务编排层**：负责导入 PDF、抓取元数据、OCR/文本解析、向量化、AI 摘要等异步任务。
4. **数据存储层**：关系型数据库 + 对象存储 + 向量索引。
5. **模型服务层**：OpenAI API 负责高精度理解；火山模型/其他模型负责低成本召回、粗分类、查询改写。
6. **外部数据源层**：arXiv、Crossref、OpenAlex、Semantic Scholar、手工导入、BibTeX 导入。

### 2.1 技术栈建议

#### 前端

- React + Next.js
- UI 组件库：Ant Design 或 Shadcn UI
- 状态管理：Zustand / React Query
- 文档预览：PDF.js

#### 后端

- Python + FastAPI
- ORM：SQLAlchemy
- 异步任务：Celery 或 Dramatiq
- 消息队列：Redis
- 接口文档：OpenAPI / Swagger

#### 数据层

- PostgreSQL：主数据库
- pgvector：向量检索
- MinIO / S3 / NAS：PDF 与附件存储
- OpenSearch（可选）：后期增强全文检索

#### 文本处理

- PyMuPDF：PDF 文本抽取
- GROBID（可选）：结构化解析论文标题、作者、参考文献
- Unstructured（可选）：通用文本切分

#### 模型层

- **OpenAI API**：论文精读摘要、结构化抽取、问答、主题分析、综述辅助
- **火山模型/其他低成本模型**：查询改写、粗标签推荐、批量初筛、相似候选召回

---

## 3. 前后端分离设计

## 3.1 前端模块划分

前端建议至少拆成 7 个页面/模块：

### A. 登录与项目主页

用于展示：

- 当前文献总量
- 本周新增论文数
- 各方向论文数量
- 待处理任务数
- 最近热点关键词

### B. 文献列表页

支持：

- 按方向、年份、方法、体制、作者、来源筛选
- 按标题、摘要、关键词全文搜索
- 查看处理状态（新导入、已解析、已摘要、已审核）
- 批量打标签、批量归档、批量重跑解析

### C. 文献详情页

每篇论文显示：

- 基础元数据
- PDF 在线预览
- AI 生成摘要
- 核心贡献
- 方法标签/雷达体制标签
- 数据集与评价指标
- 复现风险
- 组内阅读笔记
- 相似论文推荐

### D. 检索与问答页

提供三种查询模式：

1. 结构化筛选
2. 全文检索
3. 智能问答

例如：

- “2022 年以后基于 Transformer 的 SAR 目标识别论文有哪些？”
- “哪些论文比较过 MUSIC 与 ESPRIT？”
- “帮我总结毫米波 FMCW 人体行为识别的主流方法路线。”

### E. 采集任务页

用于管理论文采集任务：

- 新建关键词抓取任务
- 查看采集源状态
- 查看去重结果
- 查看失败原因
- 手工补传 PDF

### F. 专题页

把某一个方向形成“专题文献库”，例如：

- MIMO 雷达 DOA 估计
- FMCW 微多普勒分类
- SAR 成像与超分辨

专题页支持：

- 固定筛选条件
- 时间轴浏览
- 代表论文列表
- 专题总结

### G. 管理后台

用于管理：

- 标签体系
- 成员权限
- 模型路由策略
- API Key 配置
- Prompt 模板
- 定时任务配置

---

## 3.2 后端服务拆分

建议后端按领域拆成以下 API 模块：

- `Auth API`：登录、权限、用户管理
- `Paper API`：论文 CRUD、详情、状态流转
- `Ingestion API`：导入 DOI/BibTeX/PDF/URL、发起采集任务
- `Search API`：结构化搜索、全文搜索、语义搜索
- `Analysis API`：摘要、标签推荐、方法抽取、对比分析、问答
- `Collection API`：专题集合管理
- `Task API`：异步任务与处理流水
- `Admin API`：模型路由、Prompt、系统配置

如果后续规模变大，再把采集、解析、问答拆成独立微服务；第一阶段不建议一开始就过度微服务化。

---

## 4. 核心 API 设计

下面给出建议的 API 设计方式，便于你们后续直接开始实现。

## 4.1 文献导入 API

### 1）通过 DOI 导入

`POST /api/papers/import/doi`

请求体示例：

```json
{
  "doi": "10.xxxx/xxxx",
  "direction_hint": ["mimo-radar", "doa"],
  "auto_analyze": true
}
```

处理流程：

1. 查询 Crossref / OpenAlex 元数据
2. 检查数据库是否已存在
3. 若已存在，则返回已有记录
4. 若不存在，则创建论文记录
5. 尝试获取 PDF 链接
6. 创建异步任务：文本解析、标签推荐、摘要生成、向量入库

### 2）通过 BibTeX 导入

`POST /api/papers/import/bibtex`

支持粘贴文本或上传 `.bib` 文件。

### 3）通过 URL 导入

`POST /api/papers/import/url`

支持输入 arXiv、出版社页面、DOI 跳转链接。

### 4）通过 PDF 上传导入

`POST /api/papers/import/pdf`

适用于：

- 组内已有 PDF
- 从学校资源下载后的文件
- 无公开 API 的来源

上传 PDF 后，系统自动：

- 计算 hash
- 尝试从 PDF 首段抽取标题
- 用标题回查 Crossref / OpenAlex
- 关联元数据

---

## 4.2 文献详情与编辑 API

### 获取文献详情

`GET /api/papers/{paper_id}`

返回内容建议包括：

- 基础信息
- 标签
- AI 摘要
- 抽取出的“任务/方法/数据集/指标”
- PDF 地址
- 相似论文
- 阅读笔记
- 处理日志

### 更新文献元数据

`PATCH /api/papers/{paper_id}`

可修改字段：

- 标题
- 年份
- venue
- 主方向
- 优先级
- 是否需要重分析

### 文献状态流转

`POST /api/papers/{paper_id}/status`

状态建议：

- `new`
- `metadata_ready`
- `pdf_ready`
- `parsed`
- `analyzed`
- `reviewed`
- `archived`

---

## 4.3 检索 API

### 结构化搜索

`POST /api/search/filter`

支持筛选字段：

- 年份区间
- 方向
- 任务
- 雷达体制
- 方法标签
- 是否有代码
- 是否已审核

### 全文搜索

`POST /api/search/fulltext`

针对：

- 标题
- 摘要
- 正文切片
- 组内笔记

### 语义搜索

`POST /api/search/semantic`

请求体示例：

```json
{
  "query": "find papers about sparse Bayesian DOA estimation for MIMO radar",
  "top_k": 10,
  "direction_hint": ["mimo-radar"]
}
```

### 相似论文推荐

`GET /api/papers/{paper_id}/similar`

先做 embedding 召回，再结合标签做 rerank。

---

## 4.4 智能分析 API

### 生成论文摘要

`POST /api/analysis/{paper_id}/summary`

输出建议固定成结构化 JSON：

- `problem`
- `method`
- `contributions`
- `datasets_or_scenarios`
- `metrics`
- `limitations`
- `reproducibility`

### 自动标签推荐

`POST /api/analysis/{paper_id}/tags`

### 方法/实验信息抽取

`POST /api/analysis/{paper_id}/extract`

抽取字段建议包括：

- 雷达体制
- 任务类型
- 方法范式
- 数据来源
- 指标
- 是否有开源代码

### 论文问答

`POST /api/qa/ask`

请求体示例：

```json
{
  "question": "总结 2021 年以后 MIMO 雷达 DOA 估计中稀疏贝叶斯方法的发展脉络",
  "scope": {
    "direction": ["mimo-radar", "doa"],
    "year_from": 2021
  },
  "mode": "high_accuracy"
}
```

这里的 `mode` 很重要，后端可据此选择不同模型路由。

---

## 5. 后端处理流程（API 驱动）

这是最关键的部分：**所有处理都围绕一条论文处理流水线进行**。

## 5.1 论文入库主流程

无论是 DOI、BibTeX、URL 还是 PDF，统一走下面的处理链：

1. **接收导入请求**
2. **创建 paper 记录**
3. **去重检查**
4. **拉取或补全元数据**
5. **下载或上传 PDF**
6. **抽取全文文本**
7. **切片与索引**
8. **调用模型生成摘要与标签**
9. **写入向量库**
10. **进入人工审核队列**
11. **审核通过后归档可检索**

## 5.2 异步任务拆分

建议每篇论文拆成多个任务，方便失败重跑：

- `fetch_metadata`
- `download_pdf`
- `extract_text`
- `parse_structure`
- `generate_summary`
- `recommend_tags`
- `extract_entities`
- `build_embeddings`
- `quality_check`

这样做的好处：

- 某一步失败不影响其他步骤
- 成本高的步骤可单独控制
- 后续便于做批处理和重试机制

## 5.3 处理流水表示意

```text
[前端提交 DOI/PDF/URL]
        |
        v
[Ingestion API]
        |
        v
[Paper Service -> PostgreSQL]
        |
        +--> [Metadata Task]
        +--> [PDF Task]
        +--> [Text Parse Task]
        +--> [Analysis Task(OpenAI)]
        +--> [Embedding Task(低成本模型/OpenAI)]
        |
        v
[审核队列]
        |
        v
[Search API / QA API / 专题页]
```

---

## 6. 论文搜集系统设计

你特别提到“论文的搜集也要设计好，并且告诉我可以怎么修改”，这里我建议把论文采集做成 **可配置采集器系统**。

## 6.1 采集器类型设计

每个采集器都实现统一接口：

- `search(query, filters)`
- `fetch_detail(id)`
- `normalize(record)`
- `download_pdf(record)`

建议第一阶段实现以下采集器：

### A. arXiv 采集器

适合：

- 跟踪最新预印本
- 按关键词定期抓取
- 快速发现新方法

### B. Crossref 采集器

适合：

- 用 DOI 查元数据
- 补齐期刊、出版年份、作者信息

### C. OpenAlex 采集器

适合：

- 查引用关系
- 查相似工作
- 补全学术图谱信息

### D. Semantic Scholar 采集器

适合：

- 做相似论文候选召回
- 获取引用/被引信息

### E. 手工导入器

适合：

- 学校资源下载的 PDF
- 导师转发文献
- Zotero/BibTeX 历史库

---

## 6.2 采集任务配置方式

建议给每个研究方向建立一组“检索模板”。

例如：

### 方向 1：MIMO 雷达 + DOA

- `MIMO radar DOA estimation`
- `sparse Bayesian DOA MIMO radar`
- `gridless DOA radar`
- `off-grid DOA radar`

### 方向 2：FMCW + 微多普勒分类

- `FMCW radar micro-Doppler classification`
- `mmWave radar human activity recognition`
- `micro-Doppler transformer radar`

### 方向 3：SAR 成像/解译

- `SAR imaging deep learning`
- `SAR super-resolution radar`
- `SAR target recognition transformer`

### 方向 4：STAP/杂波抑制/检测

- `radar STAP clutter suppression`
- `adaptive detection radar clutter`
- `knowledge-aided STAP radar`

这些查询模板不要写死在代码里，建议做成管理后台中的可编辑配置。

---

## 6.3 采集策略

建议采用三层采集机制：

### 第一层：定时自动采集

每周跑一次：

- 抓取最近 7~14 天的新增论文
- 进入“待初筛”列表

### 第二层：专题补采

当某个方向需要补文献时，由负责人手工创建专题采集任务：

- 指定关键词
- 指定年份范围
- 指定来源
- 指定是否只抓高引用文献

### 第三层：种子扩展

从一篇代表论文出发，自动拉：

- 引用文献
- 被引文献
- 相似文献

这对于写综述非常有用。

---

## 6.4 去重与版本合并

建议用四级规则：

1. DOI 一致，直接判重
2. 标题归一化一致，判重
3. 标题高相似 + 第一作者 + 年份接近，疑似重复
4. arXiv 版本与正式发表版本，不删除，做 `version_link`

你们后面如果发现：

- 同一篇论文存在 conference 和 journal extended version
- 同一作者在 arXiv 与期刊版标题略有改动

系统应支持“人工合并记录”，而不是简单删除。

---

## 7. 论文理解与分析：OpenAI API 为主

你已经明确提出：**在论文理解和分析方面，希望使用 OpenAI API，因为精确度更高。**

我建议完全支持，并把 OpenAI 放在高价值环节。

## 7.1 适合用 OpenAI API 的任务

### 高精度任务

- 结构化摘要生成
- 论文方法抽取
- 贡献点总结
- 不同论文对比
- 特定方向综述草稿
- 基于文献库的问答
- 复现风险分析
- “与本组课题的关联”生成建议

### 原因

这些任务对：

- 准确理解上下文
- 长文本推理
- 结构化输出稳定性
- 多篇论文对比能力

要求更高，因此优先使用 OpenAI。

---

## 7.2 OpenAI API 调用策略

建议不要“来一个请求调一次大模型全文”，而是分层调用：

### 第一层：切片抽取

对论文正文分 chunk，提取：

- 问题定义
- 方法描述
- 实验设置
- 结论段

### 第二层：结构化汇总

把第一层结果送入 OpenAI，生成标准 JSON：

- `problem_definition`
- `core_method`
- `innovation_points`
- `experiment_setup`
- `main_results`
- `limitations`
- `radar_context`

### 第三层：面向应用的总结

再生成：

- 精读卡
- 组会汇报摘要
- 与本组课题相关性分析
- 与其他论文的比较结论

这样成本更可控，结果也更稳定。

---

## 7.3 Prompt 设计建议

建议把 Prompt 做成后台可配置模板，至少分成：

- `paper_summary_prompt`
- `tag_recommend_prompt`
- `radar_entity_extract_prompt`
- `paper_compare_prompt`
- `survey_outline_prompt`
- `qa_prompt`

并要求所有高精度任务尽量输出 **JSON Schema**，避免自由文本难以落库。

---

## 8. 低成本查找：火山模型等作为后期路由

你还提出：**后期论文查找时，可以使用其他模型如火山模型来降低成本。**

这是非常合理的，我建议采用“**双层模型策略**”。

## 8.1 模型能力分层

### A. 高精度模型（OpenAI）

用于：

- 精读摘要
- 多文献对比
- 综述生成
- 高质量问答
- 复杂标签抽取

### B. 低成本模型（火山模型等）

用于：

- 用户查询改写
- 粗粒度标签推荐
- 相似文献初筛
- 热词提取
- 批量候选召回后的初步排序

---

## 8.2 路由策略建议

后端配置一个 `model_router`，根据任务类型自动选择模型。

例如：

- `summary_high_accuracy` -> OpenAI
- `qa_high_accuracy` -> OpenAI
- `query_rewrite_low_cost` -> 火山模型
- `candidate_rerank_low_cost` -> 火山模型
- `bulk_tagging_low_cost` -> 火山模型

这样后端 API 不变，只改路由配置即可切换成本策略。

---

## 8.3 推荐的低成本使用方式

后期最适合让低成本模型承担的是“查找前置步骤”，例如：

1. 用户输入自然语言查询
2. 低成本模型改写成更适合检索的关键词组合
3. Search API 从数据库/向量库召回候选论文
4. 如果只是列清单，则直接返回
5. 如果需要深入总结，再调用 OpenAI 做最终分析

这个模式非常适合控制费用。

---

## 9. 数据库设计建议

下面给一个更偏实施的表设计思路。

## 9.1 核心数据表

### `papers`

存储论文主信息：

- `id`
- `title`
- `title_normalized`
- `abstract`
- `year`
- `doi`
- `arxiv_id`
- `venue`
- `source_url`
- `pdf_object_key`
- `full_text`
- `status`
- `primary_direction`
- `priority`
- `created_at`
- `updated_at`

### `paper_versions`

存储版本关系：

- `paper_id`
- `version_type`（arxiv/conference/journal）
- `related_paper_id`
- `relation_type`（preprint_of/extended_version_of）

### `authors`

存储作者信息。

### `paper_authors`

存储作者顺序。

### `tags`

存储标签体系：

- `id`
- `name`
- `category`
- `parent_id`
- `description`

### `paper_tags`

存储论文与标签关联，并区分：

- `source = human`
- `source = ai`
- `confidence`

### `paper_notes`

存储组内笔记。

### `paper_analysis`

存储模型生成结果：

- `summary_json`
- `entities_json`
- `comparison_cache`
- `qa_cache`
- `model_provider`
- `model_name`
- `prompt_version`

### `paper_chunks`

存储切片后的正文内容与 embedding 引用。

### `ingestion_jobs`

存储采集任务。

### `processing_tasks`

存储异步任务执行状态。

---

## 9.2 面向雷达方向的标签体系

建议标签至少分 5 大类：

1. **方向**：MIMO、SAR、FMCW、STAP、目标识别等
2. **任务**：检测、估计、分类、跟踪、成像、重建
3. **体制/场景**：车载、低空、海杂波、人体感知、遥感
4. **方法**：稀疏恢复、贝叶斯、图优化、CNN、Transformer、扩散模型
5. **数据/指标**：仿真、实测、公开数据集、Pd、Pfa、RMSE、PSNR 等

这部分建议第一版不要追求过细，先保证一致性和可维护性。

---

## 10. 典型页面与 API 的交互流程

这里给几个真实使用场景。

## 10.1 场景一：老师给一篇 PDF，要求快速入库

流程：

1. 前端上传 PDF
2. 调用 `POST /api/papers/import/pdf`
3. 后端创建 paper 记录
4. 异步抽取标题与正文
5. 回查 DOI/元数据
6. 调用 OpenAI 生成结构化摘要
7. 自动推荐标签
8. 前端详情页展示，等待人工审核

## 10.2 场景二：每周自动抓取新文献

流程：

1. 定时任务触发采集器
2. 调用各来源 search
3. 抓到结果后写入 `ingestion_jobs`
4. 去重
5. 对新增论文自动拉元数据
6. 将高相关论文推入待处理列表
7. 前端采集任务页展示结果

## 10.3 场景三：学生查询某方向近年进展

流程：

1. 前端输入自然语言问题
2. 低成本模型做 query rewrite
3. Search API 做结构化 + 向量混合召回
4. 若只要论文列表，则直接返回
5. 若要“总结研究脉络”，再由 OpenAI 基于候选文献生成总结

---

## 11. 推荐实施顺序

为了降低风险，我建议分 4 个阶段做。

## 阶段 1：最小可用版（2~4 周）

目标：先跑通导入、存储、检索。

实现内容：

- PostgreSQL + MinIO 搭好
- `papers`、`tags`、`notes` 基本表建好
- 前端完成列表页、详情页、上传页
- 支持 DOI / PDF / BibTeX 导入
- 支持标签搜索
- 支持组内笔记

## 阶段 2：半自动处理版（3~5 周）

目标：减少人工整理工作量。

实现内容：

- PDF 文本抽取
- 元数据补全
- 自动标签推荐
- OpenAI 摘要生成
- 异步任务面板

## 阶段 3：智能检索版（3~4 周）

目标：支持“像问人一样问系统”。

实现内容：

- 向量检索
- 语义搜索
- 相似论文推荐
- 问答页面
- 模型路由策略

## 阶段 4：综述辅助版（长期）

目标：直接服务综述和课题凝练。

实现内容：

- 多论文对比
- 专题综述草稿
- 研究路线总结
- 与本组方向匹配分析

---

## 12. 需要你确认的关键问题

在正式开建前，我建议你回答下面这些问题，我后续可以继续帮你把方案细化到数据库、API 字段甚至页面原型：

1. **你们准备部署在哪里？**
   - 实验室服务器
   - 学校云主机
   - 本地电脑 + NAS

2. **课题组是否已经有一批历史 PDF 或 Zotero 库？**
   - 如果有，第一版最好从已有文献导入开始。

3. **你们更看重中文界面还是英文界面？**
   - 这会影响前端设计与标签命名。

4. **你们是否需要权限分级？**
   - 例如老师、博士生、硕士生可编辑范围不同。

5. **是否允许系统自动抓取外部来源的元数据，但 PDF 由人工上传？**
   - 这和版权、学校资源访问方式有关。

6. **OpenAI API 预算大概如何？**
   - 这决定哪些任务默认走 OpenAI，哪些先走低成本模型。

---

## 13. 我建议你下一步这样推进

如果要真正开始做，我建议按下面顺序继续：

### 第一步：先定“方向 + 标签体系”

我可以下一轮直接帮你产出：

- 一版雷达信号处理标签树
- 每个方向对应的检索关键词模板
- 第一批应导入的种子论文范围

### 第二步：我帮你画数据库表结构

我可以继续直接给出：

- PostgreSQL 表结构
- 字段定义
- 索引建议
- `SQLAlchemy` 模型草案

### 第三步：我帮你列 API 清单

我可以继续细化成：

- FastAPI 路由定义
- 请求/响应 JSON Schema
- 异步任务状态机
- 前端页面与接口映射关系

### 第四步：我帮你设计 Prompt 与模型路由

我可以继续细化成：

- OpenAI 摘要 Prompt
- 论文信息抽取 Prompt
- 火山模型低成本 query rewrite Prompt
- 模型路由策略表

---

## 14. 建议你现在就做的决定

如果你想让我下一步直接进入“可开发阶段”，请你优先告诉我这 4 件事：

1. 你们的 3~4 个研究方向具体是什么；
2. 你们计划部署到哪里；
3. 现有历史论文大概有多少；
4. 是否接受“OpenAI 做精分析，火山模型做低成本检索前处理”的路线。

只要这 4 个问题确定下来，我下一步就可以继续给你：

- 数据库表设计
- 前端页面草图
- FastAPI 接口设计
- 论文采集配置模板
- OpenAI / 火山模型调用策略表
