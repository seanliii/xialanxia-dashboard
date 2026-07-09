"""
自动化报表生成工具
功能：
- 读取 Excel/CSV 销售数据
- 自动计算：总销售额、环比增长、TOP10 产品、各区域汇总
- 生成带图表的 Excel 报表（折线图 + 柱状图）
- 支持按日/周/月聚合

用法：
    python report_generator.py --input sales_data.xlsx --output report.xlsx --period month

依赖：
    pip install pandas openpyxl xlsxwriter
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def load_data(filepath: str) -> pd.DataFrame:
    """加载数据，自动判断格式"""
    path = Path(filepath)
    if path.suffix == ".csv":
        df = pd.read_csv(filepath, encoding="utf-8-sig")
    else:
        df = pd.read_excel(filepath)

    # 自动识别日期列
    for col in df.columns:
        if "date" in col.lower() or "日期" in col or "时间" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.rename(columns={col: "date"})
            break

    return df


def aggregate_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """按时间周期聚合"""
    if "date" not in df.columns:
        return df

    freq_map = {"day": "D", "week": "W", "month": "ME"}
    freq = freq_map.get(period, "ME")

    # 找销售额列（自动识别）
    amount_col = None
    for col in df.columns:
        if any(k in col.lower() for k in ["amount", "sales", "金额", "销售额", "收入"]):
            amount_col = col
            break

    if not amount_col:
        # 取第一个数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            amount_col = numeric_cols[0]

    if amount_col:
        grouped = df.set_index("date")[amount_col].resample(freq).sum().reset_index()
        grouped.columns = ["period", "total_amount"]

        # 计算环比增长率
        grouped["mom_growth"] = grouped["total_amount"].pct_change() * 100
        grouped["mom_growth"] = grouped["mom_growth"].round(2)
        return grouped

    return df


def get_top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """获取 TOP N 产品"""
    product_col = None
    amount_col = None

    for col in df.columns:
        if any(k in col.lower() for k in ["product", "item", "商品", "产品", "名称"]):
            product_col = col
        if any(k in col.lower() for k in ["amount", "sales", "金额", "销售额"]):
            amount_col = col

    if product_col and amount_col:
        return (df.groupby(product_col)[amount_col]
                  .sum()
                  .sort_values(ascending=False)
                  .head(n)
                  .reset_index())
    return pd.DataFrame()


def generate_report(input_file: str, output_file: str, period: str = "month"):
    """生成完整报表"""
    print(f"读取数据：{input_file}")
    df = load_data(input_file)
    print(f"数据行数：{len(df)}")

    # 创建 Excel Writer（xlsxwriter 引擎支持图表）
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        workbook = writer.book

        # ── Sheet 1：原始数据 ──
        df.to_excel(writer, sheet_name="原始数据", index=False)

        # ── Sheet 2：时间趋势 ──
        trend = aggregate_by_period(df, period)
        if not trend.empty:
            trend.to_excel(writer, sheet_name="销售趋势", index=False)

            # 添加折线图
            ws = writer.sheets["销售趋势"]
            chart = workbook.add_chart({"type": "line"})
            n_rows = len(trend)
            chart.add_series({
                "name": "销售额",
                "categories": ["销售趋势", 1, 0, n_rows, 0],
                "values":     ["销售趋势", 1, 1, n_rows, 1],
                "line": {"color": "#2E75B6", "width": 2.5},
            })
            chart.set_title({"name": f"销售趋势（按{period}）"})
            chart.set_x_axis({"name": "时间"})
            chart.set_y_axis({"name": "销售额"})
            chart.set_size({"width": 600, "height": 300})
            ws.insert_chart("E2", chart)

        # ── Sheet 3：TOP 产品 ──
        top = get_top_products(df)
        if not top.empty:
            top.to_excel(writer, sheet_name="TOP产品", index=False)

            ws = writer.sheets["TOP产品"]
            chart2 = workbook.add_chart({"type": "bar"})
            n_rows = len(top)
            chart2.add_series({
                "name": "销售额",
                "categories": ["TOP产品", 1, 0, n_rows, 0],
                "values":     ["TOP产品", 1, 1, n_rows, 1],
                "fill": {"color": "#ED7D31"},
            })
            chart2.set_title({"name": "TOP 产品销售额排行"})
            chart2.set_size({"width": 600, "height": 400})
            ws.insert_chart("D2", chart2)

        # ── Sheet 4：汇总统计 ──
        summary_data = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            summary_data[col] = {
                "总计": df[col].sum(),
                "平均": round(df[col].mean(), 2),
                "最大值": df[col].max(),
                "最小值": df[col].min(),
                "非空行数": df[col].count(),
            }
        if summary_data:
            summary_df = pd.DataFrame(summary_data).T
            summary_df.to_excel(writer, sheet_name="汇总统计")

    print(f"✅ 报表已生成：{output_file}")


def main():
    parser = argparse.ArgumentParser(description="自动化销售报表生成工具")
    parser.add_argument("--input", required=True, help="输入数据文件（Excel 或 CSV）")
    parser.add_argument("--output", default="report.xlsx", help="输出报表文件名")
    parser.add_argument("--period", choices=["day", "week", "month"], default="month",
                        help="时间聚合粒度（day/week/month），默认 month")
    args = parser.parse_args()

    generate_report(args.input, args.output, args.period)


if __name__ == "__main__":
    main()
