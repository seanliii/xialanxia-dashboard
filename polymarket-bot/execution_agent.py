"""
执行 Agent — 只负责下单执行，不做分析决策
采用双 Agent 架构中的「执行层」
包含完整风控模块
"""
import os
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, List

from config import (
    CLOB_API,
    POLYGON_PRIVATE_KEY,
    POLYGON_WALLET_ADDRESS,
    MAX_SINGLE_BET_RATIO,
    MAX_DAILY_LOSS_RATIO,
    MIN_CONFIDENCE_SCORE,
)


class RiskManager:
    """风控管理器 — Claude +1322% vs OpenClaw 清零的教训"""
    
    def __init__(self, initial_balance: float):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.daily_pnl = 0.0
        self.daily_trades = []
        self.last_reset_date = datetime.now(timezone.utc).date()
        
        # 风控参数
        self.max_single_bet = MAX_SINGLE_BET_RATIO  # 5%
        self.max_daily_loss = MAX_DAILY_LOSS_RATIO  # 15%
        
        # 状态
        self.is_trading_allowed = True
        self.stop_reason = None
    
    def check_daily_reset(self):
        """每日重置"""
        today = datetime.now(timezone.utc).date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = []
            self.last_reset_date = today
            self.is_trading_allowed = True
            self.stop_reason = None
            print("[风控] 🔄 每日重置完成")
    
    def calculate_position_size(
        self,
        edge: float,
        confidence: int,
        win_prob: float,
    ) -> float:
        """
        凯利公式计算仓位
        
        Kelly % = (bp - q) / b
        b = odds (赔率)
        p = win probability
        q = 1 - p
        
        Args:
            edge: 预期边际收益
            confidence: 置信度 (0-100)
            win_prob: 获胜概率
            
        Returns:
            建议仓位比例
        """
        if edge <= 0 or confidence < MIN_CONFIDENCE_SCORE:
            return 0.0
        
        # 计算赔率 (假设 binary market，win pays 1)
        odds = 1 / win_prob - 1 if win_prob > 0 else 0
        
        if odds <= 0:
            return 0.0
        
        # 凯利公式
        kelly = (odds * win_prob - (1 - win_prob)) / odds
        
        # 打折（保守系数 0.5）
        kelly *= 0.5
        
        # 置信度调整
        kelly *= confidence / 100
        
        # 上限
        kelly = min(kelly, self.max_single_bet)
        
        # 考虑当日已亏损情况，动态降低仓位
        if self.daily_pnl < 0:
            loss_ratio = abs(self.daily_pnl) / self.current_balance
            reduction_factor = max(0, 1 - loss_ratio * 2)
            kelly *= reduction_factor
        
        return max(0, kelly)
    
    def check_trade_allowed(self, amount: float) -> tuple[bool, str]:
        """
        检查交易是否允许
        
        Returns:
            (是否允许, 原因)
        """
        self.check_daily_reset()
        
        # 已停止交易
        if not self.is_trading_allowed:
            return False, f"交易已暂停: {self.stop_reason}"
        
        # 检查单笔限额
        single_limit = self.current_balance * self.max_single_bet
        if amount > single_limit:
            return False, f"超过单笔限额 ${single_limit:.2f}"
        
        # 检查日亏损限额
        daily_loss_limit = self.initial_balance * self.max_daily_loss
        if self.daily_pnl < -daily_loss_limit:
            self.is_trading_allowed = False
            self.stop_reason = f"触发日亏损限额 -{self.max_daily_loss:.0%}"
            return False, self.stop_reason
        
        # 检查余额
        if amount > self.current_balance:
            return False, f"余额不足: ${self.current_balance:.2f}"
        
        return True, "通过"
    
    def record_trade(self, amount: float, pnl: float):
        """记录交易结果"""
        self.daily_pnl += pnl
        self.current_balance += pnl
        self.daily_trades.append({
            "amount": amount,
            "pnl": pnl,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # 检查是否触发止损
        daily_loss_limit = self.initial_balance * self.max_daily_loss
        if self.daily_pnl < -daily_loss_limit:
            self.is_trading_allowed = False
            self.stop_reason = f"触发日亏损限额 -{self.max_daily_loss:.0%}"
            print(f"[风控] ⛔ {self.stop_reason}")
    
    def get_status(self) -> Dict:
        """获取风控状态"""
        return {
            "trading_allowed": self.is_trading_allowed,
            "stop_reason": self.stop_reason,
            "current_balance": self.current_balance,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": self.daily_pnl / self.initial_balance * 100,
            "daily_trades": len(self.daily_trades),
            "max_single_bet": self.max_single_bet,
            "max_daily_loss": self.max_daily_loss,
        }


class ExecutionAgent:
    """
    执行 Agent — 纯执行层
    
    ⚠️ 需要配置钱包私钥才能实际下单
    """
    
    def __init__(self, initial_balance: float = 1000.0):
        self.risk_manager = RiskManager(initial_balance)
        
        # 交易客户端（需要 py-clob-client）
        self.clob_client = None
        self._init_clob_client()
        
        # 模拟模式
        self.simulation_mode = not bool(POLYGON_PRIVATE_KEY)
        if self.simulation_mode:
            print("[执行] ⚠️ 未配置私钥，进入模拟模式")
        
        # 订单记录
        self.orders: List[Dict] = []
    
    def _init_clob_client(self):
        """初始化 CLOB 客户端"""
        if not POLYGON_PRIVATE_KEY:
            return
        
        try:
            from py_clob_client.client import ClobClient
            self.clob_client = ClobClient(
                host=CLOB_API,
                chain_id=137,  # Polygon
                key=POLYGON_PRIVATE_KEY,
            )
            print("[执行] ✅ CLOB 客户端初始化成功")
        except ImportError:
            print("[执行] ⚠️ 未安装 py-clob-client，pip install py-clob-client")
        except Exception as e:
            print(f"[执行] ❌ CLOB 客户端初始化失败: {e}")
    
    def execute_signal(self, signal: Dict, market: Dict) -> Dict:
        """
        执行交易信号
        
        Args:
            signal: 预测 Agent 生成的信号
            market: 市场数据
            
        Returns:
            执行结果
        """
        action = signal.get("action", "hold")
        if action == "hold":
            return {"status": "skipped", "reason": "信号为 HOLD"}
        
        # 计算仓位
        position_ratio = self.risk_manager.calculate_position_size(
            edge=signal["edge"],
            confidence=signal["confidence"],
            win_prob=signal["predicted_prob"],
        )
        
        if position_ratio <= 0:
            return {"status": "skipped", "reason": "仓位计算为 0"}
        
        amount = self.risk_manager.current_balance * position_ratio
        
        # 风控检查
        allowed, reason = self.risk_manager.check_trade_allowed(amount)
        if not allowed:
            return {"status": "blocked", "reason": reason}
        
        # 确定买入方向
        token_ids = market.get("clob_token_ids", [])
        if len(token_ids) < 2:
            return {"status": "error", "reason": "无效的 token IDs"}
        
        if action == "buy_yes":
            token_id = token_ids[0]
            side = "YES"
            price = signal["market_prob"]
        else:  # buy_no
            token_id = token_ids[1]
            side = "NO"
            price = 1 - signal["market_prob"]
        
        # 计算数量
        size = amount / price if price > 0 else 0
        
        # 执行订单
        if self.simulation_mode:
            result = self._simulate_order(market, token_id, side, price, size, amount)
        else:
            result = self._execute_order(market, token_id, side, price, size)
        
        return result
    
    def _simulate_order(
        self,
        market: Dict,
        token_id: str,
        side: str,
        price: float,
        size: float,
        amount: float,
    ) -> Dict:
        """模拟下单"""
        order = {
            "id": f"sim_{len(self.orders) + 1}",
            "market": market["question"][:50],
            "token_id": token_id,
            "side": side,
            "price": price,
            "size": size,
            "amount": amount,
            "status": "simulated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.orders.append(order)
        
        # 模拟扣款
        self.risk_manager.record_trade(amount, -amount * 0.001)  # 假设 0.1% 手续费
        
        print(f"[执行] 📝 模拟下单: {side} ${amount:.2f} @ {price:.2%}")
        
        return {
            "status": "simulated",
            "order": order,
        }
    
    def _execute_order(
        self,
        market: Dict,
        token_id: str,
        side: str,
        price: float,
        size: float,
    ) -> Dict:
        """实际下单"""
        if not self.clob_client:
            return {"status": "error", "reason": "CLOB 客户端未初始化"}
        
        try:
            # 创建订单
            order = self.clob_client.create_and_post_order({
                "token_id": token_id,
                "price": str(price),
                "size": str(size),
                "side": "BUY",
            })
            
            self.orders.append({
                "id": order.get("id"),
                "market": market["question"][:50],
                "token_id": token_id,
                "side": side,
                "price": price,
                "size": size,
                "status": "submitted",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
            print(f"[执行] ✅ 订单已提交: {order.get('id')}")
            return {"status": "submitted", "order": order}
            
        except Exception as e:
            print(f"[执行] ❌ 下单失败: {e}")
            return {"status": "error", "reason": str(e)}
    
    def get_orders(self) -> List[Dict]:
        """获取订单列表"""
        return self.orders
    
    def get_status(self) -> Dict:
        """获取执行状态"""
        return {
            "simulation_mode": self.simulation_mode,
            "clob_connected": self.clob_client is not None,
            "total_orders": len(self.orders),
            "risk_status": self.risk_manager.get_status(),
        }


# ============ 测试 ============
if __name__ == "__main__":
    print("=== 测试执行 Agent ===")
    
    # 创建执行器（模拟模式）
    executor = ExecutionAgent(initial_balance=1000)
    
    # 模拟信号
    test_signal = {
        "predicted_prob": 0.65,
        "market_prob": 0.50,
        "edge": 0.15,
        "confidence": 80,
        "action": "buy_yes",
        "reasoning": "测试信号",
    }
    
    test_market = {
        "question": "Will BTC reach $100k by end of March 2026?",
        "clob_token_ids": ["token_yes_123", "token_no_456"],
    }
    
    # 执行
    result = executor.execute_signal(test_signal, test_market)
    print(f"\n执行结果: {json.dumps(result, indent=2, default=str)}")
    
    # 状态
    status = executor.get_status()
    print(f"\n执行状态: {json.dumps(status, indent=2)}")
