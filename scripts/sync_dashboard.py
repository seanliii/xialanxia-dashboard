#!/usr/bin/env python3
"""
sync_dashboard.py — 从 structure.json 读取实时数据，全量刷新 dashboard.html

覆盖所有联动点：
1. 顶部汇总卡（总资产 / 各账户总资产 / 持仓数 / 现金）
2. 各账户卡头部（总资产 / 已投入 / 现金 / 持仓数 / 收益）
3. 各账户持仓表格（当前价 / 持仓成本当前值 / 浮动盈亏 / 已持天数 / 进度条）
4. 三账户对比表汇总行
5. 股价更新时间戳

价格获取：Yahoo Finance quoteSummary（免费，支持全部美股）
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
STRUCTURE_FILE = f"{WORKSPACE}/portfolio/accounts/structure.json"
DASHBOARD_FILE = f"{WORKSPACE}/dashboard/dashboard.html"
PUSH_SCRIPT = f"{WORKSPACE}/scripts/push_dashboard_to_github.sh"

# ─── 1. 获取实时股价 ───────────────────────────────────────────────────────────

def get_prices_yahoo(tickers: list[str]) -> dict[str, float]:
    """用 Yahoo Finance quoteSummary API 批量获取股价（免费，无需 key）"""
    prices = {}
    for ticker in tickers:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
            cmd = ["curl", "-s", "-L", "--max-time", "10",
                   "-H", "User-Agent: Mozilla/5.0",
                   url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            data = json.loads(result.stdout)
            price = (data["chart"]["result"][0]["meta"]
                     .get("regularMarketPrice")
                     or data["chart"]["result"][0]["meta"].get("previousClose"))
            if price:
                prices[ticker] = float(price)
                print(f"  {ticker}: ${price:.4f}")
            else:
                print(f"  {ticker}: price not found in Yahoo response")
        except Exception as e:
            print(f"  {ticker}: Yahoo failed ({e})")
    return prices


def get_prices_stooq(tickers: list[str]) -> dict[str, float]:
    """备用：Stooq 获取股价"""
    prices = {}
    for ticker in tickers:
        try:
            url = f"https://stooq.com/q/l/?s={ticker.lower()}.us&f=sd2t2ohlcv&h&e=csv"
            cmd = ["curl", "-s", "--max-time", "10", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                fields = lines[1].split(",")
                close = float(fields[6]) if len(fields) > 6 else 0
                if close > 0:
                    prices[ticker] = close
                    print(f"  {ticker} (stooq): ${close:.4f}")
        except Exception as e:
            print(f"  {ticker}: Stooq failed ({e})")
    return prices


def get_all_prices(tickers: list[str]) -> dict[str, float]:
    """Yahoo 优先，失败的用 Stooq 补"""
    print(f"[价格] 获取 {len(tickers)} 只股票实时价格...")
    prices = get_prices_yahoo(tickers)
    missing = [t for t in tickers if t not in prices or prices[t] == 0]
    if missing:
        print(f"[价格] Yahoo 缺失 {missing}，用 Stooq 补充...")
        fallback = get_prices_stooq(missing)
        prices.update(fallback)
    return prices


# ─── 2. 更新 structure.json ───────────────────────────────────────────────────

def update_structure(data: dict, prices: dict) -> dict:
    """用最新价格更新 structure.json 中所有持仓的 current_price / current_value / unrealized_pnl"""
    today = date.today()
    
    for acc_id, acc in data["accounts"].items():
        total_invested = 0
        for pos in acc.get("positions", []):
            ticker = pos["ticker"]
            if ticker in prices and prices[ticker] > 0:
                pos["current_price"] = round(prices[ticker], 4)
            
            curr_price = pos.get("current_price", pos["entry_price"])
            shares = pos["shares"]
            cost = pos["cost_basis"]
            
            pos["current_value"] = round(curr_price * shares, 2)
            pos["unrealized_pnl"] = round(pos["current_value"] - cost, 2)
            pos["unrealized_pnl_pct"] = round((pos["unrealized_pnl"] / cost) * 100, 2)
            
            # 更新持仓天数
            try:
                entry_date = date.fromisoformat(pos["entry_date"])
                held = (today - entry_date).days
                pos["held_days"] = held
                target_days = pos.get("hold_days_target", 30)
                pos["hold_days_remaining"] = max(0, target_days - held)
                pos["hold_progress_pct"] = min(100, round(held / target_days * 100))
            except:
                pass
            
            total_invested += pos["current_value"]
        
        # 更新账户总资产
        cash = acc.get("cash", 0)
        total = cash + total_invested
        acc["total_assets"] = round(total, 2)
        acc["total_invested"] = round(total_invested, 2)
        
        # 计算总收益
        total_cost = sum(p["cost_basis"] for p in acc.get("positions", []))
        acc["total_pnl"] = round(total_invested - total_cost, 2)
        acc["total_pnl_pct"] = round((total_invested - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0
    
    return data


# ─── 3. 生成持仓行 HTML ───────────────────────────────────────────────────────

def pnl_html(pnl: float, pnl_pct: float) -> str:
    color = "#2dd4bf" if pnl >= 0 else "#f87171"
    sign = "+" if pnl >= 0 else ""
    return f'<span style="color:{color};font-weight:700">{sign}${abs(pnl):,.0f} ({sign}{pnl_pct:.1f}%)</span>'


def progress_bar(progress: int, color: str = "#6c63ff") -> str:
    width = min(100, max(0, progress))
    return (f'<div style="background:#1e1e33;border-radius:4px;height:6px;width:80px;'
            f'display:inline-block;vertical-align:middle">'
            f'<div style="background:{color};width:{width}%;height:6px;border-radius:4px"></div></div>')


def institutional_row(pos: dict) -> str:
    pnl = pos["unrealized_pnl"]
    pnl_pct = pos["unrealized_pnl_pct"]
    held = pos.get("held_days", 0)
    target_days = pos.get("hold_days_target", 45)
    progress = pos.get("hold_progress_pct", 0)
    target_date = pos.get("target_date_est", "—")
    signal = pos.get("signal_strength", "—")
    signal_color = "#f87171" if "S" in signal else ("#fbbf24" if "A" in signal else "#94a3b8")
    
    # target upside %
    target_price = pos.get("target_price", 0)
    entry_price = pos["entry_price"]
    target_upside = round((target_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    
    # thesis — truncate from full string
    thesis = pos.get("thesis", "")
    thesis_short = thesis[:60] + "…" if len(thesis) > 60 else thesis
    
    return f"""<tr data-ticker="{pos['ticker']}" data-entry="{pos['entry_price']}" data-shares="{pos['shares']}" data-entry-date="{pos['entry_date']}" data-target-days="{target_days}">
  <td><b style="font-size:13px">{pos['ticker']}</b><br><span style="font-size:10px;color:#94a3b8">{pos.get('company','')}</span></td>
  <td style="font-size:10px;color:#94a3b8;max-width:150px">{thesis_short}</td>
  <td style="font-weight:600">${pos['entry_price']:.2f}</td>
  <td style="font-weight:700;color:#fbbf24">${pos['cost_basis']:,.0f}<br><span style="font-size:10px;color:#64748b">{pos['shares']}股</span></td>
  <td style="font-weight:700;font-size:13px"><b style="color:#e2e8f0;font-size:13px">${pos['current_price']:.2f}</b></td>
  <td>{pnl_html(pnl, pnl_pct)}</td>
  <td style="color:#60a5fa;font-weight:700">${target_price:.2f}<br><span style="font-size:10px;color:#2dd4bf">+{target_upside}%</span></td>
  <td style="color:#f87171">${pos.get('stop_loss',0):.2f}</td>
  <td>{progress_bar(progress)}<span style="font-size:10px;color:#64748b;margin-left:4px">{held}/{target_days}天</span></td>
  <td style="font-size:11px;color:#60a5fa">{target_date}</td>
  <td><span class="badge on" style="background:{signal_color};font-weight:800">{signal}</span></td>
