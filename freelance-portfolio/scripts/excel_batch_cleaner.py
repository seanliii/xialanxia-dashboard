"""
Excel 批量数据清洗工具
功能：
- 批量读取指定目录下所有 .xlsx / .csv 文件
- 自动去除空行、重复行
- 标准化字段名（去除首尾空格、统一小写）
- 支持自定义规则：日期格式统一、手机号脱敏、金额格式化
- 输出清洗报告

用法：
    python excel_batch_cleaner.py --input ./data --output ./output
    python excel_batch_cleaner.py --input ./data --output ./output --mask-phone --date-format "%Y/%m/%d"

依赖：
    pip install pandas openpyxl
"""

import os
import argparse
import pandas as pd
import re
from datetime import datetime
from pathlib import Path


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """标准化列名：去除首尾空格，统一小写，空格替换为下划线"""
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def remove_empty_and_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """去除空行和重复行，返回清洗后的 DataFrame 和统计信息"""
    original_len = len(df)
    df = df.dropna(how="all")           # 删除全空行
    after_empty = len(df)
    df = df.drop_duplicates()           # 删除完全重复行
    after_dup = len(df)

    stats = {
        "removed_empty_rows": original_len - after_empty,
        "removed_duplicate_rows": after_empty - after_dup,
    }
    return df, stats


def mask_phone_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """手机号脱敏：138****8888"""
    phone_pattern = re.compile(r"1[3-9]\d{9}")

    def mask(val):
        if isinstance(val, str):
            return phone_pattern.sub(lambda m: m.group()[:3] + "****" + m.group()[-4:], val)
        return val

    return df.applymap(mask)


def normalize_dates(df: pd.DataFrame, target_format: str = "%Y-%m-%d") -> pd.DataFrame:
    """自动识别日期列并统一格式"""
    for col in df.columns:
        if "date" in col or "时间" in col or "日期" in col:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(target_format)
            except Exception:
                pass
    return df


def process_file(filepath: Path, output_dir: Path, mask_phone: bool, date_format: str) -> dict:
    """处理单个文件，返回处理报告"""
    report = {"file": filepath.name, "status": "ok", "errors": []}

    try:
        # 读取文件
        if filepath.suffix == ".csv":
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        else:
            df = pd.read_excel(filepath)

        report["original_rows"] = len(df)
        report["original_cols"] = len(df.columns)

        # 清洗流程
        df = clean_column_names(df)
        df, stats = remove_empty_and_duplicates(df)
        report.update(stats)

        if mask_phone:
            df = mask_phone_numbers(df)

        df = normalize_dates(df, date_format)

        report["final_rows"] = len(df)

        # 输出
        out_path = output_dir / (filepath.stem + "_cleaned.xlsx")
        df.to_excel(out_path, index=False)
        report["output"] = str(out_path)

    except Exception as e:
        report["status"] = "error"
        report["errors"].append(str(e))

    return report


def main():
    parser = argparse.ArgumentParser(description="Excel/CSV 批量数据清洗工具")
    parser.add_argument("--input", required=True, help="输入目录路径")
    parser.add_argument("--output", required=True, help="输出目录路径")
    parser.add_argument("--mask-phone", action="store_true", help="开启手机号脱敏")
    parser.add_argument("--date-format", default="%Y-%m-%d", help="日期输出格式，默认 %%Y-%%m-%%d")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 扫描文件
    files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls")) + list(input_dir.glob("*.csv"))
    if not files:
        print(f"未找到任何 Excel/CSV 文件：{input_dir}")
        return

    print(f"发现 {len(files)} 个文件，开始处理...\n")

    reports = []
    for f in files:
        print(f"  处理：{f.name} ...")
        report = process_file(f, output_dir, args.mask_phone, args.date_format)
        reports.append(report)
        if report["status"] == "ok":
            print(f"  ✅ 完成：{report['original_rows']} 行 → {report['final_rows']} 行"
                  f"（删空行 {report['removed_empty_rows']}，删重复 {report['removed_duplicate_rows']}）")
        else:
            print(f"  ❌ 失败：{report['errors']}")

    # 生成汇总报告
    print("\n" + "=" * 50)
    print(f"处理完成：{sum(1 for r in reports if r['status'] == 'ok')}/{len(reports)} 成功")
    print(f"输出目录：{output_dir}")

    # 写入报告文件
    report_path = output_dir / f"clean_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w", encoding="utf-8") as fp:
        for r in reports:
            fp.write(str(r) + "\n")
    print(f"清洗报告：{report_path}")


if __name__ == "__main__":
    main()
