#!/usr/bin/env python3
"""
Step 5: FFmpeg 合成每个场景，然后 concat 拼接成完整视频
"""
import json, os, subprocess, sys

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
CLIPS_DIR = os.path.join(WORK_DIR, "clips")
AUDIO_DIR = os.path.join(WORK_DIR, "audio")
SCENES_DIR = os.path.join(WORK_DIR, "scenes")
OUTPUT_DIR = os.path.join(WORK_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(os.path.join(WORK_DIR, "script.json")) as f:
    script = json.load(f)
with open(os.path.join(WORK_DIR, "durations.json")) as f:
    durations = json.load(f)

scene_files = []

for scene in script["scenes"]:
    sid = scene["id"]
    clip = os.path.join(CLIPS_DIR, f"scene_{sid}.mp4")
    audio = os.path.join(AUDIO_DIR, f"scene_{sid}.mp3")
    overlay = os.path.join(SCENES_DIR, f"overlay_{sid}.png")
    out = os.path.join(SCENES_DIR, f"scene_{sid}_final.mp4")
    
    dur = durations[f"scene_{sid}"]
    
    print(f"\n🎬 合成场景{sid}: {scene['name']} ({dur:.1f}s)")
    
    # FFmpeg: 循环视频 + 裁剪到竖屏 + 叠加字幕 + 音频
    # -stream_loop -1: 无限循环视频（保证够长）
    # -t dur: 截取到音频时长
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", clip,
        "-i", audio,
        "-i", overlay,
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        f"[2:v]scale=1080:1920[ol];"
        f"[bg][ol]overlay=0:0[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(dur),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 10000:
        sz = os.path.getsize(out) / 1024 / 1024
        print(f"  ✅ {sz:.1f}MB")
        scene_files.append(out)
    else:
        print(f"  ❌ 失败: {r.stderr[-300:]}")
        # 即使失败也记录，用于后续concat
        scene_files.append(None)

# 过滤失败的场景
valid_scenes = [f for f in scene_files if f]
print(f"\n📋 有效场景: {len(valid_scenes)}/{len(script['scenes'])}")

if not valid_scenes:
    print("❌ 所有场景合成失败，退出")
    sys.exit(1)

# 生成 concat 文件列表
concat_file = os.path.join(WORK_DIR, "concat_list.txt")
with open(concat_file, "w") as f:
    for path in valid_scenes:
        f.write(f"file '{path}'\n")

# 最终拼接
final_out = os.path.join(OUTPUT_DIR, "final_output.mp4")
print(f"\n🔗 拼接 {len(valid_scenes)} 个场景...")
concat_cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-c:a", "aac", "-b:a", "128k",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    final_out
]

r = subprocess.run(concat_cmd, capture_output=True, text=True)
if r.returncode == 0 and os.path.exists(final_out):
    sz = os.path.getsize(final_out) / 1024 / 1024
    
    # 获取视频信息
    info_r = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", final_out
    ], capture_output=True, text=True)
    info = json.loads(info_r.stdout)
    duration = float(info["format"]["duration"])
    
    print(f"\n🎉 最终视频合成完成！")
    print(f"  📁 路径: {final_out}")
    print(f"  📏 分辨率: 1080x1920")
    print(f"  ⏱️  总时长: {duration:.1f}s")
    print(f"  💾 文件大小: {sz:.1f}MB")
    print(f"  🎬 场景数: {len(valid_scenes)}")
else:
    print(f"❌ 最终拼接失败: {r.stderr[-500:]}")
    sys.exit(1)
