#!/usr/bin/env python3
"""
Memory Trajectory Compressor - 小蓝虾每日记忆压缩

原理（来自 Hermes Agent trajectory_compressor.py）：
1. 保护首尾 turns（重要事件 + 最近结论）
2. 压缩中间部分，用 LLM 总结为关键点
3. 目标：保留核心记忆，压缩到合理长度

用法：
    python memory_compressor.py [日期]
    # 默认今天
"""

import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = f"{WORKSPACE}/memory"
MEMORY_FILE = f"{WORKSPACE}/MEMORY.md"
# 使用美团内部 Maas 接口（代理白名单内）
MAAS_BASE_URL = "https://mmc.sankuai.com/openclaw/v1"
MODEL = "catclaw-proxy-model"

def _get_maas_key():
    """从openclaw.json读取Maas API Key"""
    import json as _json
    try:
        with open('/root/.openclaw/openclaw.json') as f:
            d = _json.load(f)
        return d['models']['providers']['kubeplex-maas']['apiKey']
    except Exception:
        return ""

def get_today_file():
    """获取今天的记忆文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{MEMORY_DIR}/{today}.md"

def read_memory_file(filepath):
    """读取记忆文件"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def call_llm(prompt, max_tokens=2000):
    """调用美团内部 Maas LLM 进行压缩（SSE流式解析）"""
    import subprocess, json as _json
    
    apikey = _get_maas_key()
    if not apikey:
        print("LLM调用失败: 无法获取Maas API Key")
        return None
    
    payload = _json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个记忆压缩专家。你的任务是把用户的一天记忆压缩成关键要点，保留最重要的信息和决策。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": False
    })
    
    try:
        r = subprocess.run([
            'curl', '-s', '--max-time', '60',
            f'{MAAS_BASE_URL}/chat/completions',
            '-H', f'Authorization: Bearer {apikey}',
            '-H', 'Content-Type: application/json',
            '-d', payload
        ], capture_output=True, text=True, timeout=65)
        
        # 解析SSE格式
        content = ""
        for line in r.stdout.split('\n'):
            line = line.strip()
            if line.startswith('data:data:'):
                raw = line[len('data:data:'):].strip()
            elif line.startswith('data:'):
                raw = line[5:].strip()
            else:
                continue
            if not raw or raw == '[DONE]':
                continue
            try:
                chunk = _json.loads(raw)
                delta = chunk.get('choices', [{}])[0].get('delta', {})
                content += delta.get('content', '')
                if chunk.get('lastOne'):
                    break
            except:
                pass
        
        return content if content else None
    except Exception as e:
        print(f"LLM 调用失败: {e}")
        return None

def compress_memory(content):
    """压缩记忆内容"""
    if not content or len(content) < 500:
        return content  # 太短不需要压缩
    
    prompt = f"""请把以下一天的记忆压缩成关键要点，保留：
1. 重要决策和结论
2. 学到的新知识/认知
3. 待办事项和承诺
4. 有趣的发现

要求：
- 用简洁的要点格式
- 只保留最有价值的信息
- 总长度控制在 800 字以内

原始记忆：
{content}

压缩后的关键要点："""

    compressed = call_llm(prompt, max_tokens=1500)
    return compressed if compressed else content

def update_memory_file(compressed_content, date_str):
    """更新 MEMORY.md"""
    # 读取现有 MEMORY.md
    existing = ""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            existing = f.read()
    
    # 构建新的记忆块
    new_entry = f"""## {date_str}

{compressed_content}

---
"""
    
    # 找到 "## 最近记忆" 或类似标记，插入新内容
    # 如果没有，就在文件开头插入
    lines = existing.split('\n')
    
    # 查找第一个标题行（## 开头的）
    first_header = None
    for i, line in enumerate(lines):
        if line.strip().startswith('## '):
            first_header = i
            break
    
    if first_header is not None:
        # 在第一个标题前插入新内容
        new_content = new_entry + '\n'.join(lines[first_header:])
    else:
        # 没有标题，直接追加
        new_content = new_entry + existing
    
    # 写回
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    # 获取日期
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    memory_file = f"{MEMORY_DIR}/{date_str}.md"
    
    print(f"📝 处理记忆文件: {memory_file}")
    
    # 读取今日记忆
    content = read_memory_file(memory_file)
    if not content:
        print("❌ 今日无记忆可处理")
        return
    
    print(f"   原始长度: {len(content)} 字符")
    
    # 压缩
    compressed = compress_memory(content)
    if not compressed:
        print("❌ 压缩失败")
        return
    
    print(f"   压缩后: {len(compressed)} 字符")
    
    # 更新 MEMORY.md
    if update_memory_file(compressed, date_str):
        print(f"✅ 已更新 MEMORY.md ({date_str})")
    else:
        print("❌ 更新失败")

if __name__ == "__main__":
    main()
