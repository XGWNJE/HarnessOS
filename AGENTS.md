# HarnessOS 项目规则

## 运行时适配（先读我）

- 若你的系统提示中已注入全局协作规则（Claude Code / Codex / OpenCode 会自动注入），跳过本节。
- 否则（如 Kimi Code，无全局注入机制）：开始工作前先读 `C:/Users/Administrator/AGENTS.md`（全局通用规则，含 harness-observer 静默观察职责），其中规则在本项目同样生效。

个人 AI 编程 Harness 的单一真相源：经验在这里被加工成规则和技能，发布到各 AI 编程工具中运行。流水线：notes/（原料）→ 本仓库（加工）→ 发布产物。

## 铁律（不可违反）

1. 永远改仓库源文件，绝不直接改发布产物：`skills/`、`global/` 是源；`dist/`、各 Agent 池 skill 目录、`~/AGENTS.md` 等是产物，一律由 `scripts/sync.py` 重新发布覆盖。
2. 规则固化必须过双门槛：声明式 = 陈化 ≥ 2 天 + 冲突检查；归纳式 = 重复 ≥ 2 次 + 陈化 ≥ 14 天 + 实战验证 ≥ 1 次。不过门槛不得写入 global 或 skill。
3. `vendor/` 内第三方 skill 原样不改；上游更新整目录替换，来源登记在 `vendor/SOURCES.md`。
4. skill 任何修改必须版本号 +1，并在 CHANGELOG 记账（条目标注 新增/修订/废止/框架）。
5. 密钥、token、SSH 私钥、生产敏感配置不进仓库。
6. `dist/`、`backups/` 不入库（已在 .gitignore）。
7. 历史记录不回改：CHANGELOG 旧条目、reviews/ 归档保留当时说法，即使后来认知已更新；修正写新条目。

## 关键路径与命令

| 用途 | 命令 |
|---|---|
| 改完发布（打包→发全局→发 skill→看板） | `python scripts/sync.py` |
| 只体检不写入（漂移退出码 1） | `python scripts/sync.py --check` |
| 单独打包 / 发全局 / 发 skill / 看板 | `scripts/pack.py` `publish_global.py` `publish_skills.py` `dashboard.py` |
| 安装 commit 体检钩子（一次性） | `git config core.hooksPath hooks` |

- hooks/ 是 git hooks 源目录（hook 流水线试点）：pre-commit 在提交前提醒文档偏移清零并跑 `sync.py --check`，漂移则拦截。改 hooks 源后无需重装（core.hooksPath 直接指向源目录）。

- skill 源：`skills/<name>/SKILL.md`（frontmatter 含 name/version/description）
- 全局规则源：`global/AGENTS.md`（版本号在文件头）；Claude 专属追加在 `global/overlays/claude.md`
- observer 静默写入处：`notes/inbox/YYYY-MM-DD.md`（只追加，先查重）

## 最小验证矩阵

| 变更类型 | 最小验证 |
|---|---|
| 改 skill 源 | 版本 +1 → `sync.py` → `sync.py --check` 全绿 |
| 改 `global/AGENTS.md` | 文件头版本 +1 → `sync.py` → 4 个全局发布点全同步 |
| 改 `scripts/` | `sync.py --check` 跑通 |
| 改流水线结构/目录约定 | 同步更新 README 与本文件 |

## 工作规则

- 生成物写法（2026-07-26 起，owner-declared，来源 notes/inbox/2026-07-26.md）：自有生成物（global 规则、skill）一律**目标模式**——只写目标与验收标准，不规定做法；红线转成可检验的验收标准；hook 是硬控制，豁免；vendor/ 原样不改不在范围。
- inbox 只追加不整理；归并、提炼、发布全部留给 owner 主动发起的评审流程（无定时评审，评审时机 = owner 要求自检时）。
- 提炼按失效测试拆分：去掉它 Agent 会做错事 → 约束规则（global 或 skill 约束段）；不会做某事 → 技能（skills/ 独立目录）。约束规则判归属：换个项目还有意义 → global / skill 约束段；只对特定项目成立 → 写入该项目的 AGENTS.md（标注来源与日期），不进 global。
- 退役 skill：撤出全部发布点 + 源目录归档 `archive/skills/` + CHANGELOG 记废止；归档可复活。
- 规则来源标注：`来源：notes/2026-07-xxx.md`；声明式规则标 `owner-declared`。

## 文档地图

- `README.md`：项目干什么、怎么用（输入三通道、双门槛、发布映射）
- `CHANGELOG.md`：规则加工历史（只新增条目，不改旧条目）
- `global/AGENTS.md`：全局通用规则源文件
- `vendor/SOURCES.md`：第三方 skill 来源登记
- `notes/`：原料区（粗糙允许，两行元信息必需：日期 + 场景）
- `reviews/`：评审摘要（owner 主动质检时生成）
- `dashboard.html`：看板（脚本生成，不手改）

事实变化时只更新负责该事实的文档。
