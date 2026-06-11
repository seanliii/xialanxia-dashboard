#!/usr/bin/env python3
"""
13F 机构持仓变动日报生成器
数据来源：AISA Financial API + SEC EDGAR
每天 18:00 发送
"""
import requests, json, sys
from datetime import datetime, timezone
from aisa_full_client import (
    perplexity_search, twitter_search, ai_chat
)
# ❌ financial_metrics / financial_company / financial_earnings_news 已禁用（AISA Financial 太贵）
# 2026-03-19 替换为 Yahoo Finance（免费）

def financial_company(ticker: str) -> dict:
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=assetProfile",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        profile = r.json().get('quoteSummary', {}).get('result', [{}])[0].get('assetProfile', {})
        return {'sector': profile.get('sector', ''), 'industry': profile.get('industry', '')}
    except:
        return {}

def financial_metrics(ticker: str) -> dict:
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=defaultKeyStatistics,financialData",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json().get('quoteSummary', {}).get('result', [{}])[0]
        stats = data.get('defaultKeyStatistics', {})
        fin = data.get('financialData', {})
        def val(d, k):
            v = d.get(k, {}); return v.get('raw') if isinstance(v, dict) else v
        return {'pe_ratio': val(stats, 'forwardPE') or val(stats, 'trailingPE'),
                'roe': val(fin, 'returnOnEquity'), 'revenue_growth': val(fin, 'revenueGrowth')}
    except:
        return {}

def financial_earnings_news(ticker: str) -> list:
    return []  # 暂不支持免费替代，返回空

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"
HEADERS = {"Authorization": f"Bearer {AISA_KEY}"}

# ============ 顶级机构 CIK 列表 ============
TOP_INSTITUTIONS = [
    ("Berkshire Hathaway", "0001067983"),
    ("Bridgewater Associates", "0001350694"),
    ("Citadel", "0001423655"),
    ("Point72", "0001603466"),
    ("D.E. Shaw", "0001009207"),
    ("Renaissance Technologies", "0001037389"),
    ("Two Sigma", "0001179392"),
    ("Millennium Management", "0001273087"),
    ("Third Point", "0001040273"),
    ("Pershing Square", "0001336528"),
    ("Tiger Global", "0001167483"),
    ("Coatue Management", "0001336032"),
    ("Lone Pine Capital", "0001040570"),
    ("Viking Global", "0001040570"),
    ("Baupost Group", "0000919012"),
]


def get_institution_13f(cik: str, institution_name: str) -> dict:
    """从 SEC EDGAR 获取机构最新 13F"""
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        r = requests.get(url, headers={"User-Agent": "XiaLanXia/1.0 admin@example.com"}, timeout=15)
        data = r.json()
        
        filings = data['filings']['recent']
        forms = filings['form']
        dates = filings['filingDate']
        accessions = filings['accessionNumber']
        
        # 找最新的 13F-HR
        for i, form in enumerate(forms):
            if form == '13F-HR':
                return {
                    "name": institution_name,
                    "cik": cik,
                    "filing_date": dates[i],
                    "accession": accessions[i],
                    "period": filings.get('reportDate', [''])[i] if 'reportDate' in filings else ""
                }
    except Exception as e:
        pass
    return {"name": institution_name, "cik": cik, "filing_date": "", "accession": ""}


def get_13f_holdings(accession: str, cik: str) -> list:
    """解析 13F 持仓文件"""
    try:
        # 构造文件 URL
        acc_clean = accession.replace('-', '')
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{accession}-index.htm"
        r = requests.get(url, headers={"User-Agent": "XiaLanXia/1.0 admin@example.com"}, timeout=15)
        
        # 从 index 页面找 infotable XML
        import re
        matches = re.findall(r'href="(/Archives/edgar/data/[^"]+\.xml)"', r.text)
        xml_files = [m for m in matches if 'infotable' in m.lower() or 'primary' in m.lower()]
        
        if not xml_files:
            return []
        
        xml_url = f"https://www.sec.gov{xml_files[0]}"
        xr = requests.get(xml_url, headers={"User-Agent": "XiaLanXia/1.0 admin@example.com"}, timeout=15)
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xr.text)
        
        holdings = []
        ns = {'n': 'http://www.sec.gov/edgar/document/thirteenf/informationTable'}
        
        for entry in root.findall('.//n:infoTable', ns)[:50]:
            name = entry.findtext('n:nameOfIssuer', '', ns)
            shares = entry.findtext('.//n:sshPrnamt', '0', ns)
            value = entry.findtext('n:value', '0', ns)
            holdings.append({
                "ticker": entry.findtext('n:cusip', '', ns),
                "name": name,
                "value": int(value) * 1000,
                "shares": int(shares) if shares.isdigit() else 0
            })
        
        holdings.sort(key=lambda x: x['value'], reverse=True)
        return holdings[:20]
    except Exception as e:
        return []


def get_top_institutional_changes() -> dict:
    """
    机构持仓变动：Yahoo Finance（免费）
    2026-03-19 从 AISA Financial API 迁移
    """
    hot_tickers = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "TSLA",
                   "TSM", "AVGO", "AMD", "PLTR", "CRWD", "SNOW"]

    buy_signals = []
    sell_signals = []
    new_positions = []

    for ticker in hot_tickers:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=institutionOwnership",
                headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            owners = r.json().get('quoteSummary', {}).get('result', [{}])[0]
            holders = owners.get('institutionOwnership', {}).get('ownershipList', [])
            if not holders:
                continue
            # Yahoo Finance 只有最新快照，用持仓%变化估算方向
            for h in holders[:5]:
                pct_change = (h.get('pctChange', {}) or {}).get('raw', 0) or 0
                pct_held = (h.get('pctHeld', {}) or {}).get('raw', 0) or 0
                val = (h.get('value', {}) or {}).get('raw', 0) or 0
                org = h.get('organization', '?')
                if pct_change > 0.1:
                    buy_signals.append({
                        'institution': org, 'ticker': ticker,
                        'change_pct': round(pct_change * 100, 1),
                        'value': val, 'shares_change': 0
                    })
                elif pct_change < -0.1:
                    sell_signals.append({
                        'institution': org, 'ticker': ticker,
                        'change_pct': round(pct_change * 100, 1),
                        'value': val, 'shares_change': 0
                    })
        except:
            continue

    return {
        "buy_signals": sorted(buy_signals, key=lambda x: x['value'], reverse=True)[:20],
        "sell_signals": sorted(sell_signals, key=lambda x: abs(x['value']), reverse=True)[:20],
        "new_positions": new_positions,
    }


