# 数据处理脚本接单 — 作品集

Python 数据处理工具集，用于自由职业接单展示。

## 项目列表

### 1. Excel 批量数据清洗工具
**文件：** `scripts/excel_batch_cleaner.py`

功能：
- 批量读取目录下所有 Excel/CSV 文件
- 自动去除空行、重复行
- 统一列名格式
- 日期格式标准化（支持多种混合格式）
- 手机号脱敏（138****8888）
- 输出清洗报告

```bash
pip install pandas openpyxl
python scripts/excel_batch_cleaner.py --input ./data --output ./output --mask-phone
```

---

### 2. 自动化报表生成工具
**文件：** `scripts/report_generator.py`

功能：
- 读取销售数据，按日/周/月自动汇总
- 计算环比增长率
- 生成 TOP10 产品排行
- 输出带折线图+柱状图的 Excel 报表

```bash
pip install pandas openpyxl xlsxwriter
python scripts/report_generator.py --input sales.xlsx --output report.xlsx --period month
```

---

### 3. 多格式数据转换工具
**文件：** `scripts/data_format_converter.py`

功能：
- 支持 CSV ↔ Excel ↔ JSON ↔ Parquet 互转
- 自动检测文件编码（解决中文乱码）
- 批量转换整个目录

```bash
pip install pandas openpyxl chardet pyarrow
python scripts/data_format_converter.py --input ./data --to csv --batch
```

---

## 定制服务

有类似需求可以联系：闲鱼搜索「Python数据处理脚本」

定价参考：
- 简单脚本（<50行）：¥199，当天交付
- 中等复杂（带报表/图表）：¥499，1-2天
- 复杂定制（带界面/调度）：¥999起，3-5天
