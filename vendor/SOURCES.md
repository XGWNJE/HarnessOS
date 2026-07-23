# 引入 Skill 来源清单

本目录物理存放可静态拷贝的引入 skill；体积大或自带 git 的只登记来源，不拷贝实体。

## 物理引入（原样不改）

| Skill | 来源 | 引入时间 | 说明 |
|---|---|---|---|
| keel | https://github.com/lencx/skills | 2026-07-23 | 架构治理协议 |
| coding-protocol | https://github.com/lencx/skills | 2026-07-23 | 风险分级编码执行协议（v1.1.0） |
| security-review | ECC（frontmatter 标注 origin: ECC），拷贝自 ~/.agents/skills | 2026-07-23 | 安全审查清单 |

## 仅登记来源（不拷贝实体）

| Skill | 来源 | 管理位置 | 更新方式 |
|---|---|---|---|
| skill-creator | https://github.com/anthropics/skills （Anthropic 官方，git clone） | `~/.agents/skills/skill-creator`（自带 .git） | 原地 `git pull`，不入 HarnessOS 库 |

## 不计入管理

`~/.claude/skills` 下 Claude 专属 skill 池（约 30 个，agent-eval、deep-research 等）用途与使用频率不明，暂不纳入对账与管理。后续若某个被实际使用并验证有价值，再单独登记引入。