def get_stock_detail(ticker: str) -> dict:
    """获取股票详细信息"""
    metrics = financial_metrics(ticker)
    company = financial_company(ticker)
    
    # 6个月股价变化（用 Perplexity）
    perp = perplexity_search(
        f"What is {ticker} stock price performance in last 6 months? Current price, 6 month change %? Brief company intro.",
        model="sonar"
    )
    
    return {
        "ticker": ticker,
        "company_name": company.get("name", ticker),
        "sector": company.get("sector", ""),
        "metrics": metrics,
        "perplexity_summary": perp["answer"][:300],
        "citations": perp["citations"][:2],
    }


def generate_13f_report() -> str:
    """生成完整的 13F 日报"""
    print("🔍 正在获取 13F 数据...", flush=True)
    
    changes = get_top_institutional_changes()
    buy_signals = changes["buy_signals"][:10]
    sell_signals = changes["sell_signals"][:10]
    new_positions = changes["new_positions"][:10]
    
    # 获取 Perplexity 的最新 13F 动态
    print("📡 获取 Perplexity 实时 13F 动态...", flush=True)
    perp_news = perplexity_search(
        "Latest 13F filings Q4 2025: which hedge funds bought and sold most? Top institutional changes this quarter? Include Berkshire, Citadel, Point72, Tiger Global.",
        model="sonar"
    )
    
    # 用 AI 生成分析摘要
    print("🤖 生成 AI 分析...", flush=True)
    
    buy_list = "\n".join([f"- {b['institution']} 增仓 {b['ticker']} +{b['change_pct']:.0f}%（市值${b['value']/1e6:.1f}M）" for b in buy_signals])
    sell_list = "\n".join([f"- {s['institution']} 减仓 {s['ticker']} {s['change_pct']:.0f}%（市值${s['value']/1e6:.1f}M）" for s in sell_signals])
    new_list = "\n".join([f"- {n['institution']} 新建仓 {n['ticker']}（市值${n['value']/1e6:.1f}M）" for n in new_positions])
    
    ai_analysis = ai_chat(
        f"""基于以下 13F 机构持仓变动数据，用2-3句话总结最重要的趋势和信号：

机构增仓 (TOP 10):
{buy_list}

机构减仓 (TOP 10):
{sell_list}

新建仓 (TOP 10):
{new_list}

Perplexity 实时信息:
{perp_news['answer'][:400]}

请总结：1）机构最看好什么方向？2）在回避什么？3）有什么反共识操作？""",
        model="gpt-4.1"
    )
    
    # 构建报告
    today = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
    
    report = f"""**📊 13F 机构持仓变动日报 | {today}**
*数据来源：SEC EDGAR Q4 2025 13F 披露*

---

**🟢 头部增仓 TOP 10**

"""
    for i, b in enumerate(buy_signals[:10], 1):
        ticker = b['ticker']
        company = financial_company(ticker)
        name = company.get('name', ticker)
        report += f"{i}. **{b['institution']}** → **${ticker}** ({name[:20]})\n"
        report += f"   增仓 **+{b['change_pct']:.0f}%** | 持仓市值 **${b['value']/1e6:.1f}M**\n\n"
    
    report += "\n---\n\n**🔴 头部减仓 TOP 10**\n\n"
    
    for i, s in enumerate(sell_signals[:10], 1):
        ticker = s['ticker']
        company = financial_company(ticker)
        name = company.get('name', ticker)
        report += f"{i}. **{s['institution']}** → **${ticker}** ({name[:20]})\n"
        report += f"   减仓 **{s['change_pct']:.0f}%** | 持仓市值 **${s['value']/1e6:.1f}M**\n\n"
    
    report += "\n---\n\n**🆕 重要新建仓**\n\n"
    
    for i, n in enumerate(new_positions[:10], 1):
        ticker = n['ticker']
        company = financial_company(ticker)
        name = company.get('name', ticker)
        report += f"{i}. **{n['institution']}** 新建仓 **${ticker}** ({name[:20]})\n"
        report += f"   {n['period']} | 持仓市值 **${n['value']/1e6:.1f}M**\n\n"
    
    report += f"\n---\n\n**💡 AI 综合分析**\n\n{ai_analysis}\n"
    
    report += f"\n---\n\n**📰 最新 13F 动态（Perplexity）**\n\n{perp_news['answer'][:500]}\n"
    
    if perp_news['citations']:
        report += "\n📎 引用：\n"
        for c in perp_news['citations'][:3]:
            report += f"- {c}\n"
    
    report += f"\n\n---\n🦐 小蓝虾 | {datetime.now(timezone.utc).strftime('%H:%M')} UTC+8"
    
    return report


if __name__ == "__main__":
    print("生成 13F 日报...")
    report = generate_13f_report()
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存到文件
    with open("/tmp/13f_report_today.txt", "w") as f:
        f.write(report)
    print("\n✅ 已保存到 /tmp/13f_report_today.txt")

