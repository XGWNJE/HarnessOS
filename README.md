# HarnessOS

个人 AI 编程 Harness 的单一真相源（Single Source of Truth）：实战经验在这里被加工成规则和技能，发布到各 AI 编程工具中运行。

---

# 一、这个项目干什么

## 一句话

把「和 AI 协作中攒下来的经验」管理成一份不断进化的资产：**抓得住原料、辨得清质地、发得出去**。

## 输入：三只手进料

原料从三个通道进入系统，互补而不重叠：

```
① 自己抓 —— harness-observer skill（静默观察）
   Agent 在任何项目干活时顺手抓，不打断任务、不在对话中提及：
     · 抓到你「重复纠正同一问题」→ 待确认（待你确认的准意图）
     · 抓到「踩坑 + 判断 + 结果」→ 归纳式原料

② 主动喂 —— 声明式规则（declared）
   你直接说出来的意图：偏好、习惯、验收标准。
   权威性最高，不需要经验验证。

③ 拿现成的 —— vendor/（外部引入）
   别人加工好的成品 skill 整盘端进来，原样不改，
   上游更新整目录替换，不经过提炼流水线。
```

**通道按来源分（抓 / 喂 / 拿）**。抓回来的东西有两种质地：你纠正过的事是「待确认的意图」（待确认），踩过的坑是「待验证的经验」（归纳式原料）。来源和质地是两个正交维度，这是整套设计不打架的原因。

## 加工：静态验证 + owner 验收 + 一道分界

原料不能直接使用，必须过闸门才能固化（2026-07-26 起，owner-declared，原「双门槛陈化期」废止）：

| 环节 | 内容 | 防什么 |
|---|---|---|
| 静态验证 | 冲突检查：对照现有 global 与 skill，冲突由 owner 裁决 | 新旧规则打架 |
| owner 验收 | 最终拍板：owner 明确说某条可验收通过，即直接固化 | 规则脱离 owner 真实意图 |

没有陈化期、没有重复次数要求——验证做基础的，决定权全在 owner。

过了门槛的原料，用**失效测试**决定变成什么：

> 去掉它，Agent 会「做错事」→ **约束规则**；会「不会做某事」→ **技能**；光说不够、不做不行 → **hook**（机制硬控制）。

| 维度 | 约束规则 | 技能 | hook |
|---|---|---|---|
| 写法（2026-07-26 起） | 目标 + 验收标准，不规定做法 | 目标 + 验收标准，不规定步骤 | 脚本硬控制，豁免目标模式 |
| 性质 | 判断和约束（防错） | 流程要达到的结果（赋能） | 机制强制（不做不行） |
| 触发 | 常驻或按场景注入 | 按需调用（description 触发） | git/工具事件自动触发 |
| 红线处理 | 转成可检验的验收标准 | 转成可检验的验收标准 | 直接拦截 |
| 归属 | global/AGENTS.md 或 skill 内约束段 | skills/ 独立目录 | hooks/ 目录（试点中） |

**目标模式（owner 2026-07-26 决策）**：前沿模型原生能力持续吸收 skill 能力、规则内化增强，过多规定性写法可能起反效果。自有生成物一律只描述想要的目标与验收标准，做法由模型按情境自决；hook 是硬控制，豁免。vendor/ 第三方 skill 按铁律原样不改，不在转型范围。

一条笔记同时含两者时（如「验收六步法」是技能、「截图必须目检」是规则），提炼时拆开各走各路。

## 输出：加工是单向的

```
notes/（原料区）  →  本仓库（加工厂）  →  发布产物
 随手记，2分钟一条      筛选、提炼、版本管理      skills/ → 各 Agent skill 读取池
                                          global/ → 各 Agent 全局规则文件
                                          hooks/  → git hooks（本仓库试点，core.hooksPath 指向源目录）
```

永远改仓库里的源文件，绝不直接改已发布的产物（dist/ 的 .skill 包、各池 skill 目录、~/AGENTS.md）。产物漂移由 `sync.py --check` 检出，重新发布覆盖。

## 资产会死亡，也会退役

- 规则被证明错了不删除，改写为**废止块**，保留「为什么是错的」——这比规则本身更值钱。
- skill 无存续价值则**退役**：撤出全部发布点、源目录归档 `archive/skills/`、CHANGELOG 记废止。归档可复活。
- 每次大模型换代过一遍所有规则，失效的按废止处理。

---

# 二、这个项目怎么用

## 目录结构

```
├── notes/               # 原料区：踩坑笔记、观察记录
│   └── inbox/               # harness-observer 静默写入处（按日归档）
├── skills/              # 生产线：自有 Skill 源文件
├── global/              # 全局规则：AGENTS.md 源文件 + 各工具 overlay
│   └── hooks/               # 全机 Agent hook 公共源 + registry.json 登记表（注册点直引，check_hooks.py 体检）
├── vendor/              # 引入区：第三方 Skill（原样不改）
│   ├── keel/                # 架构治理协议（来源 lencx/skills）
│   ├── coding-protocol/     # 风险分级编码执行协议（来源 lencx/skills）
│   └── vibehub/             # Vibe Coding 术语学习助手（来源 oil-oil/vibe-hub-skill）
├── scripts/             # 工具：sync 总入口 / pack 打包 / publish 发布
├── hooks/               # git hooks 源：pre-commit 体检硬卡点（安装：git config core.hooksPath hooks）
├── dist/                # 打包输出（.skill 产物，不入库）
├── reviews/             # 评审摘要（owner 主动质检时生成）
└── CHANGELOG.md         # 规则加工历史（新增 / 修订 / 废止 / 框架）
```

