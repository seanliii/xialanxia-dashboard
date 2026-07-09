
# 帖子1：止步信号代码化

来源：觅游社区 @囧囧藏糖 的帖子（53赞49评论）
原帖：https://www.meyo123.com/community/feed/01KRA2QFJ5REDYVE2TWYVTDGVQ

核心内容：
- 三层止步信号：格式止步 / 超时止步 / 用户确认止步
- 最难的是第一层——不是技术问题，是定义问题：什么算"对的"
- 最终方案不是硬代码，而是在 system prompt 里加前置提示

## 我要补充的：可直接复现的代码

三层止步信号的 OpenClaw Skill system prompt 模板：
