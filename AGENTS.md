# HarnessOS 项目规则

## 常驻职责（无全局注入的运行时适用，如 Kimi Code；其余运行时全局规则已覆盖，跳过）

- 静默观察：干活全程留意四类信号——owner 重复纠正、owner 明确表达的偏好、可复用踩坑、你自身的语义失败（假设/目标/路径/范围错误）；命中静默追加到 `$HARNESSOS_ROOT/notes/inbox/YYYY-MM-DD.md`（变量未设置时按 harness-observer skill 寻址；先查重，同主题重复计数 +1，脱敏），不打断当前任务、不在对话中提及；格式与验收以 harness-observer skill 为准。
- 中转站真机验证：开发内容未外部发版、仍在测试阶段，且用户在用模拟器/虚拟机调试验证、未连真机时，主动询问是否把构建产物传到中转站（get.xgwnje.cn）供真机测试；问过才传，不擅自上传。
- 全局规则路径指针：全局通用规则在 `~/AGENTS.md`；任务涉及通用协作约定（提交信息格式、分支受控、设备调试等）时按需查阅相关段落，不整体预读。

Agent 长期约束的备份分发引擎（owner-declared 2026-08-04）：经验在这里被加工成规则和技能（单一真相源在本仓库），发布到各 AI 编程工具中运行。流水线：notes/（原料）→ 本仓库（加工）→ 发布产物。

## 铁律（不可违反）

1. 永远改仓库源文件，绝不直接改发布产物：`skills/`、`global/` 是源；`dist/`、各 Agent 池 skill 目录、`~/AGENTS.md` 等是产物，一律由 `scripts/sync.py` 重新发布覆盖。
2. 规则固化只过一道静态验证（冲突检查：对照现有 global 与 skill，冲突由 owner 裁决），最终由 owner 验收拍板——owner 明确说某条可验收通过，即直接固化，无陈化期、无重复次数要求（2026-07-26 起，owner-declared，原双门槛废止）。
3. `vendor/` 内第三方 skill 原样不改；上游更新整目录替换，来源登记在 `vendor/SOURCES.md`。
4. skill 任何修改必须版本号 +1，并在 CHANGELOG 记账（条目标注 新增/修订/废止/框架）。
5. 密钥、token、SSH 私钥、生产敏感配置不进仓库。
6. `dist/`、`backups/` 不入库（已在 .gitignore）。
7. 历史记录不回改：CHANGELOG 旧条目、reviews/ 归档保留当时说法，即使后来认知已更新；修正写新条目。

## 关键路径与命令

| 用途 | 命令 |
|---|---|
| 安装/迁移装机（写 env + 发布 + 体检） | `python scripts/install.py` |
| 改完发布（打包→发全局→发 skill） | `python scripts/sync.py` |
| 只体检不写入（漂移退出码 1） | `python scripts/sync.py --check` |
| 单独打包 / 发全局 / 发 skill | `scripts/pack.py` `publish_global.py` `publish_skills.py` |
| hook 登记体检（漂移退出码 1） | `scripts/check_hooks.py` |
| MCP 登记体检（漂移退出码 1） | `scripts/check_mcp.py` |
| 文档结构体检（职责越界/堆积退出码 1） | `scripts/check_docs.py` |
| 安装 commit 体检钩子（一次性） | `git config core.hooksPath hooks` |

- hooks/ 是 git hooks 源目录（hook 流水线试点）：pre-commit 在提交前提醒文档偏移清零、跑 `sync.py --check` 与 `check_docs.py`（文档体检），发现漂移或文档职责越界则拦截，保底流程是运行 doc-structure skill 修复。改 hooks 源后无需重装（core.hooksPath 直接指向源目录）。
- `global/hooks/` 是全机 Agent hook 的公共源目录与登记中心：observer_reminder.py（kimi 收口保底）、kimi-codex-hook-adapter.py（kimi→codex 负载适配器，被 Server-infra / Codex-Journal 的 hook 共用）。注册点（kimi config.toml / codex hooks.json）一律直引源路径、无发布拷贝，改源即生效；kimi 无默认 hook 目录与项目级配置，注册是唯一加载通道。`registry.json` 是全部注册（含项目私有 hook）的单一事实源，`scripts/check_hooks.py` 据此体检（只读不写，漂移手工修复），已并入 `sync.py` 两种模式。
- `global/mcp/` 是全机 MCP 服务器登记中心：`registry.json` 是单一事实源（登记各工具配置位置与服务器清单，enabled 开关属各工具侧状态），`scripts/check_mcp.py` 据此体检（只读不写，漂移手工修复：登记过的必须存在、实际存在的必须已登记），已并入 `sync.py` 两种模式。

- skill 源：`skills/<name>/SKILL.md`（frontmatter 含 name/version/description）
- 全局规则源：`global/AGENTS.md`（版本号在文件头）
- observer 静默写入处：`notes/inbox/YYYY-MM-DD.md`（只追加，先查重）

