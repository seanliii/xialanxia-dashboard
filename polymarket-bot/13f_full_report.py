#!/usr/bin/env python3
"""
13F 机构持仓变动日报 — 完整版
数据来源：SEC EDGAR 直接解析 Q4 2025 13F 文件
每天 18:00 发送
"""
import requests, xml.etree.ElementTree as ET, json, os, sys
from datetime import datetime, timezone
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from aisa_full_client import (
    perplexity_search, ai_chat, twitter_search
)

# ===== 免费替代：Stooq 价格 + Yahoo Finance 公司信息 =====
import csv, io, subprocess, time as _time

def get_price_stooq(ticker: str) -> dict:
    """免费获取股票价格（Stooq）"""
    sym = ticker.lower() + ".us"
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '6',
             f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'],
            capture_output=True, text=True, timeout=8)
        reader = csv.DictReader(io.StringIO(r.stdout))
        for row in reader:
            close = float(row.get('Close') or 0)
            open_ = float(row.get('Open') or close)
            chg = (close - open_) / open_ * 100 if open_ else 0
            return {'price': close, 'chg_pct': round(chg, 2), 'date': row.get('Date', '')}
    except:
        pass
    return {}

def financial_company(ticker: str) -> dict:
    """免费获取公司行业信息（Yahoo Finance summary）"""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=assetProfile",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json().get('quoteSummary', {}).get('result', [{}])[0]
        profile = data.get('assetProfile', {})
        return {
            'sector': profile.get('sector', ''),
            'industry': profile.get('industry', ''),
            'description': profile.get('longBusinessSummary', '')[:200]
        }
    except:
        return {}

def financial_metrics(ticker: str) -> dict:
    """免费获取财务指标（Yahoo Finance key statistics）"""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=defaultKeyStatistics,financialData",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json().get('quoteSummary', {}).get('result', [{}])[0]
        stats = data.get('defaultKeyStatistics', {})
        fin = data.get('financialData', {})
        def val(d, k):
            v = d.get(k, {})
            return v.get('raw') if isinstance(v, dict) else v
        return {
            'pe_ratio': val(stats, 'forwardPE') or val(stats, 'trailingPE'),
            'roe': val(fin, 'returnOnEquity'),
            'revenue_growth': val(fin, 'revenueGrowth'),
        }
    except:
        return {}

HEADERS = {"User-Agent": "XiaLanXia/1.0 admin@example.com"}

# ===== 顶级机构列表（CIK + 名称）=====
TOP_INSTITUTIONS = [
    ("Berkshire Hathaway",      "0001067983"),
    ("Tiger Global Management", "0001167483"),
    ("Coatue Management",       "0001336032"),
    ("Third Point",             "0001040273"),
    ("D.E. Shaw",               "0001009207"),
    ("Renaissance Technologies","0001037389"),
    ("Two Sigma Investments",   "0001179392"),
    ("Millennium Management",   "0001273087"),
    ("Lone Pine Capital",       "0001463981"),
    ("Pershing Square",         "0001336528"),
]

# CUSIP → Ticker 常用映射（SEC 里用 CUSIP，需要转换）
CUSIP_TICKER = {
    # Berkshire Q4 2025 真实持仓映射
    "037833100": "AAPL",   "025816109": "AXP",    "060505104": "BAC",
    "191216100": "KO",     "166764100": "CVX",    "615369105": "MCO",
    "674599105": "OXY",    "H1467J104": "CB",     "500754106": "KHC",
    "02079K305": "GOOGL",  "23918K108": "DVA",    "501044101": "KR",
    "92826C839": "V",      "829933100": "SIRI",   "57636Q104": "MA",
    "92343E102": "VRSN",   "21036P108": "STZ",    "14040H105": "COF",
    "91324P102": "UNH",    "25754A201": "DPZ",    "02005N100": "ALLY",
    "G0403H108": "AON",    "670346105": "NUE",    "526057104": "LEN",
    "023135106": "AMZN",   "650111107": "NYT",    "73278L105": "POOL",
    "16119P108": "CHTR",   "530909308": "LLYVK",
    # 科技/AI/成长股
    "594918104": "MSFT",   "30303M102": "META",   "88160R101": "TSLA",
    "67066G104": "NVDA",   "855244109": "TSM",    "46120E602": "PLTR",
    "40434L105": "CRWD",   "025537101": "AVGO",   "007903107": "AMD",
    "00507V109": "ARM",    "833445100": "SNOW",   "882184108": "TXN",
    "808513105": "SCHW",   "17275R102": "CSCO",   "458140100": "INTC",
    "742718109": "PG",     "345370860": "F",      "09367V508": "SPY",
    "464287655": "IVV",    "78462F103": "SPY",    "595112103": "MU",
    "64110L106": "NFLX",   "22266T109": "CPNG",   "03831W108": "APP",
    "655844108": "NSC",    "22160N109": "CSGP",   "874039100": "TSM",
    "199908005": "FIX",    "49177J102": "KVUE",   "11135F101": "AVGO",
    "931142103": "WMT",    "09857L108": "BKNG",   "023608102": "AXP",
}

