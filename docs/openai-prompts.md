# SAR Demo OpenAI Prompt 设计

## 1. `sar_paper_summary_prompt`

用途：生成单篇论文的结构化摘要。

输出字段：

- `problem`
- `method`
- `scenario`
- `contributions`
- `speed_related_issue`
- `squint_related_issue`
- `datasets_or_simulation`
- `metrics`
- `limitations`

## 2. `sar_entity_extract_prompt`

用途：从全文中提取关键 SAR 场景与方法实体。

输出字段：

- `scenarios`
- `methods`
- `issues`
- `evidence`

## 3. `sar_topic_tag_prompt`

用途：为论文补全可检索标签。

推荐标签域：

- `airborne-sar`
- `high-resolution`
- `high-speed`
- `large-squint`
- `motion-compensation`
- `autofocus`
- `rcmc`
- `omega-k`

## 4. `sar_qa_prompt`

用途：针对高速场景、大斜视场景以及运动补偿等问题，基于候选论文片段给出 grounded answer。

要求：

- 只能基于候选文献回答；
- 回答必须指出适用场景；
- 回答必须总结方法差异；
- 输出需要可回溯到论文编号。