</tr>"""


def aggressive_row(pos: dict) -> str:
    pnl = pos["unrealized_pnl"]
    pnl_pct = pos["unrealized_pnl_pct"]
    held = pos.get("held_days", 0)
    target_days = pos.get("hold_days_target", 14)
    progress = pos.get("hold_progress_pct", 0)
    target_date = pos.get("target_date_est", "—")
    
    target_price = pos.get("target_price", 0)
    entry_price = pos["entry_price"]
    target_upside = round((target_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    
    thesis_lines = pos.get("thesis", "").split("|")
    thesis_html = "<br>".join(t.strip()[:40] for t in thesis_lines[:2])
    
    return f"""<tr data-ticker="{pos['ticker']}" data-entry="{pos['entry_price']}" data-shares="{pos['shares']}" data-entry-date="{pos['entry_date']}" data-target-days="{target_days}">
  <td><b style="font-size:13px">{pos['ticker']}</b><br><span style="font-size:10px;color:#94a3b8">{pos.get('company','')}</span></td>
  <td style="font-size:10px;color:#94a3b8;max-width:140px">{thesis_html}</td>
  <td style="font-weight:600">${pos['entry_price']:.2f}</td>
  <td style="font-weight:700;color:#fbbf24">${pos['cost_basis']:,.0f}<br><span style="font-size:10px;color:#64748b">{pos['shares']}股</span></td>
  <td style="font-weight:700;font-size:13px"><b style="color:#e2e8f0;font-size:13px">${pos['current_price']:.2f}</b></td>
  <td>{pnl_html(pnl, pnl_pct)}</td>
  <td style="color:#60a5fa;font-weight:700">${target_price:.2f}<br><span style="font-size:10px;color:#2dd4bf">+{target_upside}%</span></td>
  <td style="color:#f87171">${pos.get('stop_loss',0):.2f}</td>
  <td>{progress_bar(progress)}<span style="font-size:10px;color:#64748b;margin-left:4px">{held}/{target_days}天</span></td>
  <td style="font-size:11px;color:#60a5fa">{target_date}</td>
  <td><span style="padding:3px 7px;background:rgba(251,191,36,.15);border-radius:6px;font-size:10px;color:#fbbf24;font-weight:700">A</span></td>
