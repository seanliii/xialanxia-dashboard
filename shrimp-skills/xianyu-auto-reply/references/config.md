# 闲鱼自动回复虾 - 配置文件

## 商品基础信息（必填）

```yaml
shop_name: "我的闲鱼店铺"          # 店铺名称
product_name: "填写你的商品名"      # 商品名称
original_price: 0                   # 原价（元）
min_price: 0                        # 最低接受价格（元）
shipping_method: "顺丰"             # 发货方式
shipping_time: "24小时内"           # 发货时间
```

## 议价策略

```yaml
bargain_strategy:
  hard_bottom: true          # 是否有死线（不能再低）
  bottom_price: 0            # 死线价格
  flexible_amount: 1         # 弹性让步金额（元）
  offer_coupon: true         # 是否提供优惠券
  coupon_amount: 5           # 优惠券金额
  max_bargain_rounds: 2      # 最多几轮议价后给优惠
```

## 成交信号词（触发人工通知）

```yaml
buy_signals:
  - "好的下单"
  - "直接拍"
  - "确认下单"
  - "现在买"
  - "怎么付款"
  - "拍了"
```

## 推送设置

```yaml
notification:
  channel: "daxiang"         # 推送渠道（daxiang/telegram）
  daily_report_time: "09:00" # 每日汇报时间
  urgent_notify: true        # 成交信号是否立即通知
```
