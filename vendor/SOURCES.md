# 引入 Skill 来源清单

本目录物理存放可静态拷贝的引入 skill；体积大或自带 git 的只登记来源，不拷贝实体。

## 物理引入（原样不改）

| Skill | 来源 | 引入时间 | 说明 |
|---|---|---|---|
| vibehub | https://github.com/oil-oil/vibe-hub-skill （skills/vibehub 目录 + LICENSE） | 2026-07-24 | Vibe Coding 术语学习助手（面向普通人的教学流程，依赖 VibeHub 网站知识源） |
| kimi-webbridge | Kimi 官方 WebBridge 技能（官方页 https://www.kimi.com/features/webbridge ，版本 1.11.3，随 Kimi Code 生态发布；非 git 仓库，从部署的 skill 目录回收） | 2026-08-04 | 浏览器控制：经本地守护进程（127.0.0.1:10086）控制真实浏览器。机制不绑定 Kimi 运行时，HTTP API 通用，任何 Agent 可调用；引入前已散装部署于 .claude/.codex/.config-opencode 三池 |

## 上游更新（owner 问"是否最新"时执行）

vendor 原样不改——不手工修补内容，只整目录替换。以 vibehub 为例：

1. 临时目录 `git clone --depth 1 https://github.com/oil-oil/vibe-hub-skill`
2. 比对上游 `skills/vibehub/`（含 LICENSE）与本地 `vendor/vibehub/`
3. 有差异 → 整目录替换，CHANGELOG 记 [修订]（附上游 commit 哈希），跑 `python scripts/sync.py` 重新发布；无差异 → 直接答复已是最新

## 仅登记来源（不拷贝实体）

| Skill | 来源 | 管理位置 | 更新方式 |
|---|---|---|---|
| skill-creator | https://github.com/anthropics/skills （Anthropic 官方，git clone） | `~/.agents/skills/skill-creator`（自带 .git） | 原地 `git pull`，不入 HarnessOS 库 |

## 不计入管理

`~/.claude/skills` 池现有技能已全部纳入管理（2026-08-04 核验：13 个均为 HarnessOS 发布产物或已登记引入）。后续若新出现来源不明的技能，按「物理引入」或「仅登记来源」流程登记后再对账。
