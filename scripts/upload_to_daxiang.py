#!/usr/bin/env python3
"""
upload_to_daxiang.py - 发送 dashboard HTML 文件到大象
通过 OpenClaw 内部 API 发送文件，大象生成 CDN 链接，点击可在浏览器直接打开

用法：
  python3 upload_to_daxiang.py
  python3 upload_to_daxiang.py --file /path/to/custom.html
  python3 upload_to_daxiang.py --message "自定义消息"
"""

import subprocess
import sys
import os
import json
import argparse
from datetime import datetime

# 配置
DEFAULT_FILE = "/root/.openclaw/workspace/dashboard/dashboard.html"
TARGET_UID = "2872173767"

def send_file_via_tool(file_path: str, message: str = None):
    """通过 openclaw 内置 message tool 发送文件（用 node 脚本调用）"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    
    if message is None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"📊 Dashboard 已更新 ({now}) | {file_size // 1024} KB | 点击文件在浏览器打开"
    
    print(f"📤 正在发送 {filename} ({file_size // 1024} KB) ...")
    
    # 方案1：直接用 openclaw agent 调用（传递工具调用指令）
    # 通过 sessions_send 或内部 REST API
    
    # 检查 openclaw 内部 API 端口
    # OpenClaw 默认监听 18789
    api_url = "http://localhost:18789"
    
    # 读取文件为 base64
    import base64
    with open(file_path, "rb") as f:
        file_content = f.read()
    file_b64 = base64.b64encode(file_content).decode()
    data_url = f"data:text/html;base64,{file_b64}"
    
    # 调用 message tool via OpenClaw internal API
    payload = {
        "tool": "message",
        "params": {
            "action": "send",
            "channel": "daxiang",
            "target": TARGET_UID,
            "message": message,
            "buffer": data_url,
            "filename": filename,
            "contentType": "text/html"
        }
    }
    
    # 尝试通过 curl 调用内部 API
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{api_url}/api/tool",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0 and result.stdout:
        try:
            resp = json.loads(result.stdout)
            if resp.get("ok") or resp.get("result"):
                print(f"✅ 发送成功！")
                return True
        except:
            pass
    
    # 如果内部 API 不可用，尝试方案2：写一个临时 Node.js 脚本
    print("内部 API 方式失败，尝试 Node.js 脚本...")
    return send_via_node(file_path, message, filename)


def send_via_node(file_path: str, message: str, filename: str):
    """通过 Node.js 脚本调用 openclaw SDK 发送文件"""
    
    node_script = f"""
const {{ execSync }} = require('child_process');
const fs = require('fs');
const path = require('path');

// 读取文件
const filePath = {json.dumps(file_path)};
const filename = {json.dumps(filename)};
const message = {json.dumps(message)};
const targetUid = {json.dumps(TARGET_UID)};

const fileContent = fs.readFileSync(filePath);
const b64 = fileContent.toString('base64');
const dataUrl = 'data:text/html;base64,' + b64;

// 调用内部工具
const payload = {{
  action: 'send',
  channel: 'daxiang', 
  target: targetUid,
  message: message,
  buffer: dataUrl,
  filename: filename,
  contentType: 'text/html'
}};

console.log(JSON.stringify(payload));
"""
    
    # 先写临时脚本检验逻辑
    tmp_script = "/tmp/send_daxiang_test.js"
    with open(tmp_script, "w") as f:
        f.write(node_script)
    
    result = subprocess.run(["node", tmp_script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Node 脚本运行成功，payload 构建 OK")
        print(result.stdout[:200])
    else:
        print(f"Node 失败: {result.stderr}")
    
    return False


def send_via_python_openclaw_api(file_path: str, message: str):
    """直接调用 OpenClaw REST API 发送消息（含文件）"""
    import urllib.request
    import base64
    
    filename = os.path.basename(file_path)
    
    with open(file_path, "rb") as f:
        content = f.read()
    b64 = base64.b64encode(content).decode()
    data_url = f"data:text/html;base64,{b64}"
    
    # 尝试不同端口
    for port in [18789, 3000, 8080, 9876]:
        try:
            payload = json.dumps({
                "tool": "message",
                "params": {
                    "action": "send",
                    "channel": "daxiang",
                    "target": TARGET_UID,
                    "message": message,
                    "buffer": data_url,
                    "filename": filename
                }
            }).encode()
            
            req = urllib.request.Request(
                f"http://localhost:{port}/api/tool",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                print(f"✅ 通过端口 {port} 发送成功: {result}")
                return True
        except Exception as e:
            print(f"端口 {port} 失败: {e}")
    
    return False


def main():
    parser = argparse.ArgumentParser(description="发送 dashboard HTML 到大象")
    parser.add_argument("--file", default=DEFAULT_FILE, help="要发送的 HTML 文件路径")
    parser.add_argument("--message", default=None, help="附带消息")
    args = parser.parse_args()
    
    if args.message is None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        file_size = os.path.getsize(args.file) // 1024
        args.message = f"📊 Dashboard 已更新 ({now}) | {file_size} KB | 点击文件在浏览器打开"
    
    # 先试内部 API，再试 Node
    success = send_via_python_openclaw_api(args.file, args.message)
    
    if not success:
        print("\n⚠️  自动发送失败")
        print("替代方案：手动在对话中触发发送")
        print(f"文件路径: {args.file}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
