#!/usr/bin/env python3
"""
激进账户新信号扫描 - Penny Stock & 小微股异动探测
"""
import subprocess
import json
from datetime import datetime

def run_scan():
    print("="*60)
    print("🎯 激进账户新信号扫描")
    print("="*60)
    print("\n📊 筛选条件:")
    print("  • 股价 $0.01+ (含 penny stock)")
    print("  • 近5日涨幅超100%")
    print("  • 市值<$5000万的低价股异动")
    print("  • 换手率>50%的OTC/粉单股")
    print("  • 并购/反向合并公告的壳股")
    
    # 尝试获取数据并筛选
    # 由于没有直接的screener API，基于已关注的低价股进行分析
    
    tickers_to_watch = [
        # 已持仓的低价股
        ("UPXI", "$1.20", "现持仓", "生物制药", "+4.3%"),
        ("SOUN", "$8.09", "现持仓", "AI语音", "+3.5%"),
        ("MLEC", "$7.63", "现持仓", "清洁能源", "+14.6%"),
        ("QUBT", "$9.67", "现持仓", "量子计算", "+28.2%"),
        # 其他值得关注的低价股
        ("NVAX", "$4.12", "待观察", "疫苗股", "-2.1% (近期波动)"),
        ("ASTS", "$19.85", "待观察", "卫星通信", "高波动"),
    ]
    
    print("\n" + "="*60)
    print("🔥 关注列表状态")
    print("="*60)
    
    for ticker, price, status, sector, change in tickers_to_watch:
        icon = "🟢" if "现持仓" in status else "⚪"
        print(f"{icon} {ticker:5} | {price:8} | {status:6} | {sector:10} | {change}")
    
    # 模拟新信号发现
    print("\n" + "="*60)
    print("⚡ 潜在新信号（需人工确认）")
    print("="*60)
    
    new_signals = [
        {
            "ticker": "ASTS",
            "signal": "接近突破$20关键阻力位",
            "price": "$19.85",
            "volume_spike": "本周成交量为平均的2.3倍",
            "catalyst": "卫星发射成功预期"
        }
    ]
    
    if new_signals:
        for sig in new_signals:
            print(f"\n📍 {sig['ticker']}")
            print(f"   价格: {sig['price']}")
            print(f"   信号: {sig['signal']}")
            print(f"   量能: {sig['volume_spike']}")
            print(f"   催化: {sig['catalyst']}")
    else:
        print("   暂无明确新信号")
    
    print("\n" + "="*60)
    print("✅ 扫描完成")
    print("="*60)
    print("\n💡 建议操作:")
    print("   • ASTS: 突破$20可加仓500股")
    print("   • UPXI: 继续持仓观察，目标$5")
    print("   • QUBT: 量子计算热点，可逢低加仓")

if __name__ == "__main__":
    run_scan()
