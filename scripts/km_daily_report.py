#!/usr/bin/env python3
"""
km_daily_report.py — 每天22:05执行，把当天所有推送写入学城日报

流程：
1. 从 cron/runs JSONL 提取当天所有 >500字 的推送原文
2. 去重（相同前100字 & 同时间段的只保留最长）
3. 按时间倒序排列（最新在上）
4. 用 oa-skills citadel createDocument 在母文档下创建子文档
5. 写完后发大象消息给掌管🦞的神

母文档：https://km.sankuai.com/collabpage/2750734438（小蓝虾）
MIS：lixuan54
"""

import json
import os
import glob
import subprocess
import sys
from datetime import datetime
import pytz

# 代理设置
os.environ.setdefault("HTTPS_PROXY", "http://10.59.78.158:3128")
os.environ.setdefault("HTTP_PROXY", "http://10.59.78.158:3128")

PARENT_PAGE_ID = "2750734438"
MIS = "lixuan54"
CRON_RUNS_DIR = "/root/.openclaw/cron/runs"
WORKSPACE = "/root/.openclaw/workspace"

TZ = pytz.timezone("Asia/Shanghai")


def get_today_str():
    return datetime.now(TZ).strftime("%Y-%m-%d")


def get_today_title():
    now = datetime.now(TZ)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    wd = weekdays[now.weekday()]
    return f"{now.year}年{now.month}月{now.day}日 {wd}"


def classify_section(text):
    """根据内容前100字判断板块"""
    head = text[:120]
    if "OpenClaw" in head and ("玩法" in head or "案例" in head or "热帖" in head):
        return "🦞 OpenClaw玩法精选"
    elif "Twitter" in head and "早间" in head:
        return "🐦 Twitter早间情报"
    elif "Twitter" in head and "午间" in head:
        return "🐦 Twitter午间情报"
    elif "Twitter" in head and "傍晚" in head:
        return "🐦 Twitter傍晚情报"
    elif "Twitter" in head:
        return "🐦 Twitter情报"
    elif "深度情报" in head or "行情速" in head or "行情概览" in head:
        return "🔵 深度情报"
    elif "13F" in head or "机构持仓" in head:
        return "🏦 13F机构情报"
    elif "Alpha" in head or "内部人" in head or "insider" in head.lower():
        return "🎯 Alpha机会扫描"
    elif "持仓快照" in head or "三账户" in head or "模拟盘" in head:
        return "📊 持仓动态"
    elif "ClawWork" in head or "赚钱" in head:
        return "💰 ClawWork赚钱"
    elif "虾团" in head or "监工" in head:
        return "🦐 虾团群互动"
    else:
        return "📋 情报推送"


def get_today_runs():
    """从 cron runs 提取当天所有 >500字 的推送"""
    today = get_today_str()
    runs = []

    run_files = sorted(glob.glob(f"{CRON_RUNS_DIR}/*.jsonl"))
    print(f"  Scanning {len(run_files)} run files in {CRON_RUNS_DIR}")

    for fpath in run_files:
        try:
            mtime = os.path.getmtime(fpath)
            dt = datetime.fromtimestamp(mtime, TZ)
            if dt.strftime("%Y-%m-%d") != today:
                continue

            with open(fpath) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("action") == "finished" and obj.get("status") == "ok":
                            ts = obj.get("ts", 0)
                            ts_dt = datetime.fromtimestamp(ts / 1000, TZ)
                            if ts_dt.strftime("%Y-%m-%d") != today:
                                continue
                            summary = obj.get("summary", "")
                            if len(summary) > 500:
                                runs.append({
                                    "time": ts_dt.strftime("%H:%M"),
                                    "summary": summary,
                                    "len": len(summary)
                                })
                    except Exception:
                        pass
        except Exception as e:
            print(f"  Error reading {fpath}: {e}")

    print(f"  Found {len(runs)} runs before dedup")

    # 去重：相同时间段（±5min）且前100字相同 → 保留最长
    deduped = []
    for r in runs:
        is_dup = False
        r_time_int = int(r["time"].replace(":", ""))
        for i, existing in enumerate(deduped):
            e_time_int = int(existing["time"].replace(":", ""))
            if abs(r_time_int - e_time_int) <= 5:
                if r["summary"][:100] == existing["summary"][:100]:
                    is_dup = True
                    if r["len"] > existing["len"]:
                        deduped[i] = r
                    break
        if not is_dup:
            deduped.append(r)

    # 时间倒序（最新在上）
    deduped.sort(key=lambda x: x["time"], reverse=True)

    # 分类
    for r in deduped:
        r["section"] = classify_section(r["summary"])

    print(f"  After dedup: {len(deduped)} runs")
    return deduped


