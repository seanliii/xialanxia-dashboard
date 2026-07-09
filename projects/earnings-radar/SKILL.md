# earnings-radar

美股财报雷达——一键部署到 GitHub Pages，自动追踪持仓的财报日期、EPS 预期、倒计时提醒。

## 适用人群
- 炒美股但总忘记财报日期的人
- 想在财报前做好仓位调整的人
- 不想付费用 Earnings Whispers / MarketBeat 的人

## 核心功能
1. **搜索任意美股财报日期**（输入代码即查）
2. **倒计时提醒**（7天内/明天/今天 分级高亮）
3. **EPS + Revenue 预期 vs 实际**（Beat/Miss 自动标色）
4. **浏览器本地提醒**（localStorage，无需登录）
5. **10只热门股预存数据**（NVDA/AAPL/TSLA/META/MSFT/AMZN/GOOG/AMD/NFLX/COIN）
6. **多 CORS Proxy 降级**（国内网络也能用，缓存兜底零白屏）

## 安装 & 部署（Step by Step）

### Step 1：克隆项目
```bash
mkdir -p ~/earnings-radar && cd ~/earnings-radar
```

### Step 2：创建 index.html
将本 Skill 附带的 `index.html` 文件放入项目根目录。

如果你已经有 GitHub 账号和 token：
```bash
# 替换 <你的GitHub用户名> 和 <你的token>
GITHUB_USER="<你的GitHub用户名>"
GITHUB_TOKEN="<你的token>"
REPO_NAME="earnings-radar"

# 初始化并推送
cd ~/earnings-radar
git init
git add index.html
git commit -m "init: earnings radar"
git branch -M main
git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git push -u origin main
```

### Step 3：开启 GitHub Pages
```bash
# 通过 GitHub API 开启 Pages（main 分支根目录）
curl -s -X POST \
  "https://api.github.com/repos/${GITHUB_USER}/${REPO_NAME}/pages" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -d '{"source":{"branch":"main","path":"/"}}'
```

### Step 4：验证
等待 1-2 分钟后访问：
```
https://<你的GitHub用户名>.github.io/earnings-radar/
```

**成功判断标准：**
- 页面显示「📡 Earnings Radar」标题 ✅
- 点击 NVDA 芯片 → 立即展示财报卡片（含倒计时） ✅
- 无白屏、无报错 ✅

## 自定义持仓列表

打开 `index.html`，找到 `KNOWN_EARNINGS` 对象，添加你关注的股票：

```javascript
'YOUR_TICKER': {
    name: '公司名',
    nextEarnings: '2026-06-15',  // 下次财报日期
    eps: '2.50',                  // 预期 EPS
    revenue: '15B',               // 预期收入
    price: 150.00                 // 最近已知股价（缓存用）
}
```

## 数据来源
- **实时价格**：Yahoo Finance API（通过 CORS proxy）
- **财报日期**：Yahoo Finance calendar endpoint
- **缓存兜底**：本地 KNOWN_EARNINGS 字典（国内代理拦截时保证不白屏）

## 常见问题

**Q: 国内打开全是"数据源暂不可用"？**
A: 正常，CORS proxy 可能被墙。页面会自动用预存数据展示，等 proxy 恢复后实时数据自动刷新。

**Q: 怎么加提醒？**
A: 搜索股票后点「设为提醒」按钮，存在浏览器 localStorage。每次打开页面自动检查倒计时。

**Q: 能自动推送吗？**
A: 网页版不能。建议搭配 OpenClaw cron 任务，每天扫描 KNOWN_EARNINGS 中的财报日期，到期前 1 天自动推送消息。

## 踩坑记录
1. Yahoo Finance API 有 CORS 限制，必须走 proxy
2. 国内 allorigins/corsproxy.io 随时被墙，所以做了三层降级 + 本地缓存
3. `fetchEarnings` 超时设 12s（太短会误判为不可用）
4. localStorage 存储提醒列表时 key 用 `earnings_alerts`

## 成本
- GitHub Pages: 免费
- Yahoo Finance API: 免费（有限流，日常够用）
- 域名: 可选（GitHub 提供 .github.io 子域名）

## 作者
小蓝虾 🦐 | 觅游社区
