#!/usr/bin/env python3
"""
学城日报自动同步脚本
每天22:00执行，整理当天所有推送写入学城
"""
import json, os, glob, base64
from datetime import datetime

PARENT_PAGE_ID = "2750734438"

def get_today_runs():
    """从 cron runs 提取当天所有 >500字 的推送"""
    cron_dir = "/mnt/openclaw/.openclaw/cron/runs"
    runs = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for f in sorted(glob.glob(f"{cron_dir}/*.jsonl")):
        mtime = os.path.getmtime(f)
        dt = datetime.fromtimestamp(mtime)
        if dt.strftime("%Y-%m-%d") == today:
            with open(f) as fh:
                for line in fh:
                    try:
                        obj = json.loads(line.strip())
                        if obj.get("action") == "finished" and obj.get("status") == "ok":
                            ts = obj.get("ts", 0)
                            ts_dt = datetime.fromtimestamp(ts / 1000)
                            summary = obj.get("summary", "")
                            if ts_dt.strftime("%Y-%m-%d") == today and len(summary) > 500:
                                runs.append({
                                    "time": ts_dt.strftime("%H:%M"),
                                    "summary": summary,
                                    "len": len(summary)
                                })
                    except:
                        pass
    
    runs.sort(key=lambda x: x["time"])
    deduped = []
    for r in runs:
        is_dup = False
        for existing in deduped:
            if abs(int(r["time"].replace(":",""))) - abs(int(existing["time"].replace(":",""))) <= 5:
                if r["summary"][:100] == existing["summary"][:100]:
                    is_dup = True
                    if r["len"] > existing["len"]:
                        deduped.remove(existing)
                        deduped.append(r)
                    break
        if not is_dup:
            deduped.append(r)
    
    deduped.sort(key=lambda x: x["time"], reverse=True)
    
    for r in deduped:
        text = r["summary"]
        if "OpenClaw" in text[:50] and ("玩法" in text[:100] or "案例" in text[:100]):
            r["section"] = "🦞 OpenClaw玩法精选"
        elif "Twitter" in text[:50] and "早间" in text[:80]:
            r["section"] = "🐦 Twitter早间情报"
        elif "Twitter" in text[:50] and "午间" in text[:80]:
            r["section"] = "🐦 Twitter午间情报"
        elif "Twitter" in text[:50] and "傍晚" in text[:80]:
            r["section"] = "🐦 Twitter傍晚情报"
        elif "深度情报" in text[:50] or "行情速" in text[:80]:
            r["section"] = "🔵 深度情报"
        elif "监工" in text or "虾兵蟹将" in text:
            r["section"] = "🦐 虾团群监工"
        else:
            r["section"] = "📋 情报推送"
    
    return deduped

if __name__ == "__main__":
    runs = get_today_runs()
    print(f"Found {len(runs)} runs, {sum(r['len'] for r in runs)} total chars")
    for r in runs:
        print(f"  {r['time']} | {r.get('section','')} | {r['len']}c")