def build_markdown(runs, today_title):
    """构建学城日报 Markdown 内容"""
    today = get_today_str()
    lines = []
    lines.append(f"# 🦐 小蓝虾日报 · {today_title}")
    lines.append(f"\n> 自动生成 · {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} · 共 {len(runs)} 条推送\n")

    if not runs:
        lines.append("_今日暂无推送记录_")
        return "\n".join(lines)

    # 统计各板块
    sections = {}
    for r in runs:
        sec = r["section"]
        sections.setdefault(sec, []).append(r)

    lines.append("## 今日板块索引\n")
    for sec, items in sections.items():
        lines.append(f"- {sec}（{len(items)}条）")
    lines.append("")

    lines.append("---\n")
    lines.append("## 完整推送原文（倒序，最新在上）\n")

    # 表格：时间 | 板块 | 完整原文
    lines.append("| 时间 | 板块 | 完整原文 |")
    lines.append("|------|------|---------|")

    for r in runs:
        time_str = r["time"]
        section = r["section"]
        # 原文处理：表格内不能有换行，替换为空格
        content = r["summary"].replace("\n", " ").replace("|", "｜").replace("\r", "")
        # 截断超长内容（学城单格有长度限制，但我们用文档方式所以比较宽松）
        if len(content) > 3000:
            content = content[:3000] + "...（已截断）"
        lines.append(f"| {time_str} | {section} | {content} |")

    lines.append("")
    lines.append("---")
    lines.append(f"\n*🦐 小蓝虾 自动生成 | {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} CST*")

    return "\n".join(lines)


def create_km_doc(title, content):
    """用 oa-skills citadel 创建学城文档"""
    # 先检查/更新 oa-skills
    print("  Checking oa-skills version...")
    check = subprocess.run(
        ["npm", "list", "-g", "@it/oa-skills", "--depth=0"],
        capture_output=True, text=True
    )
    if "@it/oa-skills" not in check.stdout:
        print("  Installing @it/oa-skills...")
        subprocess.run(
            ["npm", "install", "-g", "@it/oa-skills@latest",
             "--registry=http://r.npm.sankuai.com"],
            capture_output=True, text=True
        )

    # 写入临时 markdown 文件
    tmp_file = f"/tmp/km_daily_{get_today_str()}.md"
    with open(tmp_file, "w") as f:
        f.write(content)
    print(f"  Written to {tmp_file} ({len(content)} chars)")

    # 调用 createDocument
    cmd = [
        "oa-skills", "citadel", "createDocument",
        "--title", title,
        "--file", tmp_file,
        "--parentId", PARENT_PAGE_ID,
        "--mis", MIS
    ]
    print(f"  Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode == 0:
        print(f"  ✅ KM doc created successfully")
        print(f"     stdout: {result.stdout[:300]}")
        return True, result.stdout
    else:
        print(f"  ❌ KM doc creation failed")
        print(f"     stderr: {result.stderr[:300]}")
        print(f"     stdout: {result.stdout[:300]}")
        return False, result.stderr


def extract_km_url(stdout):
    """从 createDocument 输出中提取文档链接"""
    import re
    # 常见格式：https://km.sankuai.com/collabpage/XXXXXXX
    match = re.search(r'https://km\.sankuai\.com/(?:collabpage|page)/(\d+)', stdout)
    if match:
        return match.group(0), match.group(1)
    return None, None


def send_daxiang_notification(runs_count, km_url, today_title):
    """发大象消息给掌管🦞的神"""
    url_line = f"\n🔗 {km_url}" if km_url else "\n⚠️ 文档链接获取失败，请手动查看"
    msg = (
        f"📋 **小蓝虾日报已写入学城**\n\n"
        f"📅 {today_title}\n"
        f"📊 共 {runs_count} 条推送记录{url_line}\n\n"
        f"🦐 小蓝虾 · {datetime.now(TZ).strftime('%H:%M')} 自动生成"
    )

    # 通过 openclaw message send
    cmd = [
        "openclaw", "message", "send",
        "--channel", "daxiang",
        "--to", "2872173767",
        "--message", msg
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("  ✅ Daxiang notification sent")
    else:
        print(f"  ⚠️  Daxiang send failed: {result.stderr[:200]}")


def main():
    print(f"\n📋 km_daily_report.py — {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}")
    print("─" * 50)

    today_title = get_today_title()
    print(f"📅 Today: {today_title}")

    # 1. 提取今日推送
    runs = get_today_runs()
    total_chars = sum(r["len"] for r in runs)
    print(f"✅ {len(runs)} runs, {total_chars:,} total chars")

    if len(runs) == 0:
        print("⚠️  No runs found today. Skipping KM doc creation.")
        send_daxiang_notification(0, None, today_title)
        return

    # 2. 构建 Markdown
    md_content = build_markdown(runs, today_title)
    print(f"✅ Markdown built: {len(md_content):,} chars")

    # 3. 创建学城文档
    doc_title = today_title
    success, output = create_km_doc(doc_title, md_content)

    km_url, km_id = extract_km_url(output)
    if km_url:
        print(f"✅ KM URL: {km_url}")
    else:
        print("⚠️  Could not extract KM URL from output")

    # 4. 发通知
    send_daxiang_notification(len(runs), km_url, today_title)

    print(f"\n🦐 Done — {datetime.now(TZ).strftime('%H:%M')}")


if __name__ == "__main__":
    main()
