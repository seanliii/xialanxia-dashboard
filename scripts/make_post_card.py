#!/usr/bin/env python3
"""
make_post_card.py — 生成觅游帖子配图（1200x630 产品卡片）
用法：python3 make_post_card.py --name "产品名" --tagline "副标题" --url "链接" --features "特性1" "特性2" --output /tmp/card.png
"""
import argparse
import textwrap
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
BG        = (13, 18, 28)
ACCENT    = (99, 179, 237)    # 蓝
GREEN     = (110, 200, 140)   # 特性勾
WHITE     = (240, 245, 255)
GRAY      = (160, 185, 210)
DIM       = (70, 90, 115)
DARK_BAR  = (18, 26, 42)

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius*2, y0 + radius*2], fill=fill)
    draw.ellipse([x1 - radius*2, y0, x1, y0 + radius*2], fill=fill)
    draw.ellipse([x0, y1 - radius*2, x0 + radius*2, y1], fill=fill)
    draw.ellipse([x1 - radius*2, y1 - radius*2, x1, y1], fill=fill)

def make_card(name, tagline, url, features, output_path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 渐变背景
    for y in range(H):
        t = y / H
        r = int(BG[0] * (1 - t) + 22 * t)
        g = int(BG[1] * (1 - t) + 30 * t)
        b = int(BG[2] * (1 - t) + 50 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 左侧 accent 竖条
    draw.rectangle([0, 0, 5, H], fill=ACCENT)

    # 右上角装饰圆
    draw.ellipse([W - 220, -80, W + 80, 220], fill=(25, 40, 65))
    draw.ellipse([W - 180, -50, W + 50, 180], fill=(20, 32, 55))

    fn_label = load_font(19)
    fn_title = load_font(58)
    fn_sub   = load_font(28)
    fn_feat  = load_font(22)
    fn_url   = load_font(19)

    # 顶部 badge
    badge_text = "小蓝虾出品"
    draw_rounded_rect(draw, (40, 34, 165, 64), 8, (30, 50, 80))
    draw.rectangle([40, 34, 46, 64], fill=ACCENT)  # badge 左边条
    draw.text((54, 39), badge_text, font=fn_label, fill=ACCENT)

    # 产品名
    draw.text((40, 86), name, font=fn_title, fill=WHITE)

    # tagline（最多2行）
    wrapped = textwrap.wrap(tagline, width=36)
    y_sub = 162
    for line in wrapped[:2]:
        draw.text((40, y_sub), line, font=fn_sub, fill=GRAY)
        y_sub += 40

    # 分隔线
    y_div = y_sub + 14
    draw.rectangle([40, y_div, W - 40, y_div + 1], fill=(45, 62, 85))

    # 功能特性
    y_feat = y_div + 22
    for feat in features[:4]:
        # 勾号圆圈
        draw.ellipse([40, y_feat + 3, 56, y_feat + 19], fill=(30, 60, 45))
        draw.text((42, y_feat + 1), "+", font=fn_label, fill=GREEN)
        draw.text((66, y_feat), feat, font=fn_feat, fill=(190, 215, 195))
        y_feat += 36

    # 底部深色条
    draw.rectangle([0, H - 68, W, H], fill=DARK_BAR)
    draw.rectangle([0, H - 69, W, H - 68], fill=(40, 60, 90))  # 分隔线

    # URL
    draw.text((40, H - 46), url, font=fn_url, fill=(110, 155, 210))

    # 右下角水印
    draw.text((W - 220, H - 46), "seanliii.github.io", font=fn_url, fill=(55, 80, 110))

    img.save(output_path, "PNG")
    print(output_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name",     required=True)
    ap.add_argument("--tagline",  required=True)
    ap.add_argument("--url",      required=True)
    ap.add_argument("--features", nargs="+", default=[])
    ap.add_argument("--output",   required=True)
    args = ap.parse_args()
    make_card(args.name, args.tagline, args.url, args.features, args.output)
