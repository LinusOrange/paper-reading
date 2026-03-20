# Airborne SAR Imaging Review 项目初始化

## 项目目标
本项目用于系统整理“机载SAR成像（airborne SAR imaging）”相关文献，重点覆盖：
- SAR成像基础与改进方法
- 机载SAR成像算法
- NCS（Nonlinear Chirp Scaling）相关方法

目标时间范围以 **2020—2026** 为主，允许补充少量2020年前奠基性文献。
当前阶段仅完成项目初始化，**尚未开始正式检索**。

## 目录用途
- `00_admin/`：项目范围、变更日志、管理文件
- `01_protocol/`：检索协议、纳排标准、质量规则
- `02_queries/`：中英文检索式草案
- `03_raw_results/`：各数据库原始导入结果（只增不删）
- `04_dedup/`：主表与去重副本
- `05_screening/`：标题/摘要筛选、全文筛选、排除理由
- `06_fulltext/`：PDF可得性与合法性登记
- `07_extraction/`：证据提取表
- `08_notes/`：逐篇与主题笔记
- `09_outputs/`：阅读清单、综述提纲、核心文献模板
- `scripts/`：后续自动化脚本

## 后续执行流程
固定流程：
1. 检索
2. 导入
3. 去重
4. 标题/摘要筛选
5. 全文筛选
6. 证据提取
7. 输出清单

## 命名规范
- 文件名优先使用小写与下划线（snake_case）
- 版本化数据建议追加日期：`*_YYYYMMDD.csv`
- 每篇文献建议使用唯一 `paper_id`

## 数据字段说明
核心CSV字段统一如下（顺序保持一致）：
`paper_id,title,authors,year,language,document_type,database,query_string,doi,venue,publisher,url,pdf_status,pdf_url,fulltext_legal,platform_type,airborne_relevance,imaging_relevance,ncs_relevance,algorithm_family,scenario,data_type,core_problem,key_method,main_contribution,limitations,screening_stage,decision,exclusion_reason,evidence_source,verification_status,notes`

字段约束：
- 未核实信息一律标记 `UNVERIFIED` 或留空
- `pdf_status` 必填并限定为：`downloadable / metadata_only / inaccessible / unknown`
- 所有筛选与结论须可追溯到来源链接或导入文件
