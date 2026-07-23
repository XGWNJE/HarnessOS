# HarnessOS

个人 AI 编程 Harness 的单一真相源（Single Source of Truth）。实战产生原料，这里加工成规则，打包成 Skill 发布到各 AI 编程工具中运行。

## 三层流水线

```
notes/（原料区）  →  本仓库（加工厂）  →  发布产物
 随手记，2分钟一条      筛选、提炼、版本管理      skills/ → .skill 导入各 AI 工具
                                          global/ → ~/AGENTS.md 供所有 Agent 注入
```

- **notes/**：原始输入。踩坑记录、判断、实验结论。允许粗糙和矛盾，事后证明错了也没关系。唯一硬性要求：2 分钟内能记完，且带最低限度的结构（见下）。
- **skills/**：加工完成品。**只放自有 skill**，只含当前生效的规则，按场景拆分成单一职责的小 skill，靠 description 精准触发。
- **global/**：全局协作规则的源文件，发布为 `~/AGENTS.md`（如 `C:\Users\Administrator\AGENTS.md`）。只放跨项目通用、与具体仓库无关的规则；全局/项目的归属边界写在文件开头。注：Kimi Code 不注入全局规则，但此文件服务于所有注入它的 Agent，且「哪些规则归全局、哪些归项目」的边界本身需要一处维护——后续视情况把边界管理提炼为独立 skill。
- **vendor/**：引入的第三方 skill，原样保留，不做任何修改。上游更新时整目录替换，并在 CHANGELOG 记录来源与新版本。
- **加工是单向的**：永远改仓库里的源文件，绝不直接改已发布的产物（.skill、~/AGENTS.md）。

## 目录结构

```
├── notes/               # 原料区：踩坑笔记、观察记录
├── skills/              # 生产线：自有 Skill 源文件
│   ├── ai-stack-harness/    # AI 编程技术栈选型 Harness
│   └── ai-coding-workflow/  # AI 编程工作流 Harness
├── global/              # 全局规则：AGENTS.md 源文件，发布到 ~/AGENTS.md
├── vendor/              # 引入区：第三方 Skill（原样不改）
│   ├── keel/                # 架构治理协议（来源 lencx/skills）
│   └── coding-protocol/     # 风险分级编码执行协议（来源 lencx/skills）
├── scripts/             # 工具：pack.py 打包、publish_global.py 发布全局规则、dashboard.py 生成看板
├── dist/                # 打包输出（.skill 产物，不入库）
├── dashboard.html       # 规则资产看板（脚本生成，不手改）
└── CHANGELOG.md         # 规则加工历史
```

## 笔记的最低结构

notes/ 允许粗糙，但每条笔记必须带两行元信息，否则月度提炼时无法归并：

```markdown
> 日期：2026-07-23
> 场景：语言/工具/任务类型（如 rust、electron、长链路 agent 任务）
```

正文随意。「坑 + 当时判断 + 实际结果」是最有价值的组合。

## 规则的生命周期

每条规则有三种状态变更，全部记入 CHANGELOG，条目类型标注为 **新增 / 修订 / 废止**：

1. **新增**：notes/ 中重复出现 2 次以上的坑，提炼为规则合入对应 skill，版本号 +1。
2. **修订**：规则被实践证明不准确，改写法、改适用边界。版本号 +1。
3. **废止**：规则被证明错了，或因模型换代失效。**不删除，改写为废止块**，保留「为什么是错的」——这比规则本身更值钱：

```markdown
> **已废止（2026-08）：** 模型 X 代起此约束失效，原场景见 notes/2026-07-xxx。
> ~~原规则内容~~
```

## 规则溯源

每条规则尽量标注来源笔记（一行即可），便于废止/清理时回溯原始场景：

```
来源：notes/2026-07-vibe-coding-观察.md
```

模型换代清理时，优先检查没有来源标注、且已想不起适用场景的规则。

## 运转节奏

1. **每次踩坑后**：往 notes/ 记一条，带上日期和场景两行元信息。
2. **每月 / 每项目收尾**：翻笔记，重复出现 2 次以上的坑提炼成规则，合入对应 skill，标注来源，版本号 +1，记入 CHANGELOG（新增/修订/废止）。
3. **每次大模型换代**：过一遍所有 skill，失效规则按「废止」处理，不直接删。
4. **发布**：skill 源文件改动后运行 `python scripts/pack.py` 重新打包为 .skill（输出到 dist/），导入 Kimi Code / Codex / Claude Code 更新；`global/AGENTS.md`（或 overlay）改动后运行 `python scripts/publish_global.py` 发布到各 Agent 读取位置，版本号 +1，记入 CHANGELOG。
5. **看板**：规则或笔记变化后运行 `python scripts/dashboard.py` 重新生成 `dashboard.html`，浏览器打开即可总览全局。

## 全局规则发布映射

| 目标 | 文件 | 内容 |
|---|---|---|
| home（通用） | `~/AGENTS.md` | 核心规则 |
| Codex | `~/.codex/AGENTS.md` | 核心规则 |
| OpenCode | `~/.config/opencode/AGENTS.md` | 核心规则 |
| Claude Code | `~/.claude/CLAUDE.md` | 核心规则 + `global/overlays/claude.md`（子智能体、Git 纪律、代码语言等专属规则） |
| Kimi Code | — | 无全局注入机制，不发布；规则走项目级 AGENTS.md / skills |

`publish_global.py --check` 只检查漂移不写入；覆盖前自动备份到 `backups/`（不入库）。

## 引入 Skill 来源

- vendor/keel、vendor/coding-protocol 来自 https://github.com/lencx/skills ，原样引入未做修改，感谢作者 lencx。
