#!/usr/bin/env python3
"""
给 Dashboard 持仓行加 data- 属性，注入 JS 实时价格+天数+盈亏刷新
运行一次即可，之后由 portfolio_scanner.py 维护价格
"""
import re

DASHBOARD = "/root/.openclaw/workspace/dashboard/dashboard.html"

# 持仓配置：ticker -> {entry, shares, entry_date, target_days, cost}
POSITIONS = {
    "CPNG":  {"entry": 20.80, "shares": 360,  "entry_date": "2026-03-18", "target_days": 45},
    "HBAN":  {"entry": 15.39, "shares": 487,  "entry_date": "2026-03-18", "target_days": 60},
    "UPXI":  {"entry": 1.15,  "shares": 4347, "entry_date": "2026-03-18", "target_days": 14},
    "QUBT":  {"entry": 7.54,  "shares": 663,  "entry_date": "2026-03-18", "target_days": 14},
    "SOUN":  {"entry": 7.82,  "shares": 639,  "entry_date": "2026-03-18", "target_days": 14},
    "IREN":  {"entry": 42.96, "shares": 116,  "entry_date": "2026-03-18", "target_days": 21},
    "ROLR":  {"entry": 4.35,  "shares": 690,  "entry_date": "2026-03-18", "target_days": 7},
    "TOI":   {"entry": 3.59,  "shares": 1114, "entry_date": "2026-03-18", "target_days": 30},
}

with open(DASHBOARD, "r", encoding="utf-8") as f:
    html = f.read()

# 1. 给每个持仓 <tr> 加 data- 属性
def add_data_attrs(html):
    for ticker, pos in POSITIONS.items():
        # 匹配持仓行：<tr>\n  <td><b ...>TICKER</b>
        pattern = r'(<tr>)(\s*<td><b[^>]*>' + re.escape(ticker) + r'</b>)'
        replacement = (
            f'<tr data-ticker="{ticker}" '
            f'data-entry="{pos["entry"]}" '
            f'data-shares="{pos["shares"]}" '
            f'data-entry-date="{pos["entry_date"]}" '
            f'data-target-days="{pos["target_days"]}">'
            r'\2'
        )
        html = re.sub(pattern, replacement, html)
    return html

html = add_data_attrs(html)

# 2. 注入 JS（替换现有 <script> 块）
LIVE_JS = r"""
<script>
/* ===== 时钟 ===== */
function tick(){
  var el=document.getElementById('clock');
  if(!el)return;
  var d=new Date();
  el.textContent=d.toLocaleTimeString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false})+' CST';
}
setInterval(tick,1000); tick();

/* ===== 实时价格 + 持仓天数 + 盈亏刷新 ===== */
var STOOQ_BASE = 'https://stooq.com/q/l/?f=sd2t2ohlcv&h&e=csv&s=';

function daysBetween(dateStr) {
  var d0 = new Date(dateStr + 'T00:00:00+08:00');
  var d1 = new Date();
  return Math.floor((d1 - d0) / 86400000);
}

function fmtPnl(val, pct) {
  var color = val >= 0 ? '#2dd4bf' : '#f87171';
  var sign  = val >= 0 ? '+' : '';
  return '<span style="color:'+color+';font-weight:700">'
    + sign + '$' + Math.abs(val).toFixed(0)
    + ' (' + sign + pct.toFixed(1) + '%)</span>';
}

function fmtDays(days, targetDays) {
  var pct = Math.min(days / targetDays * 100, 100);
  return '<div style="background:#1e1e33;border-radius:4px;height:6px;width:80px;display:inline-block;vertical-align:middle">'
    + '<div style="background:#6c63ff;width:'+pct+'%;height:6px;border-radius:4px"></div></div>'
    + '<span style="font-size:10px;color:#64748b;margin-left:4px">'+days+'/'+targetDays+'天</span>';
}

function refreshRow(row, price) {
  var entry      = parseFloat(row.dataset.entry);
  var shares     = parseInt(row.dataset.shares);
  var entryDate  = row.dataset.entryDate;
  var targetDays = parseInt(row.dataset.targetDays);
  var days       = daysBetween(entryDate);

  var pnlAbs  = (price - entry) * shares;
  var pnlPct  = (price - entry) / entry * 100;

  // 找列：当前价 (3rd td after 建仓价), 浮动盈亏 (4th), 已持天数 (8th or 7th)
  var tds = row.querySelectorAll('td');
  // 通过遍历找到含建仓价的td后的"当前价"和"浮动盈亏"
  // 结构固定：[0]代码 [1]信号 [2]建仓价 [3]成本 [4]当前价 [5]浮动盈亏 [6]目标价 [7]止损 [8]天数 ...
  if (tds.length >= 9) {
    tds[4].innerHTML = '<b style="color:#e2e8f0;font-size:13px">$' + price.toFixed(2) + '</b>';
    tds[5].innerHTML = fmtPnl(pnlAbs, pnlPct);
    tds[8].innerHTML = fmtDays(days, targetDays);
  } else if (tds.length >= 8) {
    // 蓝虾账户列结构：[0]代码 [1]评分 [2]建仓价 [3]成本 [4]当前价 [5]盈亏 [6]目标 [7]止损 [8]天数 [9]达标日 [10]依据
    tds[4].innerHTML = '<b style="color:#e2e8f0;font-size:13px">$' + price.toFixed(2) + '</b>';
    tds[5].innerHTML = fmtPnl(pnlAbs, pnlPct);
    tds[8].innerHTML = fmtDays(days, targetDays);
  }
}

function fetchPrice(ticker, callback) {
  var url = STOOQ_BASE + ticker.toLowerCase() + '.us';
  fetch(url).then(function(r){ return r.text(); }).then(function(csv){
    var lines = csv.trim().split('\n');
    if (lines.length < 2) return;
    var cols = lines[1].split(',');
    var close = parseFloat(cols[4]); // Close is col 4 in ohlcv
    if (close > 0) callback(close);
  }).catch(function(){});
}

function refreshAll() {
  var rows = document.querySelectorAll('tr[data-ticker]');
  rows.forEach(function(row) {
    var ticker = row.dataset.ticker;
    fetchPrice(ticker, function(price) {
      refreshRow(row, price);
    });
  });
  // 更新最后刷新时间
  var el = document.getElementById('live-refresh-ts');
  if (el) {
    var d = new Date();
    el.textContent = '价格最后刷新: ' + d.toLocaleTimeString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  }
}

// 页面加载后立刻刷新，之后每5分钟
window.addEventListener('load', function(){
  refreshAll();
  setInterval(refreshAll, 5 * 60 * 1000);
});
</script>
"""

# 替换旧的 <script> 块
html = re.sub(r'<script>.*?</script>', LIVE_JS.strip(), html, flags=re.DOTALL)

# 3. 在持仓区底部加刷新时间戳（如果没有的话）
if 'live-refresh-ts' not in html:
    html = html.replace(
        '</body>',
        '<div style="text-align:center;padding:6px;font-size:10px;color:#475569" id="live-refresh-ts">价格刷新中...</div>\n</body>'
    )

with open(DASHBOARD, "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Dashboard 已注入实时价格+天数+盈亏 JS")
print(f"   持仓行: {len(POSITIONS)} 个 data-ticker 属性")
