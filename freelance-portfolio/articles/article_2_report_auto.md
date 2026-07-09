# 老板要的月报，用Python 10分钟自动生成（含折线图+柱状图）

## 前言

每个月手动做报表，从Excel里复制数据、画图表、调格式，一搞两三小时。

这篇文章教你用Python + pandas + xlsxwriter，把这件事一劳永逸地自动化。输入原始数据，输出带图表的专业报表，全程代码跑，你去喝茶。

---

## 效果预览

运行一条命令：
```bash
python report_generator.py --input sales.xlsx --output monthly_report.xlsx --period month
```

生成的报表包含4个Sheet：
- **原始数据**：原样保留
- **销售趋势**：按月汇总 + 环比增长率 + 折线图
- **TOP产品**：销售额排行 + 柱状图
- **汇总统计**：总计、平均、最大值、最小值

---

## 核心代码

### 1. 按时间聚合

```python
def aggregate_by_month(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    monthly = df.set_index("date")["amount"].resample("ME").sum().reset_index()
    monthly.columns = ["month", "total_amount"]
    
    # 计算环比增长率
    monthly["mom_growth"] = monthly["total_amount"].pct_change() * 100
    monthly["mom_growth"] = monthly["mom_growth"].round(2)
    return monthly
```

### 2. 用 xlsxwriter 插入图表

```python
import pandas as pd

def write_with_chart(df: pd.DataFrame, output_path: str):
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="销售趋势", index=False)
        
        workbook = writer.book
        worksheet = writer.sheets["销售趋势"]
        
        # 创建折线图
        chart = workbook.add_chart({"type": "line"})
        n = len(df)
        chart.add_series({
            "name": "月销售额",
            "categories": ["销售趋势", 1, 0, n, 0],   # A列：月份
            "values":     ["销售趋势", 1, 1, n, 1],   # B列：金额
            "line": {"color": "#2E75B6", "width": 2.5},
        })
        chart.set_title({"name": "月度销售趋势"})
        chart.set_size({"width": 600, "height": 300})
        
        # 插入图表到 E2 单元格
        worksheet.insert_chart("E2", chart)
```

关键点：
- `xlsxwriter` 的图表引用格式是 `[sheet_name, 起始行, 起始列, 结束行, 结束列]`，**行列都从0开始，0行是表头**
- `resample("ME")` 是按月末对齐，旧版 pandas 用 `"M"`

### 3. TOP产品柱状图

```python
# 按产品汇总销售额
top10 = df.groupby("product")["amount"].sum().sort_values(ascending=False).head(10)

# 写入 Excel 并加柱状图
top10.to_excel(writer, sheet_name="TOP产品")
chart2 = workbook.add_chart({"type": "bar"})
chart2.add_series({
    "name": "销售额",
    "categories": ["TOP产品", 1, 0, 10, 0],
    "values":     ["TOP产品", 1, 1, 10, 1],
    "fill": {"color": "#ED7D31"},
})
writer.sheets["TOP产品"].insert_chart("D2", chart2)
```

---

## 依赖安装

```bash
pip install pandas openpyxl xlsxwriter
```

注意：同一个 ExcelWriter 不能同时用 `openpyxl` 和 `xlsxwriter` 引擎。要插图表，用 `xlsxwriter`；要读已有文件，先用 `openpyxl` 读，再用 `xlsxwriter` 写新文件。

---

## 完整代码

GitHub 地址：[report-generator](https://github.com/your-username/report-generator)

---

## 延伸：定时自动跑

配合 cron（Linux/Mac）或任务计划（Windows），可以设置每月1号自动跑：

```bash
# crontab -e
# 每月1号 9:00 自动生成上月报表
0 9 1 * * python /path/to/report_generator.py --input /data/sales.xlsx --output /reports/$(date +\%Y\%m)_report.xlsx
```

这样报表直接出现在目录里，连命令都不用敲了。
