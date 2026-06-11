#!/usr/bin/env python3
"""
render_daily_dashboard.py — 读取 dashboard_today.json，注入到 dashboard.html 各模块

注入点：
  - #today-memory   : 记忆模块 → 今日重要事件
  - #today-stocks   : 股票模块 → 今日持仓快照 + 操作
  - #today-evolution: 进化模块 → 今日进化笔记
  - #today-intel    : 日志模块 → 今日情报拉取记录

每次 cron 结束后调用，全量刷新这4个 div 的内容。
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
import pytz

WORKSPACE = "/root/.openclaw/workspace"
LOG_FILE = f"{WORKSPACE}/dashboard/dashboard_today.json"
DASHBOARD_FILE = f"{WORKSPACE}/dashboard/dashboard.html"
PUSH_SCRIPT = f"{WORKSPACE}/scripts/push_dashboard_to_github.sh"

def get_now_str():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")

def load_today_log():
    if not os.path.exists(LOG_FILE):
        return None
    with open(LOG_FILE) as f:
        return json.load(f)

def render_memory_block(data):
    items = data.get("memory", [])
    if not items:
        return '<p style="color:#888;font-style:italic">今日暂无重要记忆事件</p>'
    rows = ""
    for item in reversed(items):  # 最新在上
        rows += f"""
        <div style="padding:8px 0;border-bottom:1px solid #2a2a2a">
          <span style="color:#888;font-size:12px">{item.get('time','')}</span>
          <span style="margin-left:8px;color:#e0e0e0">{item.get('content','')}</span>
        </div>"""
    return rows

def render_stocks_block(data):
    stocks = data.get("stocks", {})
    snap = stocks.get("snapshot")
    actions = stocks.get("actions", [])

    html = ""

    # 持仓快照
    if snap:
        total = snap.get("total", 0)
        pnl_pct = snap.get("pnl_pct", 0)
        pnl_color = "#4caf50" if pnl_pct >= 0 else "#f44336"
        pnl_sign = "+" if pnl_pct >= 0 else ""
        html += f"""
        <div style="background:#1a2332;border-radius:8px;padding:12px;margin-bottom:12px">
          <div style="color:#888;font-size:12px">持仓快照 · {snap.get('time','')}</div>
          <div style="font-size:22px;font-weight:bold;color:#fff;margin:4px 0">${total:,.0f}</div>
          <div style="color:{pnl_color};font-size:16px">{pnl_sign}{pnl_pct:.2f}% 今日</div>
        </div>"""

    # 今日操作
    if actions:
        html += '<div style="color:#aaa;font-size:13px;margin-bottom:6px">📋 今日操作</div>'
        for act in reversed(actions):
            color = "#4caf50" if "买" in act.get("action","") or "BUY" in act.get("action","").upper() else \
                    "#f44336" if "卖" in act.get("action","") or "SELL" in act.get("action","").upper() or "止损" in act.get("action","") else \
                    "#90caf9"
            html += f"""
            <div style="padding:8px;margin-bottom:6px;background:#1e1e1e;border-radius:6px;border-left:3px solid {color}">
              <span style="color:#888;font-size:11px">{act.get('time','')} · {act.get('ticker','')}</span>
              <div style="color:#e0e0e0;margin-top:3px">{act.get('action','')} — {act.get('content','')}</div>
            </div>"""
    elif not snap:
        html = '<p style="color:#888;font-style:italic">今日暂无股票操作</p>'
    else:
        html += '<p style="color:#888;font-style:italic;font-size:13px">今日无交易操作，持仓稳定</p>'

    return html

def render_evolution_block(data):
    items = data.get("evolution", [])
    if not items:
        return '<p style="color:#888;font-style:italic">今日暂无进化记录</p>'
    rows = ""
    for item in reversed(items):
        rows += f"""
        <div style="padding:10px;margin-bottom:8px;background:#1a2a1a;border-radius:6px;border-left:3px solid #4caf50">
          <span style="color:#888;font-size:11px">{item.get('time','')}</span>
          <div style="color:#c8e6c9;margin-top:4px">{item.get('content','')}</div>
        </div>"""
    return rows

def render_intel_block(data):
    items = data.get("intel", [])
    if not items:
        return '<p style="color:#888;font-style:italic">今日暂无情报记录</p>'
    rows = ""
    source_colors = {
        "Twitter": "#1da1f2",
        "Perplexity": "#7c3aed",
        "Scholar": "#f59e0b",
        "13F": "#10b981",
        "AISA": "#3b82f6",
        "未知": "#888"
    }
    for item in reversed(items):
        src = item.get("source", "未知")
        color = source_colors.get(src, "#888")
        rows += f"""
        <div style="padding:10px;margin-bottom:8px;background:#1e1e1e;border-radius:6px;border-left:3px solid {color}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
            <span style="background:{color}22;color:{color};padding:2px 8px;border-radius:4px;font-size:11px">{src}</span>
            <span style="color:#888;font-size:11px">{item.get('time','')}</span>
          </div>
          <div style="color:#e0e0e0;font-size:13px">{item.get('content','')}</div>
        </div>"""
    return rows

def inject_block(html: str, block_id: str, new_content: str) -> str:
    """替换 <div id="BLOCK_ID">...</div> 的内容（正确处理嵌套div，防止重复累积）"""
    # 找到目标块的起始位置
    open_tag_pattern = re.compile(rf'<div\s+id="{re.escape(block_id)}"[^>]*>')
    m = open_tag_pattern.search(html)
    if not m:
        print(f"  ⚠️  Block #{block_id} not found in HTML")
        return html

    start = m.start()
    inner_start = m.end()

    # 用嵌套计数找到真正的闭合 </div>
    depth = 1
    i = inner_start
    while i < len(html) and depth > 0:
        if html[i:i+4] == '<div':
            depth += 1
            i += 4
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                end = i + 6
                break
            i += 6
        else:
            i += 1
    else:
        print(f"  ⚠️  Block #{block_id}: could not find closing </div>")
        return html

    # 重建该块：保留外层 div 标签，替换内容
    outer_open = html[start:inner_start]
    new_block = outer_open + new_content + '</div>'
    new_html = html[:start] + new_block + html[end:]
    print(f"  ✅ #{block_id} updated")
    return new_html

def ensure_blocks_exist(html: str) -> str:
    """如果 today-* div 不存在，插入到对应 tab 页面的开头"""

    # today-memory → 插入到 #page-memory 开头
    if 'id="today-memory"' not in html:
        html = html.replace(
            '<div id="page-memory" class="page">',
            '<div id="page-memory" class="page">\n  <div id="today-memory" style="margin-bottom:16px;padding:12px;background:#111;border-radius:8px"><div style="color:#64b5f6;font-size:13px;font-weight:bold;margin-bottom:8px">📝 今日记忆事件</div></div>'
        )
        print("  ✅ Injected #today-memory placeholder")

    # today-evolution → 插入到 #page-evolution 开头
    if 'id="today-evolution"' not in html:
        html = html.replace(
            '<div id="page-evolution" class="page">',
            '<div id="page-evolution" class="page">\n  <div id="today-evolution" style="margin-bottom:16px;padding:12px;background:#111;border-radius:8px"><div style="color:#81c784;font-size:13px;font-weight:bold;margin-bottom:8px">🦐 今日进化</div></div>'
        )
        print("  ✅ Injected #today-evolution placeholder")

    # today-stocks → 找 #page-portfolio 或持仓 tab
    for stock_tab in ['id="page-portfolio"', 'id="page-stocks"', 'id="page-positions"']:
        if stock_tab in html and 'id="today-stocks"' not in html:
            html = html.replace(
                f'<div {stock_tab} class="page">',
                f'<div {stock_tab} class="page">\n  <div id="today-stocks" style="margin-bottom:16px;padding:12px;background:#111;border-radius:8px"><div style="color:#ffb74d;font-size:13px;font-weight:bold;margin-bottom:8px">📊 今日股票动态</div></div>'
            )
            print(f"  ✅ Injected #today-stocks into {stock_tab}")
            break

    # today-intel → 插入到 #page-logs 开头
    for log_tab in ['id="page-logs"', 'id="page-log"', 'id="page-intel"']:
        if log_tab in html and 'id="today-intel"' not in html:
            html = html.replace(
                f'<div {log_tab} class="page">',
                f'<div {log_tab} class="page">\n  <div id="today-intel" style="margin-bottom:16px;padding:12px;background:#111;border-radius:8px"><div style="color:#ba68c8;font-size:13px;font-weight:bold;margin-bottom:8px">🐦 今日情报拉取</div></div>'
            )
            print(f"  ✅ Injected #today-intel into {log_tab}")
            break

    return html

def update_last_refresh_time(html: str) -> str:
    now_str = get_now_str()
    # 更新已有的 last-update span，或者添加一个
    pattern = r'(<span[^>]*id="last-update"[^>]*>)[^<]*(</span>)'
    new_html, count = re.subn(pattern, rf'\g<1>最后更新: {now_str}\g<2>', html)
    if count == 0:
        # 找 dashboard title 附近插入
        html = html.replace(
            '</h1>',
            f'</h1>\n  <div style="color:#888;font-size:12px;text-align:center">最后更新: {now_str} | <a href="https://seanliii.github.io/xialanxia-dashboard/" style="color:#64b5f6">GitHub Pages</a></div>'
        )
    return html

def main():
    print(f"\n🔄 render_daily_dashboard.py — {get_now_str()}")
    print("─" * 50)

    log = load_today_log()
    if not log:
        print("⚠️  No dashboard_today.json found. Nothing to render.")
        return

    print(f"📅 Date: {log['date']} | Last updated: {log.get('last_updated','?')}")
    print(f"  memory: {len(log.get('memory',[]))} items")
    print(f"  stocks actions: {len(log.get('stocks',{}).get('actions',[]))} items")
    print(f"  evolution: {len(log.get('evolution',[]))} items")
    print(f"  intel: {len(log.get('intel',[]))} items")
    print()

    with open(DASHBOARD_FILE) as f:
        html = f.read()

    # 确保注入点存在
    html = ensure_blocks_exist(html)

    # 渲染各模块
    memory_html = render_memory_block(log)
    stocks_html = render_stocks_block(log)
    evolution_html = render_evolution_block(log)
    intel_html = render_intel_block(log)

    # 注入（带标题头）
    def wrap_with_title(title_html, content):
        return title_html + content

    html = inject_block(html, "today-memory",
        f'<div style="color:#64b5f6;font-size:13px;font-weight:bold;margin-bottom:8px">📝 今日记忆事件</div>{memory_html}')
    html = inject_block(html, "today-stocks",
        f'<div style="color:#ffb74d;font-size:13px;font-weight:bold;margin-bottom:8px">📊 今日股票动态</div>{stocks_html}')
    html = inject_block(html, "today-evolution",
        f'<div style="color:#81c784;font-size:13px;font-weight:bold;margin-bottom:8px">🦐 今日进化</div>{evolution_html}')
    html = inject_block(html, "today-intel",
        f'<div style="color:#ba68c8;font-size:13px;font-weight:bold;margin-bottom:8px">🐦 今日情报拉取</div>{intel_html}')

    html = update_last_refresh_time(html)

    with open(DASHBOARD_FILE, "w") as f:
        f.write(html)
    print(f"\n✅ dashboard.html updated")

    # 推送 GitHub Pages
    print("🚀 Pushing to GitHub Pages...")
    result = subprocess.run(["bash", PUSH_SCRIPT], capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print("✅ GitHub Pages pushed successfully")
        print("   https://seanliii.github.io/xialanxia-dashboard/")
    else:
        print(f"❌ Push failed: {result.stderr[:200]}")

if __name__ == "__main__":
    main()
