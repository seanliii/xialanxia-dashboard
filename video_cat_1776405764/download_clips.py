#!/usr/bin/env python3
"""
下载 Pexels 猫咪短视频素材（通过直链 + curl）
"""
import json, os, subprocess, sys

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
CLIPS_DIR = os.path.join(WORK_DIR, "clips")

# 预先整理的竖屏/方形猫咪 Pexels 免费视频直链（MP4，Creative Commons）
SCENE_VIDEOS = [
    # 场景1: 入坑 — kitten
    ("scene_1", "https://videos.pexels.com/video-files/4587942/4587942-uhd_2160_3840_25fps.mp4"),
    # 场景2: 假装乖巧 — cat sleeping
    ("scene_2", "https://videos.pexels.com/video-files/3195394/3195394-uhd_2560_1440_25fps.mp4"),
    # 场景3: 检阅领地 — cat exploring
    ("scene_3", "https://videos.pexels.com/video-files/4588036/4588036-uhd_2160_3840_25fps.mp4"),
    # 场景4: 凌晨跑酷 — cat playful
    ("scene_4", "https://videos.pexels.com/video-files/6794455/6794455-uhd_2160_3840_25fps.mp4"),
    # 场景5: 霸占键盘 — cat on laptop
    ("scene_5", "https://videos.pexels.com/video-files/3254025/3254025-hd_1920_1080_25fps.mp4"),
    # 场景6: 纸箱真香 — cat in box
    ("scene_6", "https://videos.pexels.com/video-files/4588007/4588007-uhd_2160_3840_25fps.mp4"),
    # 场景7: 咕噜杀 — cat cozy
    ("scene_7", "https://videos.pexels.com/video-files/3255270/3255270-hd_1920_1080_25fps.mp4"),
]

# 备用直链（如果主链下载失败）
FALLBACK_VIDEOS = [
    ("scene_1", "https://videos.pexels.com/video-files/4588014/4588014-uhd_2160_3840_25fps.mp4"),
    ("scene_2", "https://videos.pexels.com/video-files/4099389/4099389-hd_1920_1080_25fps.mp4"),
    ("scene_3", "https://videos.pexels.com/video-files/4587994/4587994-uhd_2160_3840_25fps.mp4"),
    ("scene_4", "https://videos.pexels.com/video-files/7002562/7002562-hd_1920_1080_30fps.mp4"),
    ("scene_5", "https://videos.pexels.com/video-files/8210958/8210958-hd_1920_1080_25fps.mp4"),
    ("scene_6", "https://videos.pexels.com/video-files/4587968/4587968-uhd_2160_3840_25fps.mp4"),
    ("scene_7", "https://videos.pexels.com/video-files/3196010/3196010-hd_1920_1080_25fps.mp4"),
]

def download(name, url, dest_path):
    print(f"  ⬇️  {name}: {url[:60]}...")
    result = subprocess.run([
        "curl", "-L", "-s", "--max-time", "30",
        "--retry", "2",
        "-H", "Referer: https://www.pexels.com/",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "-o", dest_path, url
    ], capture_output=True)
    if result.returncode == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        size_mb = os.path.getsize(dest_path) / 1024 / 1024
        print(f"  ✅ {name}: {size_mb:.1f} MB")
        return True
    else:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        print(f"  ❌ {name}: 下载失败（returncode={result.returncode}）")
        return False

os.makedirs(CLIPS_DIR, exist_ok=True)
failed = []

for (name, url), (_, fallback_url) in zip(SCENE_VIDEOS, FALLBACK_VIDEOS):
    dest = os.path.join(CLIPS_DIR, f"{name}.mp4")
    if os.path.exists(dest) and os.path.getsize(dest) > 10000:
        print(f"  ⏭️  {name}: 已存在，跳过")
        continue
    ok = download(name, url, dest)
    if not ok:
        print(f"  🔄 {name}: 尝试备用链接...")
        ok = download(name, fallback_url, dest)
    if not ok:
        failed.append(name)

if failed:
    print(f"\n⚠️  以下场景下载失败，将用占位符替代: {failed}")
    # 为失败场景创建纯黑占位视频
    for name in failed:
        dest = os.path.join(CLIPS_DIR, f"{name}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=25",
            "-t", "10", "-c:v", "libx264", "-pix_fmt", "yuv420p", dest
        ], capture_output=True)
        print(f"  🎨 {name}: 生成黑色占位视频")
else:
    print("\n✅ 所有素材下载完成！")
