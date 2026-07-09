---
name: competitor-intel
description: "输入股票代码，5分钟生成完整竞品情报包：财务指标/分析师预期/机构持仓/最新新闻，替代昂贵数据服务"
triggers:
  - "竞品情报"
  - "研报"
  - "股票分析"
  - "competitor intel"
  - "财报分析"
---
# 竞品情报自动生成系统

## 功能说明
输入股票代码 → 自动生成包含财务指标快照、分析师预期、机构持仓变动、公司最新新闻的完整情报包。替代 Bloomberg/Wind 等昂贵数据服务，月成本 ≤$5。

## 在线使用
直接访问：https://seanliii.github.io/competitor-intel-demo/

## 本地完整版部署步骤

### Step 1：克隆项目
```bash
git clone https://github.com/seanliii/competitor-intel-demo.git
cd competitor-intel-demo
```

### Step 2：安装依赖（如使用 Python 后端版）
```bash
pip install requests python-dotenv
```
**成功判断**：`pip show requests` 有输出

### Step 3：配置 API Key（需要 FMP 免费账号）
```bash
# 注册 https://financialmodelingprep.com/ 获取免费 API Key
export FMP_API_KEY="<你的FMP API Key>"
```
**成功判断**：环境变量设置后 `echo $FMP_API_KEY` 有输出

### Step 4：运行分析
```bash
# 分析单只股票
python3 -c "
import requests, os
key = os.environ.get('FMP_API_KEY', 'demo')
ticker = 'NVDA'  # 替换为你要分析的股票代码
# 财务指标
url = f'https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={key}'
r = requests.get(url, timeout=10)
data = r.json()
if data:
    m = data[0]
    print(f'{ticker} 市盈率: {m.get(\"peRatio\", \"N/A\")}')
    print(f'{ticker} 市值: \${m.get(\"marketCap\", 0)/1e9:.1f}B')
"
```
**成功判断**：输出包含市盈率和市值数字

### Step 5：生成完整情报报告
```bash
python3 generate_report.py --ticker NVDA --output report_NVDA.md
# 或者直接用在线工具输入代码点击生成
```
**成功判断**：生成 `report_NVDA.md`，包含6个维度的情报

## 踩坑记录
- FMP 免费账号有每日请求限制（250次/天），够个人使用
- 数据延迟约15-30分钟，不适合实时交易
- 部分数据（机构持仓）只有季度更新，非每日

## 适用场景
- 个人投资者定期追踪持仓公司动态
- 替代 Bloomberg/Wind 做初步竞品研究
- 服务化：定制行业竞品报告，¥500-2000/份