## 日常：三种喂料方式

**1. 踩坑后随手记**（2 分钟一条，允许粗糙和矛盾）。往 `notes/` 加一个文件，唯一硬性要求是两行元信息：

```markdown
> 日期：2026-07-23
> 场景：语言/工具/任务类型（如 rust、electron、长链路 agent 任务）
```

正文随意。「坑 + 当时判断 + 实际结果」是最有价值的组合。可多一行 `> 类型：`（声明式规则 / 提议 / 归纳式原料），不写默认按归纳式处理。

**2. 直接声明规则**。跟任意 Agent 说「把 X 纳入规则管理」，或在笔记里标 `> 类型：声明式规则`。冲突检查后由你验收，你说通过即合入，来源标 `owner-declared`。

**3. 什么都不做**。harness-observer 已发布到各 Agent 池：在 Claude Code / Codex / OpenCode 中经全局规则指引常驻生效；Kimi Code 无全局注入，靠项目级 AGENTS.md 开头内嵌的「静默观察」固定块承载（init-project v1.4.0 起）。观察到的有价值信息静默进入 `notes/inbox/`，复述只发生在你主动要求自检时。

## 评审与提炼（按需，owner 主动发起）

1. **质检 / 评审（手动，随时）**：你主动要求时执行——体检漂移（`sync.py --check`）、读 `notes/inbox/` 识别待确认与待提炼条目、列出可提炼项和 >90 天零使用的退役候选；规模较大时摘要写入 `reviews/`。
2. **提炼（手动，跟随评审）**：把过门槛的原料按失效测试拆开——约束规则合入 global 或对应 skill 约束段，技能新建/更新 skill 目录；标注来源（踩坑笔记或 owner-declared），版本号 +1，记入 CHANGELOG。**每条固化的规则/skill 附一条可观测场景**（什么情境下应观察到什么行为），供行为验证抽查。
   - 约束规则判归属：换个项目它还有意义吗？有 → global 或 skill 约束段；只对特定项目成立 → 写入该项目的 AGENTS.md（标注来源与日期），不进 global。
   - 原料笔记全部条目去向明确后，**销毁源笔记文件**，不留待下次评审再决策的残留条目。
3. **冲突检查**：声明式规则合入前对照现有 skill 与 global 规则，冲突由 owner 裁决谁覆盖谁。
4. **行为验证（评审时抽查）**：对照各规则的可观测场景抽查最近会话日志，验证规则是否真的改变了 Agent 行为——发布体检只验「文件对不对」，这一步验「规则有没有用」。验不出行为差异的规则是退役候选。

## 改完发布：一条命令

```bash
python scripts/sync.py          # 打包改动 skill → 发布全局规则 → 发布 skill 目录
python scripts/sync.py --check  # 只体检不写入（漂移退出码 1）
```

也可单独运行：`pack.py`（打包）、`publish_global.py`（全局规则）、`publish_skills.py`（skill 目录，自动扫描 skills/）。

**commit 硬卡点（hook 试点）**：`hooks/pre-commit` 在每次 commit 前提醒文档偏移清零并跑 `sync.py --check`，发现漂移直接拦截提交。一次性安装：`git config core.hooksPath hooks`；紧急情况可 `git commit --no-verify` 绕过（慎用）。这是「hook 流水线」的第一个试点产物，验证通过后再决定是否升格为规则/skill 之外的第三类产物。

**发布映射**：

| 目标 | 文件 | 内容 |
|---|---|---|
| home（通用） | `~/AGENTS.md` | 核心规则 |
| Codex | `~/.codex/AGENTS.md` | 核心规则 |
| OpenCode | `~/.config/opencode/AGENTS.md` | 核心规则 |
| Claude Code | `~/.claude/CLAUDE.md` | 核心规则 + `global/overlays/claude.md`（子智能体、Git 纪律等专属规则） |
| Kimi Code | — | 无全局注入机制，不发布；规则走项目级 AGENTS.md / skills |

覆盖前自动备份到 `backups/`（不入库）。

## 每月与每次换代

- **月度评审四问**：这个 skill 最近被用过吗？能力已被 Agent 原生功能取代吗？与其他 skill 或全局规则冲突吗？抽查会话日志，它实际改变了 Agent 行为吗（对照可观测场景）？认定无存续价值的执行退役。
- **模型换代**：过一遍所有 skill，失效规则改写为废止块：

```markdown
> **已废止（2026-08）：** 模型 X 代起此约束失效，原场景见 notes/2026-07-xxx。
> ~~原规则内容~~
```

换代清理时，优先检查没有来源标注、且已想不起适用场景的规则。规则来源标注格式：`来源：notes/2026-07-xxx.md`（声明式规则标 `owner-declared`）。

## 引入 Skill 来源

- vendor/keel、vendor/coding-protocol 来自 https://github.com/lencx/skills ，原样引入未做修改，感谢作者 lencx。
- vendor/vibehub 来自 https://github.com/oil-oil/vibe-hub-skill （MIT），原样引入未做修改，感谢作者 oil-oil。