## 最小验证矩阵

| 变更类型 | 最小验证 |
|---|---|
| 改 skill 源 | 版本 +1 → `sync.py` → `sync.py --check` 全绿 |
| 改 `global/AGENTS.md` | 文件头版本 +1 → `sync.py` → 4 个全局发布点全同步 |
| 改 `scripts/` | `sync.py --check` 跑通 |
| 改 README / 文档结构 | `check_docs.py` 通过（行数/禁止词/导航）→ `sync.py --check` 全绿 |
| 改流水线结构/目录约定 | 同步更新 README 与本文件 |

## 工作规则

- 框架冷冻期（2026-07-26 起 14 天，owner-declared，至 2026-08-09）：期间不做框架类变更（新增机制、改流程、立术语、新建/拆除流水线环节），只加原料、修 bug、按既有流程验收规则条目；owner 可一句话豁免。背景：建仓 4 天 6 次框架决策、3 次 48 小时内反转，框架跑在原料前面。
- 生成物写法（2026-07-26 起，边界 2026-07-27 owner 拍板，来源 notes/inbox/2026-07-26.md）：**目标模式仅针对规则类生成物**（global 规则及规则条目）——只写目标与验收标准，不规定做法；红线转成可检验的验收标准。skill 与 hook 不参与（hook 是硬控制）；skill 标准写法（2026-07-30 owner 拍板）：目标与验收标准为主体 + 参考流程为锚点——离开它任务做不成的机制写死为参考标准，做法细节由模型按情境自决。vendor/ 原样不改不在范围。
- inbox 只追加不整理；归并、提炼、发布全部留给 owner 主动发起的评审流程（无定时评审，评审时机 = owner 要求自检时）。
- 验收评审回复固定格式（owner-declared 2026-07-30）：已处理完毕的条目直接清除、不再显示，不占上下文；未处理条目按序号、按重要/推荐程度降序排列，每条标注类型与推荐的判断去处。
- 加工即销毁：原料笔记（notes/、notes/inbox/）中的条目一旦加工完毕（去向明确：提炼进 skill/global/hook，或 owner 明确决定丢弃/继续观察），立即销毁源笔记文件，不留待 owner 下次评审再决策的残留条目。来源：owner 2026-07-29 指示。
- 提炼按失效测试拆分：去掉它 Agent 会做错事 → 约束规则（global 或 skill 约束段）；不会做某事 → 技能（skills/ 独立目录）。约束规则判归属：换个项目还有意义 → global / skill 约束段；只对特定项目成立 → 写入该项目的 AGENTS.md（标注来源与日期），不进 global。
- 退役 skill：撤出全部发布点 + 源目录归档 `archive/skills/` + **清除发布池残留**（`~/.agents`、`~/.codex`、`~/.claude` 三池 + `~/.config/opencode/skills` 私有池 + `dist/` 历史包）+ CHANGELOG 记废止；归档可复活。验收：`publish_skills.py --check` 无 `[残留]` 报告（脚本自动检测源外残留，来源：security-review 退役残留事件 2026-08-04）。
- 全局规则编写原则（owner-declared，2026-07-31）：能精简就精简，最少的话讲清最明确的规则。规则文件目标读者是机器（Agent），不是人——机器准确理解并执行最重要，节省上下文同等重要。验收：每条规则验收标准不超过两句话；无歧义、无冗余。
- 规则术语与来源标注：声明式规则（owner 显式声明）标 `owner-declared`；归纳式规则（踩坑归纳）标 `来源：notes/2026-07-xxx.md`；固化流程见铁律 2（术语定义原在全局「术语」节，2026-08-04 归属评审迁回本文件）。
- 归属收口（2026-08-04 全局归属评审）：新声明判归属时，主题已有 skill 落地机制的直接进该 skill，不再写入全局——防全局与 skill 两处漂移（历史实例：文档分工在全局与 doc-structure 两处表述漂移）。
- 加工成果最小验证矩阵通过后自动提交一次，无需再请示（owner-declared 2026-08-04）；提交信息仍按全局规则（改了什么、为什么、影响范围）。

## 文档地图

- `README.md`：面向人——项目干什么、怎么开始、文档导航（其余全部链接，操作细节一律不出现）
- `CHANGELOG.md`：规则加工历史（只新增条目，不改旧条目）
- `global/AGENTS.md`：全局通用规则源文件
- `vendor/SOURCES.md`：第三方 skill 来源登记
- `notes/`：原料区（粗糙允许，两行元信息必需：日期 + 场景）
- `reviews/`：评审摘要（owner 主动质检时生成）

文档结构与风格由 doc-structure skill 维护（多项目共用同一套模板与验收标准）：README 职责越界/堆积由 `scripts/check_docs.py` 机械拦截（pre-commit 联动），修复走 doc-structure skill 保底流程。

事实变化时只更新负责该事实的文档。
