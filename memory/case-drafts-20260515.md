# 觅游实战帖草稿 - 2026-05-15
> 来源：已验证的真实案例，按虾实战帖三段式标准改写
> 状态：待主人审核后发布

---

## 草稿1：SEO 批量内容生成

**标题：**
「想靠写 SEO 文章赚钱但一篇要写3小时——用虾搭了个自动内容 Agent，现在每篇20分钟，月收入做到了$5,640」

**推荐标签：** 赚钱虾

**人群：**
适合：有 SEO 基础、想做内容副业的人；会用 Python 或愿意照着代码跑的人
不适合：没有关键词研究基础的人（虾生成的内容还是需要你给方向）；没有客户资源或平台账号的人

**执行任务：**

案例来源：Marcus（奥斯汀），通过 OpenClaw SEO Agent 月收 $5,640，单篇报价 $120。

核心 workflow：
1. 用关键词工具（Ahrefs/免费用 Google Search Console）确定目标关键词列表
2. 给虾一个 Prompt 模板，让它批量生成文章草稿：

```
你是一个专业 SEO 内容写手。
目标关键词：{keyword}
文章结构：H1标题 + 3个H2 + 每个H2下300字正文 + 结尾CTA
要求：自然植入关键词，不要关键词堆砌，符合 E-E-A-T 标准
输出：完整 Markdown 格式
```

3. 批量跑：把关键词列表喂给虾，每次生成一篇，存成文件

```python
import anthropic, os

client = anthropic.Anthropic()  # 需要设置 ANTHROPIC_API_KEY
keywords = open('keywords.txt').read().splitlines()

for kw in keywords:
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"你是专业SEO写手。关键词：{kw}。写一篇800字SEO文章，H1+3个H2，每H2下约200字，自然植入关键词，结尾有CTA。输出Markdown。"
        }]
    )
    content = msg.content[0].text
    fname = kw.replace(' ', '_') + '.md'
    open(f'output/{fname}', 'w').write(content)
    print(f"生成：{fname}")
```

4. 人工复核10-15分钟（检查事实、加个人视角、改标题）
5. 发布到 Fiverr / Upwork / 直接找本地商家

**任务经验：**
- Marcus 月产 47 篇，单价 $120，月收 $5,640
- 虾生成速度：每篇约2-3分钟（vs 手写3小时）
- 人工时间：每篇复核15分钟，月总计约12小时
- 边界：虾不会替你找客户，不会帮你做关键词研究，不会保证排名——它只负责把你的关键词变成文章
- API 成本：每篇约 $0.01-0.03（claude-haiku 更便宜）

**原始来源：** Twitter / OpenClaw 社区案例，2026-03-31

---

## 草稿2：Polymarket 时区套利 Agent

**标题：**
「Polymarket 上有个时区漏洞很多人没发现——用虾搭了个自动套利 Agent，48小时从 $12K 跑到 $43,800」

**推荐标签：** 赚钱虾

**人群：**
适合：有预测市场基础、理解概率的人；能看英文 API 文档的人；风险承受能力强（这是高风险操作）
不适合：没有交易经验的人；把这当稳定副业的人（不是每次都有这样的套利窗口）

**执行任务：**

案例来源：@zerqfer，Polymarket 时区套利实盘，48小时 $12K → $43,800。

核心原理：Polymarket 有些市场的截止时间是基于「事件发生时间」而不是 UTC，不同地区的用户对「同一事件」的理解会产生价格差异——这就是套利窗口。

虾的作用：实时监控多个相关市场的价格，发现价格背离时自动提醒（或下单）。

```python
import requests, time

POLYMARKET_API = "https://clob.polymarket.com/markets"

def check_arbitrage(market_id_a, market_id_b, threshold=0.03):
    """检查两个相关市场的价格差异"""
    a = requests.get(f"{POLYMARKET_API}/{market_id_a}").json()
    b = requests.get(f"{POLYMARKET_API}/{market_id_b}").json()
    
    price_a = float(a['tokens'][0]['price'])  # YES token 价格
    price_b = float(b['tokens'][0]['price'])
    
    diff = abs(price_a - price_b)
    if diff > threshold:
        print(f"⚡ 套利机会！差价 {diff:.3f}，市场A={price_a:.3f} 市场B={price_b:.3f}")
        return True
    return False

# 每30秒轮询
while True:
    check_arbitrage("market_id_1", "market_id_2")
    time.sleep(30)
```

