"""
Polymarket 智能交易机器人配置文件
"""
import os

# ============ AISA API 配置 ============
AISA_API_KEY = os.getenv("AISA_API_KEY", "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41")
AISA_BASE_URL = "https://api.aisa.one"

# ============ Polymarket API 配置 ============
GAMMA_API = "https://gamma-api.polymarket.com"   # 市场数据（公开）
DATA_API = "https://data-api.polymarket.com"     # 持仓/排行榜（公开）
CLOB_API = "https://clob.polymarket.com"         # 交易（需要认证）

# ============ 钱包配置 ============
# ⚠️ 需要用户填写
POLYGON_PRIVATE_KEY = os.getenv("POLYGON_PRIVATE_KEY", "")
POLYGON_WALLET_ADDRESS = os.getenv("POLYGON_WALLET_ADDRESS", "")

# ============ 风控配置 ============
MAX_SINGLE_BET_RATIO = 0.05    # 单注最大 5%（凯利公式上限）
MAX_DAILY_LOSS_RATIO = 0.15   # 单日最大亏损 15%
MIN_CONFIDENCE_SCORE = 70     # 最低置信度要求
MIN_EDGE_THRESHOLD = 0.10     # 最小边际收益 10%

# ============ 策略配置 ============
# 优先做的市场类型（可验证结果）
PREFERRED_MARKET_TAGS = [
    "weather",      # 天气（NOAA 93% 准确率）
    "sports",       # 体育
    "economics",    # 经济数据
    "crypto",       # 加密（链上数据可验证）
    "politics",     # 政治（有明确时间点）
]

# 避开的市场类型
BLACKLIST_MARKET_TAGS = [
    "culture",      # 主观判断
    "entertainment",
]

# ============ 监控的 KOL ============
TWITTER_KOLS = [
    "NateSilver538",      # Nate Silver
    "Polymarket",         # 官方
    "PM_Analytics",       # 分析
    "PolyWhaleFeed",      # 鲸鱼跟踪
    "PMTraderAdam",       # 活跃交易者
]

# ============ 时区套利配置 ============
# Polymarket 70% 用户是美国人，亚洲凌晨定价偏低
TIMEZONE_ARBITRAGE_HOURS = {
    "start": 0,   # 北京时间 00:00
    "end": 6,     # 北京时间 06:00
}
