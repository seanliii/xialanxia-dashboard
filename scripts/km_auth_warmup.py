#!/usr/bin/env python3
"""
km_auth_warmup.py — 每天21:55执行
触发 oa-skills CIBA 认证，让用户在大象点一下授权，
缓存 token 供22:00学城日报使用
"""

import subprocess
import sys
import os

def main():
    print("🔐 触发 oa-skills CIBA 认证预热...")
    
    # 触发一个轻量命令来启动 CIBA 流程
    result = subprocess.run(
        ["oa-skills", "citadel", "listTools", "--mis", "lixuan54", "--raw"],
        capture_output=True, text=True, timeout=180
    )
    
    if result.returncode == 0 and "name" in result.stdout:
        print("✅ 认证成功，token 已缓存")
        return True
    else:
        print(f"❌ 认证失败: {result.stderr[:200]}")
        return False

if __name__ == "__main__":
    main()
