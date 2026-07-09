#!/usr/bin/env python3
"""
Step 4: Pillow 生成文字叠层（白字+黑描边，1080x1920 透明 PNG）
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
SCENES_DIR = os.path.join(WORK_DIR, "scenes")
os.makedirs(SCENES_DIR, exist_ok=True)

with open(os.path.join(WORK_DIR, "script.json")) as f:
    script = json.load(f)

W, H = 1080, 1920
FONT_SIZE = 54
STROKE_WIDTH = 4

# 查找可用字体
def find_font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"  字体: {path}")
            return ImageFont.truetype(path, size)
    print("  使用默认字体（可能不支持中文）")
    return ImageFont.load_default()

font = find_font(FONT_SIZE)
font_small = find_font(42)

for scene in script["scenes"]:
    sid = scene["id"]
    out_path = os.path.join(SCENES_DIR, f"overlay_{sid}.png")
    
    # 创建透明背景
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 场景名（左上角）
    scene_name = f"#{sid} {scene['name']}"
    draw.text(
        (40, 80), scene_name,
        font=font_small,
        fill=(255, 215, 0, 220),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 200)
    )
    
    # 字幕（底部居中）
    lines = scene["subtitle"].split("\n")
    y_start = H - 280
    
    # 半透明底色
    text_h = len(lines) * (FONT_SIZE + 16) + 40
    overlay_bg = Image.new("RGBA", (W, text_h), (0, 0, 0, 120))
    img.alpha_composite(overlay_bg, (0, y_start - 20))
    
    for i, line in enumerate(lines):
        y = y_start + i * (FONT_SIZE + 16)
        # 计算文字宽度居中
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (W - text_w) // 2
        
        # 描边
        draw.text(
            (x, y), line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=STROKE_WIDTH,
            stroke_fill=(0, 0, 0, 255)
        )
    
    img.save(out_path, "PNG")
    print(f"✅ 叠层{sid}: {os.path.getsize(out_path)//1024}KB — {scene['subtitle'].replace(chr(10),' / ')}")

print(f"\n✅ 文字叠层全部生成完成！")
