# 三账户模拟交易系统 Skill

> 🦐 小蓝虾实战验证，从 2026-03-17 运行至今。初始 $150,000 三账户独立运作。

## 系统概述

| 账户 | 初始资金 | 策略 | 持仓风格 | 信号来源 |
|------|---------|------|---------|---------|
| 🏦 大机构 | $50,000 | 跟踪13F+内部人买入 | 中长线30-90天 | SEC Form 4、13F季报 |
| ⚡ 激进交易 | $50,000 | 小微股暴涨回调/突破 | 短线7-14天 | Twitter情绪、Reddit、异动 |
| 🦐 蓝虾 | $50,000 | 综合多信源自主决策 | 灵活 | Perplexity、Scholar、多引擎搜索 |

### 核心能力
- **自动价格获取**：Yahoo Finance → Stooq → Tavily 三重降级
- **自动触发建仓**：Watchlist 设定触发价，到价自动买入
- **自动止损**：硬规则，触发即平仓+记录
- **Dashboard 可视化**：GitHub Pages 一键推送，随时查看
- **SEC 内部人监控**：EDGAR Form 4 扫描 CEO/CFO 买入信号

---

## 环境准备

### 必需
```bash
# Python 3.8+（通常沙箱已有）
python3 --version  # 成功标准：显示 3.8+

# pytz（时区处理）
pip3 install pytz  # 成功标准：无报错
```

### API Keys（按需）

| Key | 用途 | 免费额度 | 必须？ |
|-----|------|---------|--------|
| GitHub Token | Dashboard 推送 | 无限 | ✅ 必须 |
| Tavily API Key | 备用价格源 | 1000次/月 | ⚠️ 推荐 |
| AISA API Key | 内部人交易数据 | 按量付费 | 可选 |

```bash
# 验证 GitHub Token
curl -s -H "Authorization: token <你的GitHub Token>" https://api.github.com/user | grep login
# 成功标准：返回你的用户名
```

### 目录结构
```
workspace/
├── scripts/
│   ├── portfolio_scanner.py      # 核心扫描器（714行）
│   ├── simulate_pnl.py           # 每日损益计算
│   ├── cron_dashboard_update.py  # Dashboard 更新入口
│   └── push_dashboard_to_github.sh  # GitHub Pages 推送
├── portfolio/
│   ├── accounts/
│   │   └── structure.json        # 三账户持仓数据
│   ├── positions.json            # 合并持仓视图
│   ├── watchlist.json            # 自动触发候选
│   └── pnl_log.json             # 历史损益记录
├── data/
│   ├── portfolio_prices.json     # 价格缓存（当天有效）
│   └── daily_signals.json        # 信号记录
└── dashboard/
    └── dashboard.html            # 可视化页面
```

---

## 第一次部署（5分钟）

### Step 1：创建目录结构

```bash
cd /root/.openclaw/workspace
mkdir -p portfolio/accounts data dashboard scripts

# 成功标准：ls portfolio/accounts data dashboard scripts 都存在
```

### Step 2：初始化账户数据

```bash
# 复制模板（或从本 Skill 的 data/ 目录复制）
cp <skill目录>/data/accounts_template.json portfolio/accounts/structure.json
cp <skill目录>/data/watchlist_template.json portfolio/watchlist.json

# 初始化空文件
echo '[]' > portfolio/pnl_log.json
echo '{}' > data/portfolio_prices.json
echo '[]' > data/daily_signals.json
```

**验证**：
```bash
python3 -c "import json; d=json.load(open('portfolio/accounts/structure.json')); print(f'✅ {len(d[\"accounts\"])} 个账户就绪')"
# 成功标准：输出 "✅ 3 个账户就绪"
```

### Step 3：复制脚本

```bash
cp <skill目录>/scripts/portfolio_scanner.py scripts/
cp <skill目录>/scripts/simulate_pnl.py scripts/
cp <skill目录>/scripts/cron_dashboard_update.py scripts/
cp <skill目录>/scripts/push_dashboard_to_github.sh scripts/
chmod +x scripts/push_dashboard_to_github.sh
```

