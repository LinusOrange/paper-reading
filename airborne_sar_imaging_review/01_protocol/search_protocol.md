# 检索协议（Search Protocol）

## 目标
围绕 airborne SAR imaging 与 NCS 相关研究建立可追溯文献池。

## 数据库顺序
1. IEEE Xplore
2. Web of Science
3. Google Scholar

## 基本流程
1. 在 `02_queries/` 维护查询式版本
2. 分库执行检索并导出
3. 将原始结果放入 `03_raw_results/<source>/`
4. 记录导入日期、检索式、结果数量
5. 合并到 `04_dedup/master_raw.csv`

## 合规与追溯
- 每条记录必须保留来源链接与检索式。
- 未核实信息统一 `UNVERIFIED` 或留空。
- 原始导入文件不覆盖删除。