def cusip_to_ticker(cusip: str) -> str:
    return CUSIP_TICKER.get(cusip, cusip[:6])


def get_latest_13f(cik: str, institution_name: str) -> dict:
    """获取机构最新 13F 文件信息"""
    try:
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                        headers=HEADERS, timeout=15)
        data = r.json()
        filings = data['filings']['recent']
        for i, form in enumerate(filings['form']):
            if form == '13F-HR':
                return {
                    "name": institution_name, "cik": cik,
                    "filing_date": filings['filingDate'][i],
                    "accession": filings['accessionNumber'][i],
                    "period": filings.get('reportDate', [''])[i] if 'reportDate' in filings else "2025-12-31"
                }
    except:
        pass
    return None


def parse_13f_holdings(cik: str, accession: str) -> list:
    """解析 13F 持仓 XML"""
    holdings = []
    try:
        cik_num = str(int(cik))
        acc_clean = accession.replace('-', '')
        
        # 获取文件列表
        idx_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{acc_clean}/"
        r = requests.get(idx_url, headers=HEADERS, timeout=15)
        
        import re
        # 找 infotable 或最大的 XML 文件（持仓明细）
        all_xmls = re.findall(r'href="(/Archives/edgar/data/[^"]+\.xml)"', r.text)
        
        # 优先找 infotable，否则取第一个非 primary_doc 的 XML
        data_xml = None
        for xml in all_xmls:
            if 'primary_doc' not in xml:
                data_xml = xml
                break
        if not data_xml and all_xmls:
            data_xml = all_xmls[0]
        
        if not data_xml:
            return []
        
        xml_url = f"https://www.sec.gov{data_xml}"
        xr = requests.get(xml_url, headers=HEADERS, timeout=20)
        
        root = ET.fromstring(xr.text)
        ns = {'n': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
        
        # 合并同一 CUSIP 的多条记录
        holdings_map = defaultdict(lambda: {"name": "", "cusip": "", "value": 0, "shares": 0})
        
        for entry in root.findall('.//n:infoTable', ns):
            cusip = entry.findtext('n:cusip', '', ns)
            name = entry.findtext('n:nameOfIssuer', '', ns)
            value = int(entry.findtext('n:value', '0', ns))
            shares_el = entry.find('.//n:sshPrnamt', ns)
            shares = int(shares_el.text) if shares_el is not None and shares_el.text.isdigit() else 0
            
            holdings_map[cusip]['name'] = name
            holdings_map[cusip]['cusip'] = cusip
            holdings_map[cusip]['value'] += value * 1000  # 单位是千美元
            holdings_map[cusip]['shares'] += shares
        
        holdings = sorted(holdings_map.values(), key=lambda x: x['value'], reverse=True)
        return holdings
        
    except Exception as e:
        return []


def compare_holdings(curr: list, prev: list) -> dict:
    """比较两期持仓，找出增减仓和新建仓"""
    curr_map = {h['cusip']: h for h in curr}
    prev_map = {h['cusip']: h for h in prev}
    
    increased = []  # 增仓
    decreased = []  # 减仓
    new_pos = []    # 新建仓
    closed_pos = [] # 清仓
    
    for cusip, h in curr_map.items():
        if cusip not in prev_map:
            new_pos.append(h)
        else:
            prev_val = prev_map[cusip]['value']
            curr_val = h['value']
            change_pct = (curr_val / prev_val - 1) * 100 if prev_val > 0 else 0
            if change_pct > 10:
                increased.append({**h, "change_pct": change_pct, "prev_value": prev_val})
            elif change_pct < -10:
                decreased.append({**h, "change_pct": change_pct, "prev_value": prev_val})
    
    for cusip, h in prev_map.items():
        if cusip not in curr_map:
            closed_pos.append(h)
    
    return {
        "increased": sorted(increased, key=lambda x: x['value'], reverse=True),
        "decreased": sorted(decreased, key=lambda x: abs(x['change_pct']), reverse=True),
        "new_positions": sorted(new_pos, key=lambda x: x['value'], reverse=True),
        "closed_positions": sorted(closed_pos, key=lambda x: x['value'], reverse=True),
    }


def get_prev_13f(cik: str) -> list:
    """获取上一期 13F 持仓（用于对比）"""
    try:
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                        headers=HEADERS, timeout=15)
        data = r.json()
        filings = data['filings']['recent']
        found = []
        for i, form in enumerate(filings['form']):
            if form == '13F-HR':
                found.append({"accession": filings['accessionNumber'][i], "date": filings['filingDate'][i]})
                if len(found) >= 2:
                    break
        
        if len(found) >= 2:
            return parse_13f_holdings(cik, found[1]['accession'])
    except:
        pass
    return []


