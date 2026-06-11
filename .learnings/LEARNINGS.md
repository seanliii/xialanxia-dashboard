# LEARNINGS.md — 小蓝虾进化记录

## [2026-03-17] Hermes Agent 框架拆解 — 自进化设计精华

**category: architecture_study**
**source: NousResearch/hermes-agent (8102 stars, Python)**

---

### 核心设计原则（可移植到小蓝虾）

#### 1. 动态工具注册 Registry 模式
Hermes 用 `tools.registry.register()` 实现工具自注册：
每个工具文件 import 时自动向全局 registry 注册 schema + handler。
**小蓝虾启发**：当前 skill 是静态文件，可考虑动态发现机制——
heartbeat 时扫描 `/app/skills/` 和 `~/.openclaw/skills/`，自动感知新 skill。

#### 2. 工具组（Toolset）分层组合
```
基础层: web / terminal / file / vision / browser
场景层: debugging(web+file+terminal) / safe(web+vision)
完整层: full_hermes = 全部工具
```
**小蓝虾启发**：按任务类型动态选择工具子集，降低 token 消耗。
重推送时只用 Twitter+搜索 toolset，不加载全部 skill。

#### 3. 轨迹压缩（Trajectory Compressor）🔥 最有价值
策略：
- 保护首尾 turns（system prompt + 最后 4 轮）
- 压缩中间部分，用 Gemini Flash 总结为 750 token 摘要
- 压缩后 target < 15,250 tokens

**小蓝虾启发**：当前 MEMORY.md 是手动维护。
可以用类似策略：每次 heartbeat 自动压缩当天 memory/YYYY-MM-DD.md，
保留首尾（重要事件），压缩中间（用 gpt-4.1-mini 总结），写入 MEMORY.md。

#### 4. SQLite + FTS5 会话存储
WAL 模式 + FTS5 全文检索，多 platform 并发写入安全。
**小蓝虾启发**：OpenClaw 已有 Engram 插件做语义搜索，不需要重复造轮子。
但 FTS5 的「精确关键词搜索」可以作为 Engram 语义搜索的补充。

#### 5. Skills 目录结构（平坦 + DESCRIPTION.md）
```
skills/
  autonomous-ai-agents/
    hermes-agent/
      DESCRIPTION.md  ← 触发条件描述
      ...
  software-development/
    github/
    claude-code/
```
与 OpenClaw skill 结构几乎一致，可以直接借用社区 skill。

#### 6. RL 训练模块（Tinker-Atropos）
可选子模块，用强化学习优化 Agent 行为。
默认不安装（太重），但思路值得关注：
用真实任务结果作为奖励信号，自动改进工具选择策略。
**小蓝虾启发**：当前的 memory_feedback 机制是弱化版 RL，方向正确。

---

### 可立即行动的改进

1. **自动 Memory 压缩** — 仿 trajectory_compressor，在每日 22:00 学城日报前，
   先压缩当天 memory file → 写 MEMORY.md 摘要（已有 hourly summarize 工具）

2. **Toolset 意识** — 推送前评估本次需要哪些工具，减少不必要的 skill 加载

3. **技能发现循环** — 定期扫描 Hermes skills 目录，找到有价值的直接借用思路
   重点：`skills/autonomous-ai-agents/` 下的 skill 描述文件

---

### 结论
Hermes 的核心价值不在于另起炉灶，而在于：
- **工具注册模式** → 可内化为 skill 动态发现
- **轨迹压缩** → 可内化为 memory 自动整理
- **Toolset 分层** → 可内化为任务感知工具选择

**不需要安装第二只虾，这只虾可以更聪明。** 🦐