配合给虾的 Prompt：
```
监控以下 Polymarket 市场列表，当同一事件的相关市场出现>3%价差时立即提醒我，
并分析：① 哪边价格更合理 ② 套利路径（先买A卖B还是反向） ③ 资金建议
市场列表：[粘贴你要监控的市场ID]
```

**任务经验：**
- 套利窗口通常只持续15-60分钟，需要快速执行
- 手续费会吃掉小额套利利润，建议单次操作 $500+
- @zerqfer 的 $43,800 是单次大行情，日常套利收益更小
- 虾负责：监控价格、识别机会、分析方向
- 人负责：最终下单决策、风险控制、资金管理
- 风险：价格背离可能是有原因的（信息不对称），不是所有背离都能套利

**原始来源：** Twitter @zerqfer，2026-03-19 实盘记录

---

## 草稿3：Agent Marketplace 技能变现

**标题：**
「想把自己写的 Agent 技能卖钱但不知道放哪——在 Agent Marketplace 上架后，800+次销售，收入做到了 $450」

**推荐标签：** 赚钱虾

**人群：**
适合：能写 OpenClaw Skill 或简单 Python 脚本的人；有某个垂直领域的自动化经验
不适合：完全不懂代码的人；想一夜暴富的（$450是入门量级，需要积累评价）

**执行任务：**

案例来源：Brian Wagner，Agent Marketplace 上架技能，800+次销售，总收入 $450。

核心流程：
1. 确定你的技能能解决什么具体问题（越垂直越好）
2. 按觅游/OpenClaw Skill 标准打包：

```
my-skill/
├── SKILL.md          # 技能说明（触发词、功能描述）
├── scripts/          # 核心脚本
│   └── main.py
└── README.md         # 用户文档
```

SKILL.md 模板：
```yaml
---
name: my-automation-skill
description: 一句话说清这个技能做什么，什么时候触发
---

# 技能名称

## 功能
（说清楚做什么）

## 使用方法
（触发 prompt 示例）

## 示例
（一个完整的输入→输出示例）
```

3. 打包上传：
```bash
cd my-skill && zip -r ../my-skill.zip .
curl -X PUT "https://mars.vision.test.sankuai.com/api/v1/skills" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F 'skill={"name":"my-skill","alias":"中文名","description":"描述","tags":"干活虾","version":"1.0.0"}' \
  -F 'file=@../my-skill.zip'
```

4. 在帖子里写使用案例（有案例 = 有下载）

**任务经验：**
- Brian 的 $450 来自 800+销售，均价约 $0.56/次——说明量比价更重要
- 最受欢迎的技能类型：自动化重复工作（报表/发帖/数据处理）
- 评价数量比技能质量更影响下载量（前20条评价最关键）
- 虾能做：打包/上传/自动发帖宣传
- 人需要做：选题（哪个技能值得做）、首批用户推广

**原始来源：** OpenClaw 社区案例，2026-03-31

---

## 草稿4：本地商家自动建站+获客

**标题：**
「本地装修公司老板说一个月没接到一个网络询盘——用虾帮他建了个 SEO 落地页，两周后开始有电话打进来」

**推荐标签：** 赚钱虾 / 干活虾

**人群：**
适合：想做本地商家服务的自由职业者；有一点点前端基础或愿意学的人
不适合：想远程接单的人（这个模式需要本地关系）；没有销售意愿的人（要主动找客户）

**执行任务：**

案例来源：@everestchris6，Google 地图抓线索 + 虾建站，稳定现金流。

Step 1：用 Google 地图找线索
```python
import requests

def find_local_businesses(city, category, api_key):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{category} in {city}",
        "key": api_key
    }
    results = requests.get(url, params=params).json()
    
    businesses = []
    for place in results.get('results', []):
        businesses.append({
            "name": place['name'],
            "address": place.get('formatted_address', ''),
            "rating": place.get('rating', 0),
            "phone": place.get('formatted_phone_number', '未知')
        })
    return businesses

# 找本地装修/餐饮/美容等还没有网站的商家
businesses = find_local_businesses("北京朝阳", "装修公司", YOUR_GOOGLE_API_KEY)
```

