#!/usr/bin/env python3
"""
微信公众号文章搜索（基于搜狗微信搜索）
用法:
  python3 wechat_search.py "关键词" [数量] [--json] [--detail]

选项:
  --json     输出JSON格式
  --detail   获取文章详细内容（通过抓取文章页面）
  
示例:
  python3 wechat_search.py "AI Agent" 5
  python3 wechat_search.py "OpenClaw 赚钱" 3 --detail
  python3 wechat_search.py "创新药" 5 --json --detail
"""

import sys
import subprocess
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import quote
import ssl
import urllib.request

# 微信 UA，搜狗对手机端反爬较宽松
MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.30'
COOKIE_FILE = '/tmp/sogou_wechat_cookie.txt'


def _encode_url(url: str) -> str:
    """对 URL 里的非 ASCII 字符和空格做 percent-encoding"""
    url = re.sub(r'[^\x00-\x7F]+', lambda m: quote(m.group(0)), url)
    url = url.replace(' ', '%20')
    return url


def resolve_real_url(sogou_url: str) -> str:
    """解析搜狗跳转链接，返回真实的 mp.weixin.qq.com 链接"""
    if not sogou_url or 'weixin.qq.com' in sogou_url:
        return sogou_url  # 已经是真实链接
    
    try:
        encoded_url = _encode_url(sogou_url)
        result = subprocess.run(
            ['curl', '-s', '--connect-timeout', '8', '-m', '12',
             '-b', COOKIE_FILE,
             encoded_url,
             '-H', f'User-Agent: {MOBILE_UA}',
             '-H', 'Referer: https://weixin.sogou.com/'],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout
        # 搜狗把真实 URL 拆成多段字符串相加，用正则提取所有片段并拼接
        # 格式: url += 'xxx'; url += 'yyy'; ...
        parts = re.findall(r"url \+= '([^']+)'", html)
        if parts:
            real_url = ''.join(parts)
            if 'mp.weixin.qq.com' in real_url or 'weixin.qq.com' in real_url:
                return real_url
    except Exception:
        pass
    return sogou_url  # 失败时返回原链接


def fetch_article_content(url: str, max_chars: int = 3000) -> str:
    """抓取公众号文章的详细内容"""
    if not url:
        return ''
    
    try:
        # 用 curl 获取文章页面
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "10", "-m", "20", 
             "-L",  # follow redirects
             url,
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
            capture_output=True, text=True, timeout=25
        )
        
        if result.returncode != 0 or not result.stdout:
            return ''
        
        html = result.stdout
        soup = BeautifulSoup(html, 'html.parser')
        
        # 微信公众号文章内容在 id="js_content" 或 class="rich_media_content" 中
        content_div = soup.find(id='js_content') or soup.find(class_='rich_media_content')
        
        if content_div:
            # 提取纯文本，保留段落结构
            paragraphs = []
            for elem in content_div.find_all(['p', 'section', 'h1', 'h2', 'h3', 'h4', 'li']):
                text = elem.get_text(strip=True)
                if text and len(text) > 2:
                    paragraphs.append(text)
            
            content = '\n'.join(paragraphs)
            if len(content) > max_chars:
                content = content[:max_chars] + '...(截断)'
            return content
        
        # fallback: 如果是搜狗跳转页，尝试提取可用内容
        # 搜狗链接可能会先跳转到搜狗中间页
        article_content = soup.find('div', class_='txt-box')
        if article_content:
            return article_content.get_text(strip=True)[:max_chars]
        
        # 最后 fallback: 提取 body 文本
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            # 清理空行
            lines = [l for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
            content = '\n'.join(lines[:50])  # 最多50行
            if len(content) > max_chars:
                content = content[:max_chars] + '...(截断)'
            return content
        
        return ''
    except Exception as e:
        return f'[获取失败: {str(e)[:50]}]'


def _init_sogou_cookie():
    """初始化搜狗 Cookie（每次会话调用一次）"""
    try:
        subprocess.run(
            ['curl', '-s', '-c', COOKIE_FILE, '-o', '/dev/null',
             'https://weixin.sogou.com/',
             '-H', f'User-Agent: {MOBILE_UA}'],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass


def search_wechat(query: str, top_num: int = 10, fetch_detail: bool = False, resolve_url: bool = False) -> list:
    """搜索微信公众号文章"""
    _init_sogou_cookie()
    encoded_query = quote(query)
    url = f"https://weixin.sogou.com/weixin?query={encoded_query}&type=2&page=1"
    
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-m", "15",
         "-L",  # follow redirect
         "-b", COOKIE_FILE, "-c", COOKIE_FILE,
         url,
         "-H", f"User-Agent: {MOBILE_UA}",
         "-H", "Referer: https://weixin.sogou.com/"],
        capture_output=True, text=True, timeout=20
    )
    
    if result.returncode != 0:
        print(f"Error: curl failed with code {result.returncode}", file=sys.stderr)
        return []
    
    html = result.stdout
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('li', {'id': lambda x: x and x.startswith('sogou_vr_11002601_box_')})
    
    articles = []
    for item in items[:top_num]:
        title = item.find('h3')
        title_text = title.get_text(strip=True) if title else ''
        
        source = item.find('span', {'class': 'all-time-y2'})
        source_text = source.get_text(strip=True) if source else ''
        
        snippet = item.find('p', {'class': 'txt-info'})
        snippet_text = snippet.get_text(strip=True) if snippet else ''
        
        # 提取日期
        date_script = item.find('span', {'class': 's2'})
        date_text = ''
        if date_script:
            script = date_script.find('script')
            if script and script.string:
                ts_match = re.search(r"'(\d+)'", script.string)
                if ts_match:
                    ts = int(ts_match.group(1))
                    date_text = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        
        # 提取链接（解析真实 mp.weixin.qq.com 链接）
        link_tag = item.find('a', {'target': '_blank'})
        href = ''
        if link_tag and link_tag.get('href'):
            raw_href = link_tag['href']
            if raw_href.startswith('http'):
                sogou_url = raw_href
            else:
                sogou_url = "https://weixin.sogou.com" + raw_href
            # 尝试解析出真实文章链接（通过 onmousedown 属性或直接跟随跳转）
            onmd = link_tag.get('onmousedown', '')
            # 有时真实链接藏在 noscript 中
            noscript = item.find('noscript')
            real_url = ''
            if noscript:
                ns_soup = BeautifulSoup(noscript.decode_contents(), 'html.parser')
                ns_link = ns_soup.find('a')
                if ns_link and ns_link.get('href', '').startswith('http'):
                    real_url = ns_link['href']
            # 也可以从 data-url 属性获取
            if not real_url:
                real_url = link_tag.get('data-url', '')
            # 如果没拿到真实链接：按需解析（resolve_url=True 时才解析，否则保留搜狗链接）
            if real_url and 'weixin.qq.com' in real_url:
                href = real_url
            elif resolve_url:
                href = resolve_real_url(sogou_url)
            else:
                href = sogou_url
        
        if title_text:
            article = {
                'title': title_text,
                'source': source_text,
                'snippet': snippet_text,
                'date': date_text,
                'url': href
            }
            
            # 如果需要详情，抓取文章内容
            if fetch_detail and href:
                article['content'] = fetch_article_content(href)
            
            articles.append(article)
    
    return articles


