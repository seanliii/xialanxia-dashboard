#!/usr/bin/env python3
"""
self_health_check.py — 小蓝虾自检脚本
每天自动检查健康状态，有问题主动大象通知掌管🦞的神

检查项目：
1. 外网连通性
2. AISA API 余额
3. 持仓止损状态（Stooq 实时价格）
4. 群机器人状态（通过发送测试）
5. Dashboard 最后更新时间

用法：python3 self_health_check.py
Cron：每天 08:00 自动跑
"""

import os
import json
import subprocess
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
POSITIONS_FILE = WORKSPACE / "portfolio/positions.json"
DASHBOARD_HTML = WORKSPACE / "dashboard/dashboard.html"
AISA_API_KEY = os.environ.get("AISA_API_KEY", "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41")
DAXIANG_OWNER_ID = "2872173767"

# openclaw message 命令（用于发大象）
def send_daxiang(msg: str):
    """通过 openclaw 发大象消息给掌管🦞的神"""
    try:
        result = subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "daxiang",
             "-t", DAXIANG_OWNER_ID,
             "-m", msg],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"[发送stderr] {result.stderr[:200]}")
        return result.returncode == 0
    except Exception as e:
        print(f"[发送失败] {e}")
        return False

# ── 检查1：外网连通性 ──────────────────────────────────
def check_network() -> dict:
    """ping 8.8.8.8，测试外网连通"""
    try:
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "2", "8.8.8.8"],
            capture_output=True, text=True, timeout=10
        )
        loss_line = [l for l in result.stdout.split('\n') if 'packet loss' in l]
        if loss_line and '100%' in loss_line[0]:
            return {"ok": False, "msg": "外网断线（100% packet loss）"}
        elif loss_line and '0%' in loss_line[0]:
            return {"ok": True, "msg": "外网正常"}
        else:
            return {"ok": False, "msg": f"外网异常: {loss_line}"}
    except Exception as e:
        return {"ok": False, "msg": f"ping 失败: {e}"}

