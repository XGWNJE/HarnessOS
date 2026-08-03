# 引入 Skill 来源清单

本目录物理存放可静态拷贝的引入 skill；体积大或自带 git 的只登记来源，不拷贝实体。

## 物理引入（原样不改）

| Skill | 来源 | 引入时间 | 说明 |
|---|---|---|---|
| vibehub | https://github.com/oil-oil/vibe-hub-skill （skills/vibehub 目录 + LICENSE） | 2026-07-24 | Vibe Coding 术语学习助手（面向普通人的教学流程，依赖 VibeHub 网站知识源） |

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

`~/.claude/skills` 下 Claude 专属 skill 池（约 30 个，agent-eval、deep-research 等）用途与使用频率不明，暂不纳入对账与管理。后续若某个被实际使用并验证有价值，再单独登记引入。