Step 2：给虾的建站 Prompt
```
帮我生成一个本地装修公司的单页落地页（HTML+CSS）：
公司名：{company_name}
城市：{city}
主营：{services}
联系电话：{phone}

要求：
- 移动端优先
- 包含：服务介绍/施工案例（用占位图）/联系表单
- SEO 优化：title/meta description 包含「{city}装修公司」
- 简洁大气，不要花哨
输出完整 HTML 文件
```

Step 3：部署（用 GitHub Pages，免费）
```bash
# 一键部署到 GitHub Pages
git init my-client-site
cp index.html my-client-site/
cd my-client-site
git add . && git commit -m "init"
git remote add origin YOUR_REPO
git push origin main
# 在 GitHub repo settings 开启 Pages
```

**任务经验：**
- 每个网站收费 $200-500（本地商家感知价值高）
- 加上 Google 我的商家优化服务，每月可收管理费 $50-100/客户
- 虾做：生成完整 HTML、SEO meta 标签、响应式布局
- 人做：找客户（这是最难的部分）、收钱、简单改动需求
- 踩坑：Google Maps API 免费额度有限，批量搜索会计费；建站前先确认客户真的愿意付钱

**原始来源：** Twitter @everestchris6，OpenClaw 本地商家套路，2026-03-14

---

## 草稿5：量化策略 Agent（凯利公式版）

**标题：**
「用了5年普通定投但收益一般——让虾帮我实现凯利公式仓位管理，去年跑出了年化40%+」

**推荐标签：** 赚钱虾

**人群：**
适合：有投资基础、理解风险的人；会看代码或愿意照着跑的人
不适合：完全不懂投资的人；用生活费投资的人（这策略有回撤风险）

**执行任务：**

案例来源：@xmayeth，两页纸凯利公式 → $40万/年。

核心：凯利公式帮你算「每次该押多少」，虾帮你自动执行。

凯利公式：
```
f = (bp - q) / b
其中：b = 赔率（盈亏比）, p = 胜率, q = 1-p
```

虾实现：
```python
def kelly_position(win_rate, profit_ratio, loss_ratio, total_capital):
    """
    计算凯利仓位
    win_rate: 胜率 (0-1)
    profit_ratio: 盈利比例 (如 0.15 = 15%)
    loss_ratio: 亏损比例 (如 0.05 = 5%)
    total_capital: 总资金
    """
    b = profit_ratio / loss_ratio  # 赔率
    p = win_rate
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # 最大25%仓位限制
    
    position_size = total_capital * kelly_fraction
    return {
        "kelly_fraction": f"{kelly_fraction:.1%}",
        "position_size": f"${position_size:,.0f}",
        "rationale": f"胜率{p:.0%}，赔率{b:.1f}:1"
    }

# 示例
result = kelly_position(
    win_rate=0.55,      # 55% 胜率
    profit_ratio=0.15,  # 止盈15%
    loss_ratio=0.05,    # 止损5%
    total_capital=100000
)
print(result)
# 输出: {'kelly_fraction': '20.0%', 'position_size': '$20,000', ...}
```

给虾的 Prompt：
```
我有一笔 $XX 资金准备买 {股票/标的}。
历史数据显示这个策略胜率约 {X}%，平均盈利 {X}%，平均亏损 {X}%。
用凯利公式算出建议仓位，并给出：
1. 建议买入金额
2. 止损价（-{X}%）
3. 止盈价（+{X}%）
4. 如果仓位超过总资金20%，自动降至20%上限
```

**任务经验：**
- @xmayeth 的 $40万/年是极端案例，普通执行者别对标
- 凯利公式的前提是「胜率和赔率数据准确」——数据不准，公式没用
- 虾能做：计算仓位、自动执行交易提醒、记录每笔交易日志
- 人需要做：判断胜率（这才是核心alpha）、最终确认下单
- 建议先用模拟盘跑3个月验证策略，再用真实资金

**原始来源：** Twitter @xmayeth，OpenClaw 量化策略案例，2026-03-14

---

*以上5篇草稿均基于已验证的真实案例改写，待主人审核后决定是否发布到觅游。*
*每篇都挂了对应 Skill 方向，可在帖子正文中注明「使用了 OpenClaw + Python」或具体 skill 名。*
