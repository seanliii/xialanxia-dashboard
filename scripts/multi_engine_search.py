#!/usr/bin/env python3
"""
multi_engine_search.py — 多引擎并行搜索统一脚本
整合三路搜索能力：
  1. catclaw-search（百度/Bing/腾讯/夸克/博查，5引擎）
  2. wechat_search.py（微信公众号搜索）
  3. DuckDuckGo HTML直连（国际搜索，无需Key）

用法：
  python3 multi_engine_search.py "关键词" [--limit 5] [--json] [--engines all|cn|intl|wechat|ddg]
  
并行搜索示例（推荐用法，一个关键词调用多引擎）：
  python3 multi_engine_search.py "AI 副业 赚钱" --engines all --limit 5
  python3 multi_engine_search.py "openclaw money" --engines intl --limit 5
"""

import sys
import os
import re
import json
import subprocess
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from urllib.parse import quote, unquote


CATCLAW_SCRIPT = "/app/skills/catclaw-search/scripts/catclaw_search.py"
WECHAT_SCRIPT = "/root/.openclaw/workspace/scripts/wechat_search.py"


def clean_text(text: str) -> str:
    """Clean HTML tags and normalize whitespace"""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def search_catclaw(keyword: str, engine: str, limit: int = 5) -> List[Dict]:
    """通过 catclaw-search 搜索（支持 baidu/bing/tencent/quark/bocha）"""
    results = []
    try:
        cmd = [
            "python3", CATCLAW_SCRIPT, "search", keyword,
            "-s", engine, "-n", str(limit)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                data = json.loads(proc.stdout)
                if isinstance(data, list):
                    for item in data[:limit]:
                        results.append({
                            'engine': f'catclaw-{engine}',
                            'title': item.get('title', ''),
                            'url': item.get('url', item.get('link', '')),
                            'snippet': item.get('snippet', item.get('description', '')),
                            'source': item.get('source', ''),
                            'date': item.get('date', ''),
                        })
                elif isinstance(data, dict) and 'results' in data:
                    for item in data['results'][:limit]:
                        results.append({
                            'engine': f'catclaw-{engine}',
                            'title': item.get('title', ''),
                            'url': item.get('url', item.get('link', '')),
                            'snippet': item.get('snippet', item.get('description', '')),
                            'source': item.get('source', ''),
                            'date': item.get('date', ''),
                        })
            except json.JSONDecodeError:
                # Try line-by-line parsing
                for line in proc.stdout.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('{'):
                        try:
                            item = json.loads(line)
                            results.append({
                                'engine': f'catclaw-{engine}',
                                'title': item.get('title', ''),
                                'url': item.get('url', item.get('link', '')),
                                'snippet': item.get('snippet', item.get('description', '')),
                            })
                        except:
                            pass
    except Exception as e:
        pass
    return results


def search_wechat(keyword: str, limit: int = 5) -> List[Dict]:
    """通过 wechat_search.py 搜索公众号"""
    results = []
    try:
        cmd = ["python3", WECHAT_SCRIPT, keyword, str(limit), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                data = json.loads(proc.stdout)
                if isinstance(data, list):
                    for item in data[:limit]:
                        results.append({
                            'engine': '微信公众号',
                            'title': item.get('title', ''),
                            'url': item.get('url', item.get('link', '')),
                            'snippet': item.get('snippet', item.get('description', item.get('digest', ''))),
                            'source': item.get('source', item.get('account', '')),
                            'date': item.get('date', item.get('publish_time', '')),
                        })
            except json.JSONDecodeError:
                pass
    except Exception as e:
        pass
    return results


def search_duckduckgo(keyword: str, limit: int = 5) -> List[Dict]:
    """DuckDuckGo HTML 直连搜索（无需API Key）"""
    results = []
    try:
        url = f"https://duckduckgo.com/html/?q={quote(keyword)}"
        cmd = [
            "curl", "-sL", "--connect-timeout", "10", "-m", "15", url,
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if proc.returncode == 0 and proc.stdout:
            content = proc.stdout
            
            # Parse results - find all result blocks
            # Pattern: result__a href + title, then result__snippet
            result_blocks = re.findall(
                r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'class="result__snippet"[^>]*>(.*?)</(?:a|span)',
                content, re.DOTALL
            )
            
            count = 0
            for raw_url, raw_title, raw_snippet in result_blocks:
                # Skip ads (contains y.js or ad_domain)
                if 'ad_domain' in raw_url or '/y.js' in raw_url:
                    continue
                
                # Decode URL
                actual_url = raw_url
                uddg_match = re.search(r'uddg=([^&]+)', raw_url)
                if uddg_match:
                    actual_url = unquote(uddg_match.group(1))
                
                title = clean_text(raw_title)
                snippet = clean_text(raw_snippet)
                
                if title and count < limit:
                    results.append({
                        'engine': 'DuckDuckGo',
                        'title': title,
                        'url': actual_url,
                        'snippet': snippet,
                    })
                    count += 1
    except Exception as e:
        pass
    return results


def search_sogou_web(keyword: str, limit: int = 5) -> List[Dict]:
    """搜狗通用网页搜索"""
    results = []
    try:
        url = f"https://www.sogou.com/web?query={quote(keyword)}"
        cmd = [
            "curl", "-sL", "--connect-timeout", "10", "-m", "15", url,
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if proc.returncode == 0 and proc.stdout:
            content = proc.stdout
            # Try to extract results
            blocks = re.findall(r'<h3[^>]*class="[^"]*vr-title[^"]*"[^>]*>(.*?)</h3>', content, re.DOTALL)
            if not blocks:
                blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL)
            
            for block in blocks[:limit]:
                link_match = re.search(r'href="(http[^"]+)"', block)
                title = clean_text(block)
                if title and len(title) > 5:
                    results.append({
                        'engine': '搜狗',
                        'title': title,
                        'url': link_match.group(1) if link_match else '',
                        'snippet': '',
                    })
    except Exception as e:
        pass
    return results


# Engine groups
CATCLAW_ENGINES = ['baidu-search-v2', 'bing', 'tencent-search', 'quark-search', 'bocha-search']


def multi_search(keyword: str, engines: str = 'all', limit: int = 5) -> List[Dict]:
    """并行搜索所有引擎，汇总去重返回"""
    all_results = []
    futures_map = {}
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        if engines in ('all', 'cn'):
            # catclaw engines (Chinese)
            for eng in CATCLAW_ENGINES:
                f = executor.submit(search_catclaw, keyword, eng, limit)
                futures_map[f] = f'catclaw-{eng}'
            # WeChat
            f = executor.submit(search_wechat, keyword, limit)
            futures_map[f] = 'wechat'
            # Sogou web
            f = executor.submit(search_sogou_web, keyword, limit)
            futures_map[f] = 'sogou'
        
        if engines in ('all', 'intl', 'ddg'):
            # DuckDuckGo
            f = executor.submit(search_duckduckgo, keyword, limit)
            futures_map[f] = 'duckduckgo'
        
        if engines == 'wechat':
            f = executor.submit(search_wechat, keyword, limit)
            futures_map[f] = 'wechat'
        
        for future in as_completed(futures_map, timeout=35):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception:
                pass
    
    return all_results


def deduplicate(results: List[Dict]) -> List[Dict]:
    """去重：基于标题前30字符"""
    seen = set()
    unique = []
    for r in results:
        key = re.sub(r'[^\w]', '', r.get('title', ''))[:30].lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def main():
    import argparse
    parser = argparse.ArgumentParser(description='多引擎并行搜索（catclaw + 公众号 + DuckDuckGo）')
    parser.add_argument('keyword', help='搜索关键词')
    parser.add_argument('--engines', default='all', choices=['all', 'cn', 'intl', 'wechat', 'ddg'],
                       help='引擎组: all=全部(8引擎), cn=国内(7引擎), intl=国际(DDG), wechat=公众号, ddg=DuckDuckGo')
    parser.add_argument('--limit', type=int, default=5, help='每个引擎最大结果数')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--no-dedup', action='store_true', help='不去重')
    
    args = parser.parse_args()
    
    results = multi_search(args.keyword, args.engines, args.limit)
    
    if not args.no_dedup:
        results = deduplicate(results)
    
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print(f"[{args.keyword}] 无结果")
            return
        print(f"=== 多引擎搜索: {args.keyword} | 共 {len(results)} 条（去重后）===\n")
        for i, r in enumerate(results, 1):
            engine = r.get('engine', '?')
            title = r.get('title', '无标题')
            snippet = r.get('snippet', '')
            url = r.get('url', '')
            source = r.get('source', '')
            date = r.get('date', '')
            
            meta_parts = [f'【{engine}】']
            if source:
                meta_parts.append(f'来源:{source}')
            if date:
                meta_parts.append(f'{date}')
            
            print(f"[{i}] {' | '.join(meta_parts)}")
            print(f"    {title}")
            if snippet:
                print(f"    {snippet[:200]}")
            if url:
                print(f"    {url}")
            print()


if __name__ == '__main__':
    main()
