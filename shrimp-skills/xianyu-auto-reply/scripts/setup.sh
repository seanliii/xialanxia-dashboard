#!/bin/bash
# 闲鱼自动回复虾 - 一键启用脚本
# 使用方法：bash setup.sh

echo "🦐 闲鱼自动回复虾 - 启用向导"
echo "================================"
echo ""
echo "请按提示填写配置："
echo ""

read -p "商品名称: " PRODUCT_NAME
read -p "原价（元）: " ORIGINAL_PRICE
read -p "最低接受价格（元）: " MIN_PRICE
read -p "发货方式（如：顺丰）: " SHIPPING_METHOD
read -p "发货时间（如：24小时内）: " SHIPPING_TIME

# 写入配置
CONFIG_FILE="$(dirname "$0")/../references/config.md"
sed -i "s/填写你的商品名/$PRODUCT_NAME/g" "$CONFIG_FILE"
sed -i "s/original_price: 0/original_price: $ORIGINAL_PRICE/g" "$CONFIG_FILE"
sed -i "s/min_price: 0/min_price: $MIN_PRICE/g" "$CONFIG_FILE"
sed -i "s/发货方式: \"顺丰\"/发货方式: \"$SHIPPING_METHOD\"/g" "$CONFIG_FILE"
sed -i "s/发货时间: \"24小时内\"/发货时间: \"$SHIPPING_TIME\"/g" "$CONFIG_FILE"

echo ""
echo "✅ 配置已保存"
echo ""
echo "下一步：在你的 OpenClaw 中安装此 skill，然后虾会自动开始工作"
echo ""
echo "📊 验证方法：1周后对比晚间10点后成交订单占比（目标从<5%提升到>20%）"
