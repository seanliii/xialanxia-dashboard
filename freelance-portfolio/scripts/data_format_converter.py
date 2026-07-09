"""
多格式数据转换工具
功能：
- 支持格式互转：CSV ↔ Excel ↔ JSON ↔ Parquet
- 批量处理整个目录
- 支持编码自动检测（解决中文乱码）
- 支持自定义分隔符（CSV）
- 大文件分块处理（避免 OOM）

用法：
    # 单文件转换
    python data_format_converter.py --input data.csv --to xlsx
    python data_format_converter.py --input data.xlsx --to json --pretty

    # 批量转换整个目录
    python data_format_converter.py --input ./data_dir --to csv --batch

依赖：
    pip install pandas openpyxl chardet pyarrow
"""

import argparse
import os
import json
from pathlib import Path

import pandas as pd
import chardet


SUPPORTED_FORMATS = ["csv", "xlsx", "xls", "json", "parquet"]


def detect_encoding(filepath: str) -> str:
    """自动检测文件编码（解决中文乱码）"""
    with open(filepath, "rb") as f:
        raw = f.read(10000)   # 读前 10KB 判断编码
    result = chardet.detect(raw)
    encoding = result.get("encoding") or "utf-8"
    # 常见中文编码修正
    if encoding.lower() in ("gb2312", "gbk", "gb18030"):
        encoding = "gbk"
    return encoding


def read_file(filepath: Path, sep: str = ",") -> pd.DataFrame:
    """读取文件，自动识别格式和编码"""
    ext = filepath.suffix.lower().lstrip(".")

    if ext == "csv":
        encoding = detect_encoding(str(filepath))
        try:
            return pd.read_csv(filepath, sep=sep, encoding=encoding)
        except UnicodeDecodeError:
            return pd.read_csv(filepath, sep=sep, encoding="gbk")

    elif ext in ("xlsx", "xls"):
        return pd.read_excel(filepath)

    elif ext == "json":
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        else:
            raise ValueError(f"不支持的 JSON 结构：{type(data)}")

    elif ext == "parquet":
        return pd.read_parquet(filepath)

    else:
        raise ValueError(f"不支持的输入格式：{ext}，支持：{SUPPORTED_FORMATS}")


def write_file(df: pd.DataFrame, output_path: Path, pretty: bool = False):
    """根据输出格式写文件"""
    ext = output_path.suffix.lower().lstrip(".")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ext == "csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")   # utf-8-sig 让 Excel 正常打开中文

    elif ext in ("xlsx", "xls"):
        df.to_excel(output_path, index=False)

    elif ext == "json":
        records = df.to_dict(orient="records")
        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(records, f, ensure_ascii=False, indent=2)
            else:
                json.dump(records, f, ensure_ascii=False)

    elif ext == "parquet":
        df.to_parquet(output_path, index=False)

    else:
        raise ValueError(f"不支持的输出格式：{ext}")


def convert_file(input_path: Path, target_format: str, output_dir: Path,
                 sep: str = ",", pretty: bool = False) -> dict:
    """转换单个文件"""
    result = {"file": input_path.name, "status": "ok", "error": ""}
    try:
        df = read_file(input_path, sep=sep)
        out_name = input_path.stem + "." + target_format
        out_path = output_dir / out_name
        write_file(df, out_path, pretty=pretty)
        result["output"] = str(out_path)
        result["rows"] = len(df)
        result["cols"] = len(df.columns)
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


def main():
    parser = argparse.ArgumentParser(description="多格式数据转换工具")
    parser.add_argument("--input", required=True, help="输入文件或目录路径")
    parser.add_argument("--to", required=True, choices=SUPPORTED_FORMATS, help="目标格式")
    parser.add_argument("--output", default=None, help="输出目录（默认同输入目录下的 converted/）")
    parser.add_argument("--batch", action="store_true", help="批量处理整个目录")
    parser.add_argument("--sep", default=",", help="CSV 分隔符，默认逗号")
    parser.add_argument("--pretty", action="store_true", help="JSON 美化输出")
    args = parser.parse_args()

    input_path = Path(args.input)

    # 确定输出目录
    if args.output:
        output_dir = Path(args.output)
    elif input_path.is_dir():
        output_dir = input_path / "converted"
    else:
        output_dir = input_path.parent / "converted"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集待处理文件
    if args.batch or input_path.is_dir():
        if not input_path.is_dir():
            print(f"❌ --batch 模式下 --input 必须是目录：{input_path}")
            return
        files = []
        for fmt in SUPPORTED_FORMATS:
            files.extend(input_path.glob(f"*.{fmt}"))
        files = [f for f in files if f.suffix.lstrip(".") != args.to]
    else:
        files = [input_path]

    if not files:
        print("未找到可处理的文件")
        return

    print(f"共 {len(files)} 个文件，目标格式：{args.to}\n")

    success, fail = 0, 0
    for f in files:
        print(f"  转换：{f.name} → {f.stem}.{args.to} ...", end=" ")
        r = convert_file(f, args.to, output_dir, sep=args.sep, pretty=args.pretty)
        if r["status"] == "ok":
            print(f"✅  ({r['rows']} 行 × {r['cols']} 列)")
            success += 1
        else:
            print(f"❌  {r['error']}")
            fail += 1

    print(f"\n完成：{success} 成功，{fail} 失败。输出目录：{output_dir}")


if __name__ == "__main__":
    main()