# ── 检查2：AISA API 余额 ──────────────────────────────
def check_aisa_balance() -> dict:
    """查询 AISA API 余额"""
    try:
        resp = requests.get(
            "https://api.aisa.one/apis/v1/user/balance",
            headers={"Authorization": f"Bearer {AISA_API_KEY}"},
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            balance = data.get("balance", data.get("credits", "未知"))
            try:
                bal_float = float(balance)
                if bal_float < 1.0:
                    return {"ok": False, "msg": f"AISA余额不足 ${bal_float:.2f}，需充值 → https://api.aisa.one"}
                else:
                    return {"ok": True, "msg": f"AISA余额 ${bal_float:.2f}"}
            except:
                return {"ok": True, "msg": f"AISA余额 {balance}"}
        elif resp.status_code == 403:
            return {"ok": False, "msg": "AISA API 403（余额耗尽或Key失效），需充值 → https://api.aisa.one"}
        else:
            return {"ok": False, "msg": f"AISA API 异常 HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"ok": None, "msg": "AISA 检查跳过（外网不通）"}
    except Exception as e:
        return {"ok": None, "msg": f"AISA 检查异常: {e}"}

# ── 检查3：持仓止损状态 ──────────────────────────────
def check_stop_losses() -> dict:
    """从 Stooq 获取实时价格，检查止损"""
    if not POSITIONS_FILE.exists():
        return {"ok": True, "msg": "positions.json 不存在，跳过"}

    with open(POSITIONS_FILE) as f:
        data = json.load(f)

    positions = data.get("positions", [])
    triggered = []
    warnings = []  # 缓冲 < 5%
    failed_tickers = []
    updated_positions = []

    for pos in positions:
        ticker = pos.get("ticker", "")
        stop_loss = pos.get("stop_loss")
        if not ticker or not stop_loss:
            updated_positions.append(pos)
            continue

        # BTC 特殊处理
        stooq_ticker = "BTCUSD" if ticker == "BTC-USD" else f"{ticker}.US"

        try:
            url = f"https://stooq.com/q/l/?s={stooq_ticker}&f=sd2t2ohlcv&h&e=csv"
            resp = requests.get(url, timeout=8)
            lines = resp.text.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split(',')
                close_price = float(parts[6]) if len(parts) > 6 else None
                if close_price and close_price > 0:
                    pos["current_price"] = close_price
                    pos["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

                    buffer_pct = (close_price - stop_loss) / close_price * 100
                    if close_price <= stop_loss:
                        triggered.append(f"🔴 **{ticker}** 止损触发！当前${close_price:.2f} ≤ 止损${stop_loss}（**立即平仓**）")
                    elif buffer_pct < 5:
                        warnings.append(f"⚠️ {ticker} 缓冲仅 {buffer_pct:.1f}%（${close_price:.2f}，止损${stop_loss}）")
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(ticker)
        except requests.exceptions.ConnectionError:
            failed_tickers.append(ticker)
        except Exception as e:
            failed_tickers.append(f"{ticker}({e})")

        updated_positions.append(pos)
        time.sleep(0.3)  # 避免 Stooq 限速

    # 写回更新后的价格
    data["positions"] = updated_positions
    with open(POSITIONS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    issues = triggered + warnings
    if triggered:
        return {"ok": False, "msg": "\n".join(issues), "triggered": triggered, "warnings": warnings, "failed": failed_tickers}
    elif warnings:
        return {"ok": "warn", "msg": "\n".join(issues), "triggered": [], "warnings": warnings, "failed": failed_tickers}
    else:
        return {"ok": True, "msg": f"全部持仓止损安全（{len(positions)}只）", "triggered": [], "warnings": [], "failed": failed_tickers}

# ── 检查4：Dashboard 更新时间 ──────────────────────────
def check_dashboard_freshness() -> dict:
    """检查 Dashboard HTML 是否在过去24小时内更新过"""
    if not DASHBOARD_HTML.exists():
        return {"ok": False, "msg": "dashboard.html 不存在！"}

    mtime = DASHBOARD_HTML.stat().st_mtime
    last_modified = datetime.fromtimestamp(mtime)
    hours_ago = (datetime.now() - last_modified).total_seconds() / 3600

    if hours_ago > 26:
        return {"ok": False, "msg": f"Dashboard 超过 {hours_ago:.0f}h 未更新（最后: {last_modified.strftime('%m-%d %H:%M')}）"}
    else:
        return {"ok": True, "msg": f"Dashboard 正常（{hours_ago:.0f}h 前更新）"}

# ── 主流程 ────────────────────────────────────────────
def main():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*50}")
    print(f"🦐 小蓝虾自检 — {now_str}")
    print(f"{'='*50}")

    results = {}

    # 1. 网络
    print("\n[1/4] 检查外网...")
    results["network"] = check_network()
    print(f"  → {results['network']['msg']}")

    # 2. AISA（仅网络通时）
    print("\n[2/4] 检查 AISA API...")
    if results["network"]["ok"]:
        results["aisa"] = check_aisa_balance()
    else:
        results["aisa"] = {"ok": None, "msg": "AISA 跳过（外网不通）"}
    print(f"  → {results['aisa']['msg']}")

    # 3. 持仓止损
    print("\n[3/4] 检查持仓止损...")
    if results["network"]["ok"]:
        results["stops"] = check_stop_losses()
    else:
        results["stops"] = {"ok": None, "msg": "止损检查跳过（外网不通，使用缓存价格）"}
    print(f"  → {results['stops']['msg']}")

    # 4. Dashboard 新鲜度
    print("\n[4/4] 检查 Dashboard...")
    results["dashboard"] = check_dashboard_freshness()
    print(f"  → {results['dashboard']['msg']}")

    # ── 汇总 & 决定是否报警 ────────────────────────────
    critical_issues = []
    warn_issues = []

    if not results["network"]["ok"]:
        critical_issues.append(f"🔌 {results['network']['msg']}")

    if results["aisa"].get("ok") is False:
        critical_issues.append(f"💸 {results['aisa']['msg']}")

    stops = results["stops"]
    if stops.get("ok") is False:
        for t in stops.get("triggered", []):
            critical_issues.append(t)
        for w in stops.get("warnings", []):
            warn_issues.append(w)
    elif stops.get("ok") == "warn":
        for w in stops.get("warnings", []):
            warn_issues.append(w)

    if not results["dashboard"]["ok"]:
        warn_issues.append(f"📊 {results['dashboard']['msg']}")

    # ── 发送大象通知 ──────────────────────────────────
    if critical_issues or warn_issues:
        lines = [f"**🦐 小蓝虾自检报告** — {now_str}\n"]

        if critical_issues:
            lines.append("**🚨 紧急问题（需要处理）：**")
            lines.extend(critical_issues)

        if warn_issues:
            lines.append("\n**⚠️ 警告（关注）：**")
            lines.extend(warn_issues)

        lines.append("\n---")
        # 给出自救建议
        if not results["network"]["ok"]:
            lines.append("💡 外网断线 → 请检查网络/代理，或告诉我恢复了我立即开干")
        if results["aisa"].get("ok") is False:
            lines.append("💡 AISA充值 → https://api.aisa.one（建议充$5-10）")
        if stops.get("triggered"):
            lines.append("💡 止损触发 → 已更新positions.json，请确认是否执行平仓")

        msg = "\n".join(lines)
        print(f"\n{'='*50}")
        print("📢 发送大象通知...")
        print(msg)
        success = send_daxiang(msg)
        print(f"  → {'✅ 发送成功' if success else '❌ 发送失败（openclaw命令问题）'}")
    else:
        print(f"\n✅ 全部正常，无需报警")
        # 全好的时候只打印日志，不发消息（避免骚扰）

    # ── 写自检日志 ────────────────────────────────────
    log_file = WORKSPACE / "memory/health_check_log.json"
    log_file.parent.mkdir(exist_ok=True)

    log_entry = {
        "timestamp": now_str,
        "network_ok": results["network"]["ok"],
        "aisa_ok": results["aisa"]["ok"],
        "stops_ok": results["stops"]["ok"],
        "dashboard_ok": results["dashboard"]["ok"],
        "critical_count": len(critical_issues),
        "warn_count": len(warn_issues)
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except:
            logs = []
    logs.append(log_entry)
    logs = logs[-30:]  # 保留最近30条
    log_file.write_text(json.dumps(logs, indent=2, ensure_ascii=False))

    print(f"\n日志已写入: {log_file}")
    print(f"{'='*50}\n")

    return len(critical_issues) == 0

if __name__ == "__main__":
    ok = main()
    exit(0 if ok else 1)