def get_stock_6m_performance(ticker: str) -> str:
    """获取股票近 6 个月表现"""
    try:
        result = perplexity_search(
            f"What is {ticker} stock price performance in the last 6 months? Give current price, 6-month % change, and 3-sentence reason for the trend. Be concise.",
            model="sonar"
        )
        return result['answer'][:250]
    except:
        return "数据获取中..."


def generate_full_13f_report() -> str:
    """生成完整 13F 日报"""
    today = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
    
    print("📥 获取头部机构 13F 数据...", flush=True)
    
    # 收集所有机构的持仓变动
    all_buys = []    # [(机构名, 股票名, CUSIP, 市值, 变动%)]
    all_sells = []
    all_new = []
    
    institution_summaries = []
    
    for inst_name, cik in TOP_INSTITUTIONS[:8]:  # 先做 8 家
        print(f"  处理 {inst_name}...", flush=True)
        
        filing = get_latest_13f(cik, inst_name)
        if not filing:
            continue
        
        curr_holdings = parse_13f_holdings(cik, filing['accession'])
        prev_holdings = get_prev_13f(cik)
        
        if not curr_holdings:
            continue
        
        changes = compare_holdings(curr_holdings, prev_holdings)
        
        # 收集增仓
        for h in changes['increased'][:5]:
            ticker = cusip_to_ticker(h['cusip'])
            all_buys.append({
                "institution": inst_name,
                "ticker": ticker,
                "name": h['name'],
                "value": h['value'],
                "change_pct": h.get('change_pct', 0),
                "cusip": h['cusip'],
            })
        
        # 收集减仓
        for h in changes['decreased'][:5]:
            ticker = cusip_to_ticker(h['cusip'])
            all_sells.append({
                "institution": inst_name,
                "ticker": ticker,
                "name": h['name'],
                "value": h['value'],
                "change_pct": h.get('change_pct', 0),
                "cusip": h['cusip'],
            })
        
        # 收集新建仓
        for h in changes['new_positions'][:3]:
            ticker = cusip_to_ticker(h['cusip'])
            all_new.append({
                "institution": inst_name,
                "ticker": ticker,
                "name": h['name'],
                "value": h['value'],
                "cusip": h['cusip'],
            })
        
        institution_summaries.append({
            "name": inst_name,
            "total_value": sum(h['value'] for h in curr_holdings),
            "top3": [cusip_to_ticker(h['cusip']) for h in curr_holdings[:3]],
            "new_count": len(changes['new_positions']),
            "increased_count": len(changes['increased']),
            "decreased_count": len(changes['decreased']),
        })
    
    # 按市值排序
    all_buys.sort(key=lambda x: x['value'], reverse=True)
    all_sells.sort(key=lambda x: abs(x['value']), reverse=True)
    all_new.sort(key=lambda x: x['value'], reverse=True)
    
    # 获取 Perplexity 实时 13F 动态
    print("🌐 Perplexity 查实时 13F 动态...", flush=True)
    perp = perplexity_search(
        "Latest Q4 2025 13F filings: what did top hedge funds Berkshire, Tiger Global, Citadel, Point72 buy and sell? Any major position changes? New positions in AI or tech?",
        model="sonar"
    )
    
    # AI 综合分析
    print("🤖 AI 生成分析...", flush=True)
    buy_summary = "\n".join([f"- {b['institution']} 增仓 ${b['ticker']}({b['name'][:20]}) +{b['change_pct']:.0f}% 市值${b['value']/1e6:.0f}M" for b in all_buys[:10]])
    sell_summary = "\n".join([f"- {s['institution']} 减仓 ${s['ticker']}({s['name'][:20]}) {s['change_pct']:.0f}% 市值${s['value']/1e6:.0f}M" for s in all_sells[:10]])
    new_summary = "\n".join([f"- {n['institution']} 新建仓 ${n['ticker']}({n['name'][:20]}) 市值${n['value']/1e6:.0f}M" for n in all_new[:10]])
    
    ai_analysis = ai_chat(
        f"""基于 Q4 2025 13F 机构持仓变动，给出专业分析：

增仓：\n{buy_summary}
减仓：\n{sell_summary}
新建仓：\n{new_summary}

分析要点：
1. 机构最看好什么板块/方向？
2. 在回避什么？
3. 有哪些反共识或有趣的操作？
4. 对普通投资者的参考信号是什么？

请用中文，3-4段，专业但可读。""",
        model="gpt-4.1", max_tokens=600
    )
    
    # ===== 构建报告 =====
    report = f"""**📊 13F 机构持仓变动日报 | {today} 18:00**
*Q4 2025（截至2025年12月31日） | 来源：SEC EDGAR*

---

**🟢 头部机构增仓 TOP 20**

"""
    for i, b in enumerate(all_buys[:20], 1):
        ticker = b['ticker']
        company_name = b['name']
        # 简短公司介绍（只对前5名做详细介绍）
        if i <= 5:
            co_info = financial_company(ticker)
            sector = co_info.get('sector', '')
            industry = co_info.get('industry', '')
            co_desc = f"（{sector}·{industry}）" if sector else ""
        else:
            co_desc = ""
        
        report += f"**{i}. {b['institution']}** → **${ticker}**\n"
        report += f"   {company_name[:25]}{co_desc}\n"
        report += f"   增仓 **+{b['change_pct']:.0f}%** | 当前持仓 **${b['value']/1e6:.0f}M**\n\n"
    
    report += "\n---\n\n**🔴 头部机构减仓 TOP 20**\n\n"
    
    for i, s in enumerate(all_sells[:20], 1):
        report += f"**{i}. {s['institution']}** → **${s['ticker']}**\n"
        report += f"   {s['name'][:25]}\n"
        report += f"   减仓 **{s['change_pct']:.0f}%** | 当前持仓 **${s['value']/1e6:.0f}M**\n\n"
    
    report += "\n---\n\n**🆕 重要新建仓（头部仓位）**\n\n"
    
    for i, n in enumerate(all_new[:20], 1):
        report += f"**{i}. {n['institution']}** 新买入 **${n['ticker']}**\n"
        report += f"   {n['name'][:30]} | 建仓规模 **${n['value']/1e6:.0f}M**\n\n"
    
    # 重点股票详情（TOP 5 增仓的股票）
    report += "\n---\n\n**🔍 重点标的详情（TOP 5 增仓）**\n\n"
    
    seen_tickers = set()
    detail_count = 0
    for b in all_buys:
        ticker = b['ticker']
        if ticker in seen_tickers or len(ticker) > 5:
            continue
        seen_tickers.add(ticker)
        detail_count += 1
        
        if detail_count > 5:
            break
        
        print(f"  获取 {ticker} 详情...", flush=True)
        perf = get_stock_6m_performance(ticker)
        m = financial_metrics(ticker)
        
        report += f"**${ticker}** — {b['name'][:30]}\n"
        if m.get('pe_ratio'):
            report += f"PE={m['pe_ratio']:.1f} | ROE={m.get('roe',0):.1%} | 营收增速={m.get('revenue_growth',0):.1%}\n"
        report += f"📈 近半年：{perf[:200]}\n\n"
    
    # AI 分析
    report += f"\n---\n\n**💡 AI 综合分析**\n\n{ai_analysis}\n"
    
    # Perplexity 实时动态
    report += f"\n---\n\n**📡 实时 13F 动态（Perplexity Sonar）**\n\n{perp['answer'][:500]}\n"
    if perp.get('citations'):
        report += "\n📎 来源：\n"
        for c in perp['citations'][:3]:
            report += f"- {c}\n"
    
    report += f"\n\n---\n🦐 小蓝虾 | {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')} CST"
    
    return report


if __name__ == "__main__":
    print("🚀 开始生成 13F 机构持仓日报...\n", flush=True)
    report = generate_full_13f_report()
    
    print("\n" + "="*70)
    print(report[:3000])
    print("="*70)
    
    # 保存
    with open("/tmp/13f_report_latest.txt", "w") as f:
        f.write(report)
    print("\n✅ 完整报告已保存到 /tmp/13f_report_latest.txt")
    print(f"📏 报告长度: {len(report)} 字符")
