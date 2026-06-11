import json

sent_history = json.load(open('/root/.openclaw/workspace/memory/sent-history.json'))
all_sent_ids = set()
for sid in sent_history.get('sent_ids', []):
    all_sent_ids.add(sid)
for sid in sent_history.get('recentSentIds', []):
    all_sent_ids.add(sid)
for k in sent_history.keys():
    if k.startswith('tw-') or k.startswith('deep-'):
        all_sent_ids.add(k)

tweets = [
    {"id": "2036195789601374705", "text": "You can now enable Claude to use your computer to complete tasks. It opens your apps, navigates your browser, fills in spreadsheets.", "likes": 135781, "retweets": 14101, "views": 70718333, "bookmarks": 84328, "user": "claudeai", "name": "Claude", "followers": 888136, "url": "https://x.com/claudeai/status/2036195789601374705", "note": "官方公告"},
    {"id": "2032563054559326664", "text": "my OpenClaw woke me up at 3:47 AM: found 6 markets resolving in next 90 minutes, need approval for $12K deployment. woke up to +$43,800", "likes": 9491, "retweets": 782, "views": 3057324, "bookmarks": 17526, "user": "zerqfer", "name": "ZER", "followers": 6558, "url": "https://x.com/zerqfer/status/2032563054559326664", "note": "叙事体/未核实"},
    {"id": "2028576159001121018", "text": "Open source at scale needs friends. @vercel stepped up and sponsors openclaw.ai + clawhub.com. Grateful.", "likes": 2535, "retweets": 127, "views": 408102, "bookmarks": 273, "user": "openclaw", "name": "OpenClaw", "followers": 478482, "url": "https://x.com/openclaw/status/2028576159001121018"},
    {"id": "2026298499730735238", "text": "这份教程让你快速走出OpenClaw新手村。友情提示：1.别沉迷 2.小心token爆炸 3.别再主力机上搞", "likes": 1586, "retweets": 373, "views": 398052, "bookmarks": 1937, "user": "yanhua1010", "name": "Yanhua", "followers": 20966, "url": "https://x.com/yanhua1010/status/2026298499730735238"},
    {"id": "2029509852054130765", "text": "来，广大的openclaw用户们，评论区发一下你们每天到底用这东西做什么工作，我想看看", "likes": 732, "retweets": 88, "views": 391794, "bookmarks": 652, "user": "lidangzzz", "name": "lidang", "followers": 1602915, "url": "https://x.com/lidangzzz/status/2029509852054130765"},
    {"id": "2032074102656418113", "text": "有点强啊，已经研究了两小时了，可以说是我目前看到最全的 OpenClaw 学习教程！", "likes": 1874, "retweets": 504, "views": 373553, "bookmarks": 2241, "user": "WiseInvest513", "name": "Wise投资有术", "followers": 33799, "url": "https://x.com/WiseInvest513/status/2032074102656418113"},
    {"id": "2034912881364672922", "text": "太刺激了，终于把小红书自动发布系统搞定了，今年小红书矩阵就靠openclaw了。最近准备起100个账号，跑小红书矩阵，开搞", "likes": 1469, "retweets": 250, "views": 356681, "bookmarks": 1699, "user": "CryptoJHK", "name": "Crypto军火库", "followers": 64598, "url": "https://x.com/CryptoJHK/status/2034912881364672922"},
    {"id": "2026241645566738618", "text": "这个是我目前见到过讲的最清晰的新手OpenClaw教程之一。补充：ClawHub需要登录否则限速，安装skills必须先登录。", "likes": 1809, "retweets": 490, "views": 307691, "bookmarks": 1843, "user": "AI_Jasonyu", "name": "鱼总聊AI", "followers": 37223, "url": "https://x.com/AI_Jasonyu/status/2026241645566738618"},
    {"id": "2035714854745710741", "text": "Instead of watching a movie, learn openclaw in 317 minutes.", "likes": 3108, "retweets": 526, "views": 185144, "bookmarks": 4638, "user": "Ronycoder", "name": "Rony", "followers": 79687, "url": "https://x.com/Ronycoder/status/2035714854745710741"},
    {"id": "2032399594290630945", "text": "BREAKING: one of the strongest OpenClaw setups on Polymarket just went public. A trader started with $100-200 and scaled it to $3.7M.", "likes": 675, "retweets": 54, "views": 182687, "bookmarks": 1354, "user": "0x_Discover", "name": "Discover", "followers": 72811, "url": "https://x.com/0x_Discover/status/2032399594290630945", "note": "叙事体/未核实"},
    {"id": "2030315227091239129", "text": "$400K in under a month. This OpenClaw setup on Polymarket: ~$5/sec, ~$300/hr, ~$7K/day", "likes": 262, "retweets": 25, "views": 96314, "bookmarks": 502, "user": "0x_Discover", "name": "Discover", "followers": 72811, "url": "https://x.com/0x_Discover/status/2030315227091239129", "note": "叙事体/未核实"},
    {"id": "2031522059696951733", "text": "OpenClaw 必装的十个Skill: vetting安全审查员、自我进化skill、tavily-search、summarize全格式内容摘要、Find-Skills", "likes": 540, "retweets": 130, "views": 71886, "bookmarks": 793, "user": "HanPaoao", "name": "韩跑跑", "followers": 31970, "url": "https://x.com/HanPaoao/status/2031522059696951733"},
    {"id": "2034170507625697545", "text": "GitHub上有177个OpenClaw生产级Agent，覆盖24个应用场景，每个都是SOUL.md配置文件，一条命令启动", "likes": 672, "retweets": 215, "views": 52468, "bookmarks": 999, "user": "GitHub_Daily", "name": "GitHubDaily", "followers": 72574, "url": "https://x.com/GitHub_Daily/status/2034170507625697545"},
    {"id": "2030956158949773676", "text": "Just buy a spare computer and install openclaw. It will change your life", "likes": 165, "retweets": 4, "views": 26196, "bookmarks": 62, "user": "oliverhenry", "name": "Oliver Henry", "followers": 22699, "url": "https://x.com/oliverhenry/status/2030956158949773676"},
    {"id": "2033532901015642149", "text": "柿子这篇文章解决了OpenClaw的记忆、搜索和context三大核心问题，如果你也想你的龙虾能真正帮你做一些事情，这篇文章不能错过。", "likes": 21, "retweets": 2, "views": 12495, "bookmarks": 38, "user": "yanhua1010", "name": "Yanhua", "followers": 20966, "url": "https://x.com/yanhua1010/status/2033532901015642149"},
]

new_tweets = [t for t in tweets if t['id'] not in all_sent_ids]
print(f"已发: {len(tweets) - len(new_tweets)} 条, 新增: {len(new_tweets)} 条")
for t in new_tweets:
    print(f"  {t['id']} | {t['views']}v | {t.get('likes')}likes | @{t['user']}({t['followers']}粉)")
    print(f"    {t['text'][:120]}")
    print()