def main():
    if len(sys.argv) < 2:
        print("用法: python3 wechat_search.py \"关键词\" [数量] [--json] [--detail] [--resolve-url]")
        print("示例: python3 wechat_search.py \"AI Agent\" 5")
        print("      python3 wechat_search.py \"OpenClaw 赚钱\" 3 --detail")
        print("      python3 wechat_search.py \"AI 赚钱\" 5 --resolve-url   # 解析真实微信链接(较慢)")
        print("\n选项:")
        print("  --json         输出JSON格式")
        print("  --detail       获取文章详细内容（每篇需额外请求，较慢）")
        print("  --resolve-url  解析真实 mp.weixin.qq.com 链接（每篇需额外请求，较慢）")
        sys.exit(1)
    
    query = sys.argv[1]
    
    # 解析参数
    args = sys.argv[2:]
    json_mode = '--json' in args
    detail_mode = '--detail' in args
    resolve_mode = '--resolve-url' in args
    
    # 提取数量参数（第一个纯数字参数）
    top_num = 10
    for arg in args:
        if arg.isdigit():
            top_num = int(arg)
            break
    
    articles = search_wechat(query, top_num, fetch_detail=detail_mode, resolve_url=resolve_mode)
    
    if json_mode:
        print(json.dumps(articles, ensure_ascii=False, indent=2))
    else:
        print(f"🔍 搜索「{query}」- 找到 {len(articles)} 篇公众号文章\n")
        for i, a in enumerate(articles, 1):
            print(f"{i}. 【{a['source']}】{a['title']}")
            if a['date']:
                print(f"   📅 {a['date']}")
            if a.get('content') and detail_mode:
                # 显示前200字内容
                content_preview = a['content'][:300].replace('\n', ' ')
                print(f"   📄 {content_preview}")
            elif a['snippet']:
                print(f"   📝 {a['snippet'][:150]}")
            if a['url']:
                print(f"   🔗 {a['url'][:150]}")
            print()


if __name__ == "__main__":
    main()
