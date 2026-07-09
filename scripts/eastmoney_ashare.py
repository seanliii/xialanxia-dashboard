#!/usr/bin/env python3
"""
A股实时行情模块 — 接入 portfolio_scanner 的 A 股价格源
数据来源：新浪财经 API（免费、实时、延迟几分钟）

用法：
  1. 作为模块导入：from eastmoney_ashare import get_ashare_price, get_ashare_batch, get_ashare_monitor
  2. 独立运行：python3 eastmoney_ashare.py 600519 000001 688981

支持：
  - 沪市（sh）：600xxx, 601xxx, 603xxx, 688xxx
  - 深市（sz）：000xxx, 001xxx, 002xxx, 003xxx, 300xxx, 301xxx
  - 北交所（bj）：8xxxxx, 4xxxxx

A 股代码自动识别市场前缀（sh/sz/bj），用户只需输入纯数字代码。
"""

import re
import sys
import json
import urllib.request
from datetime import datetime

# === 核心配置 ===
SINA_API = "http://hq.sinajs.cn/list={}"
HEADERS = {"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}


def _code_to_sina(code: str) -> str:
    """A股代码 → 新浪格式（sh600519 / sz000001 / bj830799）"""
    code = code.strip().upper().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    # 如果已经带前缀
    if code.lower().startswith(("sh", "sz", "bj")):
        return code.lower()
    # 自动判断市场
    if code.startswith(("6", "9")):
        return f"sh{code}"
    elif code.startswith(("0", "2", "3")):
        return f"sz{code}"
    elif code.startswith(("8", "4")):
        return f"bj{code}"
    else:
        return f"sh{code}"  # 默认沪市


def _parse_sina_line(line: str) -> dict:
    """解析新浪行情返回的一行数据"""
    # var hq_str_sh600519="贵州茅台,1287.000,1290.200,1285.880,..."
    m = re.match(r'var hq_str_(\w+)="(.*)";?', line.strip())
    if not m or not m.group(2):
        return None

    sina_code = m.group(1)
    fields = m.group(2).split(",")

    if len(fields) < 32:
        return None

    try:
        result = {
            "code": sina_code[2:],  # 纯数字
            "sina_code": sina_code,
            "name": fields[0],
            "open": float(fields[1]) if fields[1] else 0,
            "prev_close": float(fields[2]) if fields[2] else 0,
            "price": float(fields[3]) if fields[3] else 0,
            "high": float(fields[4]) if fields[4] else 0,
            "low": float(fields[5]) if fields[5] else 0,
            "volume": int(float(fields[8])) if fields[8] else 0,  # 成交量（股）
            "amount": float(fields[9]) if fields[9] else 0,  # 成交额（元）
            "date": fields[30] if len(fields) > 30 else "",
            "time": fields[31] if len(fields) > 31 else "",
        }

        # 计算涨跌
        if result["prev_close"] > 0 and result["price"] > 0:
            result["change"] = result["price"] - result["prev_close"]
            result["change_pct"] = (result["change"] / result["prev_close"]) * 100
        else:
            result["change"] = 0
            result["change_pct"] = 0

        # 成交量转万股，成交额转亿
        result["volume_wan"] = round(result["volume"] / 10000, 2)
        result["amount_yi"] = round(result["amount"] / 100000000, 2)

        return result
    except (ValueError, IndexError):
        return None


def get_ashare_price(code: str) -> dict:
    """
    获取单只 A 股实时价格
    
    Args:
        code: 股票代码（纯数字或带前缀均可）
    
    Returns:
        dict: {code, name, price, change, change_pct, high, low, volume_wan, amount_yi, ...}
        None: 获取失败
    """
    sina_code = _code_to_sina(code)
    url = SINA_API.format(sina_code)

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            # 新浪返回 GBK 编码
            data = resp.read().decode("gbk", errors="replace")
    except Exception as e:
        return None

    for line in data.strip().split("\n"):
        result = _parse_sina_line(line)
        if result and result["price"] > 0:
            return result
    return None


def get_ashare_batch(codes: list) -> dict:
    """
    批量获取 A 股实时价格
    
    Args:
        codes: 股票代码列表
    
    Returns:
        dict: {code: {price_data}, ...}  获取失败的不在结果中
    """
    if not codes:
        return {}

    sina_codes = [_code_to_sina(c) for c in codes]
    url = SINA_API.format(",".join(sina_codes))

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("gbk", errors="replace")
    except Exception as e:
        print(f"❌ 批量获取失败: {e}")
        return {}

    results = {}
    for line in data.strip().split("\n"):
        parsed = _parse_sina_line(line)
        if parsed and parsed["price"] > 0:
            results[parsed["code"]] = parsed

    return results


def get_ashare_monitor(codes: list, alert_pct: float = 5.0) -> list:
    """
    监控 A 股持仓，超过阈值报警
    
    Args:
        codes: 股票代码列表
        alert_pct: 涨跌幅报警阈值（默认5%）
    
    Returns:
        list: 触发报警的股票列表
    """
    prices = get_ashare_batch(codes)
    alerts = []

    for code, data in prices.items():
        if abs(data["change_pct"]) >= alert_pct:
            alerts.append({
                "code": code,
                "name": data["name"],
                "price": data["price"],
                "change_pct": data["change_pct"],
                "alert_type": "涨停预警" if data["change_pct"] > 0 else "跌停预警"
            })

    return alerts


def format_quote(data: dict) -> str:
    """格式化输出单只股票行情"""
    arrow = "📈" if data["change_pct"] >= 0 else "📉"
    sign = "+" if data["change"] >= 0 else ""
    return (
        f'{arrow} **{data["name"]}** ({data["code"]})\n'
        f'   💰 现价: ¥{data["price"]:.2f}  {sign}{data["change"]:.2f} ({sign}{data["change_pct"]:.2f}%)\n'
        f'   📊 最高: ¥{data["high"]:.2f}  最低: ¥{data["low"]:.2f}\n'
        f'   📦 成交: {data["volume_wan"]:.0f}万股 / ¥{data["amount_yi"]:.2f}亿\n'
        f'   ⏰ {data["date"]} {data["time"]}'
    )


# === 独立运行 ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 eastmoney_ashare.py <代码1> [代码2] ...")
        print("示例: python3 eastmoney_ashare.py 600519 000001 688981")
        sys.exit(1)

    codes = sys.argv[1:]
    print(f"🔍 查询 {len(codes)} 只 A 股行情...\n")

    if len(codes) == 1:
        data = get_ashare_price(codes[0])
        if data:
            print(format_quote(data))
        else:
            print(f"❌ 获取失败: {codes[0]}")
    else:
        results = get_ashare_batch(codes)
        for code in codes:
            pure_code = code.replace("sh", "").replace("sz", "").replace("bj", "")
            if pure_code in results:
                print(format_quote(results[pure_code]))
                print()
            else:
                print(f"❌ 获取失败: {code}\n")

    # 监控示例
    alerts = get_ashare_monitor(codes)
    if alerts:
        print("\n⚠️ === 异动报警 ===")
        for a in alerts:
            print(f'  {a["alert_type"]}: {a["name"]}({a["code"]}) {a["change_pct"]:+.2f}%')