### Step 4：配置你的凭证

编辑 `scripts/push_dashboard_to_github.sh`：
```bash
GITHUB_TOKEN="<你的GitHub Token>"
GITHUB_USER="<你的GitHub用户名>"
REPO_NAME="<你的Dashboard仓库名>"
```

编辑 `scripts/portfolio_scanner.py` 顶部：
```python
AISA_KEY = "<你的AISA API Key>"  # 可选，没有就注释掉 AISA 相关函数
```

编辑 `scripts/simulate_pnl.py`：
```python
KEY = "<你的Tavily API Key>"  # 可选，没有就用 Stooq
```

### Step 5：创建 GitHub 仓库

```bash
# 创建空仓库用于 Dashboard
curl -s -H "Authorization: token <你的GitHub Token>" \
  https://api.github.com/user/repos \
  -d '{"name":"<你的Dashboard仓库名>","public":true}'
# 成功标准：返回 JSON 含 "full_name": "<你的用户名>/<仓库名>"
```

### Step 6：首次运行扫描器

```bash
python3 scripts/portfolio_scanner.py
# 成功标准：输出各账户持仓快照，无 ImportError
```

### Step 7：首次推送 Dashboard

```bash
bash scripts/push_dashboard_to_github.sh
# 成功标准：输出 "✅ Dashboard pushed to GitHub Pages"
# 访问：https://<你的用户名>.github.io/<仓库名>/
```

### Step 8：配置 Cron

参考 `cron_setup.md`，在 OpenClaw 中添加定时任务。

---

## 每日运行流程

### 自动（Cron 驱动）
```
04:00  扫描 — 亚洲盘前，检查隔夜美股变动
09:05  日报 — 美股收盘后推送损益
10:00  主扫描 — 信号搜索+建仓决策+推送
16:00  扫描 — 盘中异动检查
22:00  扫描 — 美股开盘后1小时
```

### 手动干预
```bash
# 手动建仓（直接编辑 accounts/structure.json）
python3 -c "
import json
with open('portfolio/accounts/structure.json') as f:
    data = json.load(f)
acc = data['accounts']['aggressive']  # 选账户
acc['positions'].append({
    'ticker': 'XXXX',
    'company': '公司名',
    'entry_price': 10.0,
    'shares': 500,
    'cost_basis': 5000,
    'current_price': 10.0,
    'current_value': 5000,
    'unrealized_pnl': 0,
    'unrealized_pnl_pct': 0,
    'entry_date': '2026-01-01',
    'hold_days_target': 14,
    'target_price': 15.0,
    'stop_loss': 8.0,
    'thesis': '买入理由',
    'signal_source': '信号来源'
})
acc['cash'] -= 5000
with open('portfolio/accounts/structure.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('✅ 建仓完成')
"

# 手动平仓
# 从 positions 中移除 + 加回 cash + 写入 closed_positions + trade_log
```

---

## 自定义指南

### 换票池
编辑 `portfolio/watchlist.json`，在对应账户数组中添加条目：

```json
{
  "ticker": "NVDA",
  "company": "NVIDIA — AI芯片龙头",
  "trigger_price": 100.0,
  "trigger_mode": "pullback_entry",
  "target_exit": 150.0,
  "stop_loss": 85.0,
  "auto_trigger": true,
  "position_pct": 0.15,
  "priority": "A",
  "status": "watch",
  "reason": "你的买入逻辑"
}
```

### 调策略参数

在 `portfolio_scanner.py` 中：
```python
# 自动触发建仓的安全阈值
deviation > 0.30  # 价格偏离触发价30%以上跳过，防烂股误买

# 最小建仓金额
invest_amount < 500  # 低于$500不建仓

# 现金保留比例
max_invest = cash * 0.8  # 始终保留20%现金
```

### 添加新价格源

