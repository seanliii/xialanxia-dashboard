#!/usr/bin/env python3
"""
Polymarket 智能交易机器人
整合预测 Agent + 执行 Agent + 风控系统

使用方法：
    # 模拟模式（不需要私钥）
    python trading_bot.py --simulate
    
    # 实盘模式（需要配置钱包）
    export POLYGON_PRIVATE_KEY="your_key"
    python trading_bot.py --live
    
    # 单次扫描
    python trading_bot.py --scan
"""
import argparse
import json
import time
from datetime import datetime, timezone
from typing import Dict, List

from prediction_agent import PredictionAgent
from execution_agent import ExecutionAgent
from polymarket_client import PolymarketDataClient
from aisa_client import AISATwitterClient
from config import MIN_CONFIDENCE_SCORE, MIN_EDGE_THRESHOLD


class TradingBot:
    """
    Polymarket 交易机器人
    
    双 Agent 架构：
    - 预测 Agent: 分析市场、生成信号
    - 执行 Agent: 风控检查、下单执行
    """
    
    def __init__(self, initial_balance: float = 1000.0, simulate: bool = True):
        self.prediction_agent = PredictionAgent()
        self.execution_agent = ExecutionAgent(initial_balance)
        self.polymarket = PolymarketDataClient()
        self.twitter = AISATwitterClient()
        
        self.simulate = simulate
        self.running = False
        
        # 交易记录
        self.trade_history: List[Dict] = []
        
        print(f"[Bot] 🤖 初始化完成")
        print(f"[Bot] 💰 初始余额: ${initial_balance}")
        print(f"[Bot] 🎮 模式: {'模拟' if simulate else '实盘'}")
    
    def scan_and_trade(self, max_trades: int = 3) -> List[Dict]:
        """
        扫描市场并执行交易
        
        Args:
            max_trades: 最大交易数
            
        Returns:
            交易结果列表
        """
        print("\n" + "=" * 50)
        print(f"🔍 扫描市场 @ {datetime.now(timezone.utc).isoformat()}")
        print("=" * 50)
        
        results = []
        
        # 1. 扫描机会
        opportunities = self.prediction_agent.scan_opportunities(limit=20)
        
        if not opportunities:
            print("[Bot] 📭 未发现符合条件的机会")
            return results
        
        print(f"[Bot] 📊 发现 {len(opportunities)} 个机会")
        
        # 2. 执行交易
        trades_executed = 0
        
        for opp in opportunities:
            if trades_executed >= max_trades:
                break
            
            market = opp["market"]
            signal = opp["signal"]
            
            print(f"\n📌 {market['question'][:50]}...")
            print(f"   Edge: {signal['edge']:.1%} | 置信度: {signal['confidence']}%")
            print(f"   建议: {signal['action']}")
            
            # 执行
            result = self.execution_agent.execute_signal(signal, market)
            results.append({
                "market": market["question"],
                "signal": signal,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
            if result["status"] in ["submitted", "simulated"]:
                trades_executed += 1
                print(f"   ✅ 执行成功")
            else:
                print(f"   ⏭️ 跳过: {result.get('reason', 'Unknown')}")
        
        # 保存记录
        self.trade_history.extend(results)
        
        return results
    
    def run_loop(self, interval_minutes: int = 30):
        """
        循环扫描模式
        
        Args:
            interval_minutes: 扫描间隔（分钟）
        """
        self.running = True
        print(f"[Bot] 🔄 启动循环扫描，间隔 {interval_minutes} 分钟")
        print("[Bot] 💡 按 Ctrl+C 停止")
        
        try:
            while self.running:
                self.scan_and_trade()
                
                # 打印状态
                self._print_status()
                
                # 等待
                print(f"\n⏰ 下次扫描: {interval_minutes} 分钟后...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n[Bot] ⏹️ 用户停止")
            self.running = False
    
    def _print_status(self):
        """打印状态"""
        status = self.execution_agent.get_status()
        risk = status["risk_status"]
        
        print("\n📊 当前状态:")
        print(f"   💰 余额: ${risk['current_balance']:.2f}")
        print(f"   📈 今日盈亏: ${risk['daily_pnl']:.2f} ({risk['daily_pnl_pct']:.1f}%)")
        print(f"   📝 今日交易: {risk['daily_trades']} 笔")
        print(f"   🚦 交易状态: {'允许' if risk['trading_allowed'] else '暂停'}")
        
        if risk["stop_reason"]:
            print(f"   ⚠️ 暂停原因: {risk['stop_reason']}")
    
    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return self.trade_history
    
    def save_history(self, filepath: str = "trade_history.json"):
        """保存交易历史"""
        with open(filepath, "w") as f:
            json.dump(self.trade_history, f, indent=2, default=str)
        print(f"[Bot] 💾 交易历史已保存: {filepath}")


def print_market_summary():
    """打印市场概览"""
    client = PolymarketDataClient()
    
    print("\n" + "=" * 60)
    print("📊 POLYMARKET 市场概览")
    print("=" * 60)
    
    # 热门市场
    print("\n🔥 热门市场 (24h 交易量排序):")
    markets = client.get_markets(limit=5, order_by="volume24hr")
    for i, m in enumerate(markets, 1):
        prices = m.get("outcome_prices", [])
        yes_price = float(prices[0]) if prices else 0.5
        print(f"\n  {i}. {m['question'][:60]}...")
        print(f"     💵 24h Volume: ${m['volume_24h']:,.0f}")
        print(f"     📊 Yes Price: {yes_price:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Polymarket 智能交易机器人")
    parser.add_argument("--simulate", action="store_true", help="模拟模式（默认）")
    parser.add_argument("--live", action="store_true", help="实盘模式")
    parser.add_argument("--scan", action="store_true", help="单次扫描")
    parser.add_argument("--loop", action="store_true", help="循环扫描")
    parser.add_argument("--interval", type=int, default=30, help="扫描间隔（分钟）")
    parser.add_argument("--balance", type=float, default=1000, help="初始余额")
    parser.add_argument("--market", action="store_true", help="显示市场概览")
    
    args = parser.parse_args()
    
    # 显示市场概览
    if args.market:
        print_market_summary()
        return
    
    # 创建机器人
    simulate = not args.live
    bot = TradingBot(initial_balance=args.balance, simulate=simulate)
    
    if args.loop:
        # 循环模式
        bot.run_loop(interval_minutes=args.interval)
    else:
        # 单次扫描
        results = bot.scan_and_trade()
        
        # 保存结果
        if results:
            bot.save_history()
        
        # 打印状态
        bot._print_status()


if __name__ == "__main__":
    main()