</tr>"""


def blueshrimp_row(pos: dict) -> str:
    pnl = pos["unrealized_pnl"]
    pnl_pct = pos["unrealized_pnl_pct"]
    held = pos.get("held_days", 0)
    target_days = pos.get("hold_days_target", 30)
    progress = pos.get("hold_progress_pct", 0)
    target_date = pos.get("target_date_est", "—")
    score = pos.get("abcde_score", pos.get("score", 70))
    score_color = "#2dd4bf" if score >= 75 else "#fbbf24"
    
    target_price = pos.get("target_price", 0)
    entry_price = pos["entry_price"]
    target_upside = round((target_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    
    thesis = pos.get("thesis", "")
    thesis_short = thesis[:80] + "…" if len(thesis) > 80 else thesis
    
    return f"""<tr data-ticker="{pos['ticker']}" data-entry="{pos['entry_price']}" data-shares="{pos['shares']}" data-entry-date="{pos['entry_date']}" data-target-days="{target_days}">
  <td><b style="font-size:13px">{pos['ticker']}</b><br><span style="font-size:10px;color:#94a3b8">{pos.get('company','')}</span></td>
  <td style="text-align:center"><b style="color:{score_color};font-size:16px">{score}</b><span style="font-size:10px;color:#64748b">/100</span></td>
  <td>${pos['entry_price']:.2f}</td>
  <td style="color:#fbbf24">${pos['cost_basis']:,.0f}<br><span style="font-size:10px;color:#64748b">{pos['shares']}股</span></td>
  <td style="font-weight:700"><b style="color:#e2e8f0;font-size:13px">${pos['current_price']:.2f}</b></td>
  <td>{pnl_html(pnl, pnl_pct)}</td>
  <td style="color:#60a5fa">${target_price:.2f}<br><span style="font-size:10px;color:#2dd4bf">+{target_upside}%</span></td>
  <td style="color:#f87171">${pos.get('stop_loss',0):.2f}</td>
  <td>{progress_bar(progress)}<span style="font-size:10px;color:#64748b;margin-left:4px">{held}/{target_days}天</span></td>
  <td style="font-size:11px;color:#60a5fa">{target_date}</td>
  <td style="font-size:10px;color:#94a3b8">{thesis_short}</td>
