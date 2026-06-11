#!/usr/bin/env python3
"""
13F 日报发送脚本 — 每天 18:00 触发
"""
import subprocess, sys, os, requests, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"

def send_daxiang(message: str, target: str = "2872173767"):
    """通过 OpenClaw message tool 发送大象消息"""
    # 大象消息单次限制 ~4000 字，分段发送
    max_len = 3500
    parts = []
    while len(message) > max_len:
        split_pos = message.rfind('\n', 0, max_len)
        if split_pos < max_len * 0.8:
            split_pos = max_len
        parts.append(message[:split_pos])
        message = message[split_pos:].lstrip('\n')
    parts.append(message)
    
    for i, part in enumerate(parts):
        if i > 0:
            part = f"*(续 {i+1}/{len(parts)})*\n\n" + part
        cmd = ['openclaw', 'message', 'send', '--channel', 'daxiang', '--target', target, '--message', part]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"发送失败: {result.stderr}")
        else:
            print(f"✅ 第 {i+1}/{len(parts)} 段发送成功")
    
    return True

if __name__ == "__main__":
    print("生成 13F 报告...", flush=True)
    from 13f_full_report import generate_full_13f_report
    report = generate_full_13f_report()
    
    print(f"\n报告长度: {len(report)} 字")
    print("发送大象消息...", flush=True)
    send_daxiang(report)
    print("✅ 13F 日报发送完成")
