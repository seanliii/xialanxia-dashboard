# 用Python批量清洗Excel数据，200行代码搞定95%的需求

## 前言

工作中最常见的数据处理需求是什么？

大概率是：客户给你发来十几个Excel，格式不一，有空行、有重复、日期格式还各不相同。手动处理要两个小时，用Python写个脚本，5分钟跑完。

这篇文章整理了一套完整的Excel批量清洗方案，代码可以直接复制用。

---

## 核心依赖

```bash
pip install pandas openpyxl
```

---

## 一、读取多个Excel文件

```python
from pathlib import Path
import pandas as pd

def load_all_excels(directory: str) -> dict:
    """读取目录下所有 Excel 和 CSV 文件"""
    files = {}
    for path in Path(directory).glob("*.xlsx"):
        files[path.name] = pd.read_excel(path)
    for path in Path(directory).glob("*.csv"):
        files[path.name] = pd.read_csv(path, encoding="utf-8-sig")
    return files
```

---

## 二、去除空行和重复行

```python
def clean_basic(df: pd.DataFrame) -> pd.DataFrame:
    original = len(df)
    df = df.dropna(how="all")       # 删全空行
    df = df.drop_duplicates()       # 删重复行
    print(f"删除了 {original - len(df)} 行无效数据")
    return df
```

---

## 三、统一列名格式

客户给的Excel，列名五花八门：`姓名`、` 姓名 `、`Name`、`name`……

```python
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df
```

---

## 四、日期格式统一

最头疼的问题：同一份数据里有 `2024/1/5`、`2024-01-05`、`20240105` 三种格式混用。

```python
def fix_dates(df: pd.DataFrame, target_format="%Y-%m-%d") -> pd.DataFrame:
    for col in df.columns:
        if "date" in col or "日期" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(target_format)
    return df
```

`errors="coerce"` 会把解析失败的日期变成 `NaT`，不会报错崩溃。

---

## 五、手机号脱敏

```python
import re

def mask_phones(df: pd.DataFrame) -> pd.DataFrame:
    pattern = re.compile(r"1[3-9]\d{9}")

    def do_mask(val):
        if isinstance(val, str):
            return pattern.sub(
                lambda m: m.group()[:3] + "****" + m.group()[-4:],
                val
            )
        return val

    return df.applymap(do_mask)
```

`138****8888` — 前3后4，中间4位打码。

---

## 六、组合成完整流水线

```python
def process_file(input_path: str, output_path: str):
    df = pd.read_excel(input_path)
    
    df = normalize_columns(df)
    df = clean_basic(df)
    df = fix_dates(df)
    df = mask_phones(df)
    
    df.to_excel(output_path, index=False)
    print(f"✅ 已输出：{output_path}")

# 批量处理
for path in Path("./data").glob("*.xlsx"):
    process_file(str(path), f"./output/{path.stem}_cleaned.xlsx")
```

---

## 总结

这5个函数覆盖了绝大多数数据清洗场景：

| 函数 | 解决什么问题 |
|------|------------|
| `load_all_excels` | 批量读取 |
| `clean_basic` | 空行/重复行 |
| `normalize_columns` | 列名不统一 |
| `fix_dates` | 日期格式混乱 |
| `mask_phones` | 敏感数据脱敏 |

完整代码已上传 GitHub：[excel-batch-cleaner](https://github.com/your-username/excel-batch-cleaner)

有具体需求欢迎评论区说，或者闲鱼搜「Python数据处理」找我。