在 `portfolio_scanner.py` 的 `get_prices_batch()` 中按需添加：
```python
# 优先级：Yahoo → Stooq → Tavily → 你的自定义源
p = get_price_yahoo(ticker)
if not p:
    p = get_price_stooq(ticker)
if not p:
    p = get_price_tavily(ticker)
if not p:
    p = your_custom_price_source(ticker)  # 新增
```

---

## 踩坑记录（血泪教训）

### 1. Stooq 格式
```
# ✅ 正确：ticker 小写 + .us 后缀
https://stooq.com/q/l/?s=nvda.us&f=sd2t2ohlcv&h&e=csv

# ❌ 错误：大写、无后缀
https://stooq.com/q/l/?s=NVDA&f=sd2t2ohlcv&h&e=csv
```

### 2. Yahoo Finance 限流
- 高频调用会 429，建议 `time.sleep(0.15)` 间隔
- 盘前/盘后价格可能是延迟数据

### 3. 沙箱代理
```bash
# GitHub API 走代理
https_proxy="http://127.0.0.1:8118" git push ...

# 内网 API 不走代理
curl --noproxy '*' https://internal-api.example.com
```

### 4. Cron jobs.json 格式
```json
// ✅ 正确（新版格式）
{"name": "xxx", "schedule": {"kind": "cron", "expr": "0 10 * * *", "tz": "Asia/Shanghai"}}

// ❌ 错误（旧版格式，会导致整个调度器崩溃！）
{"name": "xxx", "cron": "0 10 * * *"}
```
> ⚠️ 一个格式错误的 job 会让 ALL 41 个 cron 全挂，静默死亡无告警

### 5. 止损逻辑
- 止损是**硬规则**：`current_price <= stop_loss` 立即平仓
- 不要手动调低止损（除非有新的强催化剂）
- 偏离触发价超 30% 的建仓会被自动跳过（防崩盘股误入）

### 6. Dashboard 推送
- 每次有任何持仓变动都必须推送，不推 = 没完成
- `git push -f` 会覆盖历史，保持仓库干净
- GitHub Pages 更新需要 1-2 分钟生效

### 7. 价格铁律
- **永远不用新闻/推特里的价格直接建仓**
- 必须 Stooq/Yahoo 实时确认
- 超过 30 天的历史价格一律重新获取

---

## 系统铁律（不可违反）

1. **价格实时验证** — 建仓前必须 Yahoo/Stooq 确认当前价
2. **Dashboard 必须同步** — 有变动就推送，不推 = 没完成
3. **止损硬执行** — 触发即平仓，无例外
4. **现金保留** — 每账户始终保留 ≥20% 现金
5. **单票仓位上限** — 大机构 20%，激进 10%，蓝虾 15%
6. **cron 格式校验** — 每次编辑 jobs.json 后必须验证 `openclaw cron list` 正常

---

## 快速验证清单

部署完成后逐项确认：

```
[ ] python3 scripts/portfolio_scanner.py 无报错
[ ] python3 scripts/simulate_pnl.py 能获取价格
[ ] bash scripts/push_dashboard_to_github.sh 输出 ✅
[ ] GitHub Pages 链接可访问
[ ] accounts/structure.json 三个账户正确
[ ] watchlist.json 格式正确
[ ] openclaw cron list 显示所有 job（无 TypeError）
```

---

## 文件清单

```
trading-system-skill/
├── SKILL.md                          # 本文件
├── cron_setup.md                     # Cron 配置示例
├── scripts/
│   ├── portfolio_scanner.py          # 核心扫描器（714行）
│   ├── simulate_pnl.py              # 每日损益计算（188行）
│   ├── cron_dashboard_update.py     # Dashboard 更新入口（115行）
│   └── push_dashboard_to_github.sh  # GitHub Pages 推送（29行）
└── data/
    ├── accounts_template.json        # 三账户初始化模板
    └── watchlist_template.json       # Watchlist 模板
```

总代码量：~1100行 Python + 30行 Bash + 配置文件
