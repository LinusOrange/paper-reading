# 质量规则（Quality Rules）

## 数据真实性
- 禁止虚构任何文献信息。
- 无法核实字段一律 `UNVERIFIED` 或留空。

## PDF状态
- 每条文献必须标注 `pdf_status`：
  - `downloadable`
  - `metadata_only`
  - `inaccessible`
  - `unknown`

## 冲突处理
- 多来源冲突时，保留冲突并标明来源，不做主观裁决。

## 可追溯性
- 每条筛选/提取结果必须可追溯至来源页面或导入文件。