</tr>"""


# ─── 4. 重建持仓区域 HTML ────────────────────────────────────────────────────

def build_institutional_section(acc: dict) -> str:
    total = acc["total_assets"]
    invested = acc["total_invested"]
    cash = acc["cash"]
    n = len(acc.get("positions", []))
    pnl = acc["total_pnl"]
    pnl_pct = acc["total_pnl_pct"]
    pnl_color = "#2dd4bf" if pnl >= 0 else "#f87171"
    pnl_sign = "+" if pnl >= 0 else ""
    
    rows = "\n".join(institutional_row(p) for p in acc.get("positions", []))
    
    # 等待区
    watchlist_wait = acc.get("watchlist_waiting_text", "⏳ 等待入场：<b style='color:#60a5fa'>SOFI</b> 等回调$16建仓")
    
    return f"""<!-- ===== 大机构账户 ===== -->
  <div class="card" style="margin-bottom:14px;border-top:3px solid #6c63ff">
    <div class="card-header" style="background:rgba(108,99,255,.07)">
      <div class="card-title">🏦 大机构账户 · ${total:,.0f}</div>
      <span style="font-size:10px;color:#94a3b8">策略：跟踪13F顶级投资人持仓变化 · 低频高确定性 · 30-90天持有周期</span>
    </div>
    <div style="display:flex;gap:12px;padding:10px 14px;flex-wrap:wrap;border-bottom:1px solid #1e1e33">
      <div style="font-size:11px"><span style="color:#64748b">总资产</span> <b style="color:#6c63ff">${total:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">已投入</span> <b style="color:#fbbf24">${invested:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">现金</span> <b style="color:#2dd4bf">${cash:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">持仓</span> <b>{n}只</b></div>
      <div style="font-size:11px;margin-left:auto"><span style="color:#64748b">浮动盈亏</span> <b style="color:{pnl_color}">{pnl_sign}${abs(pnl):,.0f} ({pnl_sign}{pnl_pct:.2f}%)</b></div>
    </div>
    <div style="overflow-x:auto">
      <table class="tbl">
        <thead><tr>
          <th>代码 / 公司</th><th>信号来源</th><th>建仓价</th><th>持仓成本</th>
          <th>当前价</th><th>浮动盈亏</th><th>目标价</th><th>止损</th>
          <th>已持/目标天</th><th>预计达标日</th><th>信号强度</th>
        </tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <div style="padding:8px 14px;font-size:11px;color:#64748b;border-top:1px solid #1e1e33">
      {watchlist_wait}
    </div>
  </div>"""


def build_aggressive_section(acc: dict) -> str:
    total = acc["total_assets"]
    invested = acc["total_invested"]
    cash = acc["cash"]
    n = len(acc.get("positions", []))
    pnl = acc["total_pnl"]
    pnl_pct = acc["total_pnl_pct"]
    pnl_color = "#2dd4bf" if pnl >= 0 else "#f87171"
    pnl_sign = "+" if pnl >= 0 else ""
    
    rows = "\n".join(aggressive_row(p) for p in acc.get("positions", []))
    
    return f"""<!-- ===== 激进交易账户 ===== -->
  <div class="card" style="margin-bottom:14px;border-top:3px solid #fbbf24">
    <div class="card-header" style="background:rgba(251,191,36,.07)">
      <div class="card-title">⚡ 激进交易账户 · ${total:,.0f}</div>
      <span style="font-size:10px;color:#94a3b8">策略：猎暴涨微盘股 · Battalion Oil(27x) / 亿珑能源(15x) / MLEC(3x) 模式</span>
    </div>
    <div style="display:flex;gap:12px;padding:10px 14px;flex-wrap:wrap;border-bottom:1px solid #1e1e33">
      <div style="font-size:11px"><span style="color:#64748b">总资产</span> <b style="color:#fbbf24">${total:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">已投入</span> <b style="color:#fbbf24">${invested:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">现金</span> <b style="color:#2dd4bf">${cash:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">持仓</span> <b>{n}只</b></div>
      <div style="font-size:11px;margin-left:auto"><span style="color:#64748b">浮动盈亏</span> <b style="color:{pnl_color}">{pnl_sign}${abs(pnl):,.0f} ({pnl_sign}{pnl_pct:.2f}%)</b></div>
    </div>
    <div style="overflow-x:auto">
      <table class="tbl">
        <thead><tr>
          <th>代码 / 公司</th><th>信号来源</th><th>建仓价</th><th>持仓成本</th>
          <th>当前价</th><th>浮动盈亏</th><th>目标价</th><th>止损</th>
          <th>已持/目标天</th><th>预计达标日</th><th>信号强度</th>
        </tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <div style="padding:8px 14px;font-size:11px;color:#64748b;border-top:1px solid #1e1e33">
      🔫 触发模式：<b style="color:#2dd4bf">breakout↑</b> 向上突破建仓 · <b style="color:#f87171">pullback↓</b> 回调入场
    </div>
  </div>"""


def build_blueshrimp_section(acc: dict) -> str:
    total = acc["total_assets"]
    invested = acc["total_invested"]
    cash = acc["cash"]
    n = len(acc.get("positions", []))
    pnl = acc["total_pnl"]
    pnl_pct = acc["total_pnl_pct"]
    pnl_color = "#2dd4bf" if pnl >= 0 else "#f87171"
    pnl_sign = "+" if pnl >= 0 else ""
    
    rows = "\n".join(blueshrimp_row(p) for p in acc.get("positions", []))
    
    return f"""<!-- ===== 蓝虾账户 ===== -->
  <div class="card" style="margin-bottom:14px;border-top:3px solid #f87171">
    <div class="card-header" style="background:rgba(248,113,113,.07)">
      <div class="card-title">🦐 蓝虾交易账户 · ${total:,.0f}</div>
      <span style="font-size:10px;color:#94a3b8">策略：小蓝虾自主决策 · ABCDE评分≥70建仓 · 多信源交叉验证</span>
    </div>
    <div style="display:flex;gap:12px;padding:10px 14px;flex-wrap:wrap;border-bottom:1px solid #1e1e33">
      <div style="font-size:11px"><span style="color:#64748b">总资产</span> <b style="color:#f87171">${total:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">已投入</span> <b style="color:#fbbf24">${invested:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">现金</span> <b style="color:#2dd4bf">${cash:,.0f}</b></div>
      <div style="font-size:11px"><span style="color:#64748b">持仓</span> <b>{n}只</b></div>
      <div style="font-size:11px;margin-left:auto"><span style="color:#64748b">浮动盈亏</span> <b style="color:{pnl_color}">{pnl_sign}${abs(pnl):,.0f} ({pnl_sign}{pnl_pct:.2f}%)</b></div>
    </div>
    <div style="overflow-x:auto">
      <table class="tbl">
        <thead><tr>
          <th>代码 / 公司</th><th>ABCDE评分</th><th>建仓价</th><th>持仓成本</th>
          <th>当前价</th><th>浮动盈亏</th><th>目标价</th><th>止损</th>
          <th>已持/目标天</th><th>预计达标日</th><th>决策依据</th>
        </tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <div style="padding:8px 14px;font-size:11px;color:#64748b;border-top:1px solid #1e1e33">
      🦐 ABCDE模型：A激活(20) · B业务(20) · C催化剂(20) · D流通(20) · E时机(20) · <b style="color:#2dd4bf">≥70建仓</b>
    </div>
  </div>"""


# ─── 5. 更新 Dashboard HTML ───────────────────────────────────────────────────

def update_dashboard_html(data: dict, now_str: str):
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    
    accs = data["accounts"]
    inst = accs["institutional"]
    aggr = accs["aggressive"]
    blue = accs["blueshrimp"]
    
    inst_total = inst["total_assets"]
    aggr_total = aggr["total_assets"]
    blue_total = blue["total_assets"]
    grand_total = inst_total + aggr_total + blue_total
    
    inst_pnl = inst["total_pnl"]
    aggr_pnl = aggr["total_pnl"]
    blue_pnl = blue["total_pnl"]
    grand_pnl = inst_pnl + aggr_pnl + blue_pnl
    grand_pnl_pct = round(grand_pnl / 150000 * 100, 2)
    grand_color = "#2dd4bf" if grand_pnl >= 0 else "#f87171"
    grand_sign = "+" if grand_pnl >= 0 else ""
    
    inst_n = len(inst.get("positions", []))
    aggr_n = len(aggr.get("positions", []))
    blue_n = len(blue.get("positions", []))
    
    # ── 5a. 顶部总资产卡 ──
    html = re.sub(
        r'(<div class="stat-val" style="[^"]*color:#60a5fa[^"]*">)\$[\d,]+',
        lambda m: m.group(1) + f'${grand_total:,.0f}',
        html, count=1
    )
    # 总盈亏
    html = re.sub(
        r'(总盈亏[^<]*<b[^>]*>)[^<]*(</b>)',
        lambda m: m.group(1) + f'{grand_sign}${abs(grand_pnl):,.0f} ({grand_sign}{grand_pnl_pct:.2f}%)' + m.group(2),
        html, count=1
    )
    
    # ── 5b. 三账户汇总小卡 ──
    def replace_account_card(html, label, total, n, cash, color):
        # 总资产值
        pattern = rf'(<div class="stat-lbl">{re.escape(label)}</div><div class="stat-val"[^>]*>)\$[\d,]+'
        html = re.sub(pattern, lambda m: m.group(1) + f'${total:,.0f}', html, count=1)
        # 副标题（持仓数|现金）
        tickers = "|".join(p["ticker"] for p in data["accounts"][
            "institutional" if "大机构" in label else
            "aggressive" if "激进" in label else "blueshrimp"
        ].get("positions", []))
        sub_text = f'{tickers} {n}只 | 现金${cash:,.0f}'
        pattern2 = rf'({re.escape(label)}</div><div[^>]*>)\$[\d,]+</div><div class="stat-sub">[^<]+'
        # simpler: just replace the stat-sub text under this label
        # We'll do a targeted block replacement
        return html
    
    # 用更精确的替换：找到三个 stat div 整体替换
    inst_tickers = "·".join(p["ticker"] for p in inst.get("positions", []))
    aggr_tickers = "·".join(p["ticker"] for p in aggr.get("positions", []))
    blue_tickers = "·".join(p["ticker"] for p in blue.get("positions", []))
    
    inst_pnl_color = "#2dd4bf" if inst_pnl >= 0 else "#f87171"
    aggr_pnl_color = "#2dd4bf" if aggr_pnl >= 0 else "#f87171"
    blue_pnl_color = "#2dd4bf" if blue_pnl >= 0 else "#f87171"
    
    new_stat_inst = (f'<div class="stat" style="border-top:3px solid #6c63ff">'
                     f'<div class="stat-lbl">🏦 大机构</div>'
                     f'<div class="stat-val" style="color:#6c63ff">${inst_total:,.0f}</div>'
                     f'<div class="stat-sub">{inst_tickers} {inst_n}只 | 现金${inst["cash"]:,.0f}</div></div>')
    new_stat_aggr = (f'<div class="stat" style="border-top:3px solid #fbbf24">'
                     f'<div class="stat-lbl">⚡ 激进交易</div>'
                     f'<div class="stat-val" style="color:#fbbf24">${aggr_total:,.0f}</div>'
                     f'<div class="stat-sub">{aggr_tickers} {aggr_n}只 | 现金${aggr["cash"]:,.0f}</div></div>')
    new_stat_blue = (f'<div class="stat" style="border-top:3px solid #f87171">'
                     f'<div class="stat-lbl">🦐 蓝虾交易</div>'
                     f'<div class="stat-val" style="color:#f87171">${blue_total:,.0f}</div>'
                     f'<div class="stat-sub">{blue_tickers} {blue_n}只 | 现金${blue["cash"]:,.0f}</div></div>')
    
    # 修复：用精确匹配替换三账户 stat div（嵌套 div 用 stat-lbl 前缀锁定边界）
    html = re.sub(
        r'<div class="stat" style="border-top:3px solid #6c63ff"><div class="stat-lbl">🏦 大机构</div>(?:(?!</div></div>).)*</div></div>'
        r'\s*<div class="stat" style="border-top:3px solid #fbbf24"><div class="stat-lbl">⚡ 激进交易</div>(?:(?!</div></div>).)*</div></div>'
        r'\s*<div class="stat" style="border-top:3px solid #f87171"><div class="stat-lbl">🦐 蓝虾交易</div>(?:(?!</div></div>).)*</div></div>',
        new_stat_inst + '\n    ' + new_stat_aggr + '\n    ' + new_stat_blue,
        html, flags=re.DOTALL, count=1
    )
    
    # ── 5c. 三账户持仓区域整体替换 ──
    new_inst_html = build_institutional_section(inst)
    new_aggr_html = build_aggressive_section(aggr)
    new_blue_html = build_blueshrimp_section(blue)
    
    # 替换大机构区域（从注释到下一个注释）
    html = re.sub(
        r'<!-- ===== 大机构账户 ===== -->.*?(?=<!-- ===== 激进交易账户 ===== -->)',
        new_inst_html + '\n\n  ',
        html, flags=re.DOTALL, count=1
    )
    html = re.sub(
        r'<!-- ===== 激进交易账户 ===== -->.*?(?=<!-- ===== 蓝虾账户 ===== -->)',
        new_aggr_html + '\n\n  ',
        html, flags=re.DOTALL, count=1
    )
    html = re.sub(
        r'<!-- ===== 蓝虾账户 ===== -->.*?(?=<!-- 汇总 \+ 规则 -->|<!-- ===== )',
        new_blue_html + '\n\n  ',
        html, flags=re.DOTALL, count=1
    )
    
    # ── 5d. 三账户对比表 ──
    inst_invested = sum(p["cost_basis"] for p in inst.get("positions", []))
    aggr_invested = sum(p["cost_basis"] for p in aggr.get("positions", []))
    blue_invested = sum(p["cost_basis"] for p in blue.get("positions", []))
    total_invested = inst_invested + aggr_invested + blue_invested
    total_cash = inst["cash"] + aggr["cash"] + blue["cash"]
    
    new_comparison = f"""<tbody>
          <tr><td>🏦 大机构</td><td><b style="color:#6c63ff">${inst_total:,.0f}</b></td><td>{inst_n}只/${inst_invested:,.0f}</td><td>${inst['cash']:,.0f}</td><td style="font-size:10px">13F跟踪 30-90天</td></tr>
          <tr><td>⚡ 激进交易</td><td><b style="color:#fbbf24">${aggr_total:,.0f}</b></td><td>{aggr_n}只/${aggr_invested:,.0f}</td><td>${aggr['cash']:,.0f}</td><td style="font-size:10px">暴涨猎手 1-21天</td></tr>
          <tr><td>🦐 蓝虾</td><td><b style="color:#f87171">${blue_total:,.0f}</b></td><td>{blue_n}只/${blue_invested:,.0f}</td><td>${blue['cash']:,.0f}</td><td style="font-size:10px">自主决策 1-30天</td></tr>
          <tr><td><b>合计</b></td><td><b style="color:#2dd4bf">${grand_total:,.0f}</b></td><td>{inst_n+aggr_n+blue_n}只/${total_invested:,.0f}</td><td>${total_cash:,.0f}</td><td style="font-size:10px">{grand_sign}${abs(grand_pnl):,.0f}({grand_sign}{grand_pnl_pct:.2f}%)</td></tr>
        </tbody>"""
    
    html = re.sub(
        r'<tbody>\s*<tr><td>🏦 大机构</td>.*?</tbody>',
        new_comparison,
        html, flags=re.DOTALL, count=1
    )
    
    # ── 5e. 更新时间戳 + 页面日期 ──
    html = re.sub(
        r'(股价更新[：:][^<\n]*|价格更新[：:][^<\n]*|last updated[^<\n]*)',
        f'股价更新：{now_str}',
        html, flags=re.IGNORECASE, count=1
    )
    # 更新页面内各处日期（总览副标题/今日推送/工作Trace）
    today_date = datetime.now().strftime('%Y-%m-%d')
    html = re.sub(r'小蓝虾 OpenClaw Agent · \d{4}-\d{2}-\d{2}',
                  f'小蓝虾 OpenClaw Agent · {today_date}', html)
    html = re.sub(r'📡 今日推送 \(\d{4}-\d{2}-\d{2}\)',
                  f'📡 今日推送 ({today_date})', html)
    html = re.sub(r'工作 Trace \(\d{4}-\d{2}-\d{2}\)',
                  f'工作 Trace ({today_date})', html)
    html = re.sub(r'今日关键事件（\d{4}[-–]\d{2}[-–]\d{2}）',
                  f'今日关键事件（{today_date}）', html)
    # 如果没有时间戳，在头部汇总卡附近加一个
    if '股价更新' not in html:
        html = html.replace(
            '自动扫描: <b style="color:#2dd4bf">北京时间 10/16/22/04点</b>',
            f'自动扫描: <b style="color:#2dd4bf">北京时间 10/16/22/04点</b><br>股价更新：{now_str}'
        )
    
    # ── 自动同步记忆页 ──
    html = update_memory_section(html, now_str)

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[Dashboard] 已写入 {DASHBOARD_FILE}")


def update_memory_section(html: str, now_str: str) -> str:
    """读取今日 memory/YYYY-MM-DD.md，提取关键事件，更新记忆页"""
    import glob
    from datetime import date

    today = date.today().strftime("%Y-%m-%d")
    memory_file = os.path.join(WORKSPACE, f"memory/{today}.md")
    
    # 读取今日记忆文件（最多前200行）
    memory_lines = []
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            memory_lines = f.readlines()[:200]

    # 统计日记文件数量
    memory_files = glob.glob(os.path.join(WORKSPACE, "memory/2026-*.md"))
    diary_count = len(memory_files)

    # 提取今日关键事件（## 标题行）
    key_events = []
    for line in memory_lines:
        line = line.strip()
        if line.startswith("## ") and "—" in line:
            event = line.replace("## ", "").strip()
            key_events.append(event)
        if len(key_events) >= 5:
            break

    # 读取最新的 memory 文件列表（倒序取最近8个）
    memory_files.sort(reverse=True)
    diary_rows = ""
    for mf in memory_files[:8]:
        fname = os.path.basename(mf).replace(".md", "")
        if fname == today:
            label = f'<span class="tag g">今日</span> {fname}'
            km_link = '<span class="tag">待生成</span>'
        else:
            label = fname
            km_link = '<span class="tag" style="color:#64748b">本地</span>'
        diary_rows += f'<tr><td>{label}</td><td>-</td><td>{km_link}</td></tr>\n'

    # 构建关键记忆 tags
    key_tags = ""
    for ev in key_events[:5]:
        short = ev[:20] if len(ev) > 20 else ev
        key_tags += f'<span class="tag">{short}</span>'

    new_memory_section = f'''<!-- ══ MEMORY ══ -->
<div id="page-memory" class="page">
  <div style="margin-bottom:14px"><h2 style="font-size:17px;font-weight:800">🧠 记忆系统</h2></div>
  <div class="g4" style="margin-bottom:14px">
    <div class="stat"><div class="stat-lbl">记忆后端</div><div class="stat-val" style="font-size:14px;color:var(--accent)">Engram</div><div class="stat-sub">v9.0.92 · balanced</div></div>
    <div class="stat"><div class="stat-lbl">日记文件</div><div class="stat-val" style="color:var(--blue)">{diary_count}</div><div class="stat-sub">自动统计</div></div>
    <div class="stat"><div class="stat-lbl">长期记忆</div><div class="stat-val" style="color:var(--green)">MEMORY.md</div><div class="stat-sub">精华提炼</div></div>
    <div class="stat"><div class="stat-lbl">最后同步</div><div class="stat-val" style="color:var(--yellow);font-size:13px">{now_str}</div><div class="stat-sub">自动更新</div></div>
  </div>
  <div class="g2">
    <div class="card">
      <div class="card-header"><div class="card-title">📅 日记文件</div></div>
      <div class="card-body" style="padding:0">
        <table class="tbl">
          <thead><tr><th>文件</th><th>内容</th><th>学城日报</th></tr></thead>
          <tbody>
            {diary_rows}
          </tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><div class="card-title">🔑 今日关键事件（{today}）</div></div>
      <div class="card-body">
        <div style="display:flex;flex-direction:column;gap:10px">
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:3px">身份</div><div style="font-size:11px">小蓝虾 🦐🔵 · 主人 uid:2872173767</div></div>
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:3px">今日关键事件</div><div style="font-size:11px;display:flex;flex-wrap:wrap;gap:3px">{key_tags if key_tags else '<span class="tag">今日无记录</span>'}</div></div>
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:3px">铁律</div><div style="font-size:11px">持仓变动 → 更新Dashboard → push GitHub Pages</div></div>
        </div>
      </div>
    </div>
  </div>
</div>'''

    new_memory_section_with_spacing = new_memory_section + '\n\n'
    updated = re.sub(
        r'<!-- ══ MEMORY ══ -->.*?(?=<!-- ══ FILES ══ -->)',
        new_memory_section_with_spacing,
        html,
        flags=re.DOTALL
    )
    if updated != html:
        print(f"[Memory] 记忆页已同步 ({today}, {len(key_events)}个关键事件)")
    else:
        print("[Memory] 记忆页 pattern 未匹配，跳过")
    return updated


# ─── 6. 推送 GitHub Pages ─────────────────────────────────────────────────────

def push_to_github():
    if not os.path.exists(PUSH_SCRIPT):
        print(f"[GitHub] 推送脚本不存在: {PUSH_SCRIPT}")
        return False
    try:
        result = subprocess.run(
            ["bash", PUSH_SCRIPT],
            capture_output=True, text=True, timeout=60,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            print("[GitHub] ✅ 推送成功")
            return True
        else:
            print(f"[GitHub] ❌ 推送失败:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"[GitHub] ❌ 推送异常: {e}")
        return False


# ─── 7. 主流程 ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"[sync_dashboard] 开始执行 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 读取 structure.json
    with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 收集所有持仓 ticker
    all_tickers = []
    for acc in data["accounts"].values():
        for pos in acc.get("positions", []):
            if pos["ticker"] not in all_tickers:
                all_tickers.append(pos["ticker"])
    
    print(f"[持仓] 共 {len(all_tickers)} 只：{all_tickers}")
    
    # 获取实时价格
    prices = get_all_prices(all_tickers)
    
    # 更新 structure.json
    data = update_structure(data, prices)
    with open(STRUCTURE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[structure.json] 已更新")
    
    # 打印汇总
    grand_total = sum(acc["total_assets"] for acc in data["accounts"].values())
    grand_pnl = sum(acc["total_pnl"] for acc in data["accounts"].values())
    print(f"\n[汇总] 总资产: ${grand_total:,.2f} | 浮动盈亏: ${grand_pnl:+,.2f}")
    for acc_id, acc in data["accounts"].items():
        print(f"  {acc_id}: ${acc['total_assets']:,.2f} (现金${acc['cash']:,.0f} + 持仓${acc['total_invested']:,.0f}) PnL: ${acc['total_pnl']:+,.2f}")
    
    # 更新 Dashboard HTML
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_dashboard_html(data, now_str)
    
    # 推送 GitHub Pages
    push_result = push_to_github()
    
    print("\n[完成] ✅ sync_dashboard 执行完毕")
    return 0 if push_result else 1


if __name__ == "__main__":
    sys.exit(main())
