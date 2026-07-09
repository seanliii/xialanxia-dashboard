#!/usr/bin/env python3
"""
Step 3: 为每个场景生成 Edge TTS 配音
"""
import asyncio, json, os, subprocess, sys

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
AUDIO_DIR = os.path.join(WORK_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

with open(os.path.join(WORK_DIR, "script.json")) as f:
    script = json.load(f)

async def gen_tts(scene_id, text, voice, out_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

durations = {}

for scene in script["scenes"]:
    sid = scene["id"]
    out_path = os.path.join(AUDIO_DIR, f"scene_{sid}.mp3")
    
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f"⏭️  场景{sid}: 已存在")
    else:
        print(f"🎤 场景{sid}: 生成配音...")
        asyncio.run(gen_tts(sid, scene["narration"], scene["voice"], out_path))
        print(f"  ✅ 场景{sid}: {os.path.getsize(out_path)//1024}KB")
    
    # 获取实际音频时长
    r = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", out_path
    ], capture_output=True, text=True)
    info = json.loads(r.stdout)
    dur = float(info["format"]["duration"])
    durations[f"scene_{sid}"] = dur
    print(f"  ⏱️  场景{sid}: {dur:.2f}s")

# 保存时长数据
with open(os.path.join(WORK_DIR, "durations.json"), "w") as f:
    json.dump(durations, f, indent=2)

total = sum(durations.values())
print(f"\n✅ 全部配音完成！总时长: {total:.1f}s")
