# CHANGELOG

条目标注类型：新增 / 修订 / 废止 / 框架。

## 2026-07-23 — skill 导入三个工具

- [框架] `publish_skills.py` 扩展为 6 个自有 skill × 3 个读取池（~/.agents/skills 共享池、~/.codex/skills Codex 池、~/.claude/skills Claude 池）共 18 个发布点；修复符号链接目标的处理（Codex 池 vps-server-info 原为符号链接，已备份并替换为实体目录）
- [修订] 消除 Codex 池 vps-server-info 旧版分叉（第 3 处分叉）
- Kimi Code CLI 无独立 skills 目录（config 仅有 merge_all_available_skills 开关），不单独发布，待实测确认其读取来源；.skill 包保留为分发格式
- 看板同步徽章增至 22 个（18 skill 发布点 + 4 全局规则发布点），全绿

## 2026-07-23 — 规则体系分层对齐

- [修订] `init-project` v1.0.0 → v1.1.0：明确分层——通用规则内容与归属判断以 HarnessOS `global/AGENTS.md` 源文件为准（~/AGENTS.md 为发布产物），本 skill 只做项目侧（调查项目事实、起草项目级 AGENTS.md、清理副本漂移）；「规则上浮」明确指向改 HarnessOS 源文件 + sync.py；不再自行重复定义全局/项目边界
- [修订] 全局规则 v1.1.0 → v1.2.0：「全局 / 项目的边界」补双向引用——项目级规则的建立重整由 init-project 执行；上浮操作指向 HarnessOS 源文件 + sync.py

## 2026-07-23 — 总入口 + 看板单屏化

- [框架] 新增 `scripts/sync.py`：一条命令完成 打包 → 发布全局规则 → 发布 skill 目录 → 刷新看板；`--check` 只体检不写入
- [修订] `pack.py`：同版本已存在改为跳过（不再中断后续 skill）；vendor 引入 skill frontmatter 不规范时跳过而非报错
- [框架] 看板重构为单屏概览：KPI 条（同步率/加工率/待处理数）+ Skill 构建×发布矩阵 + 全局规则内联徽章 + 原料进度 + 「待处理」清单；砍掉会无限增长的加工历史时间线，细节回 CHANGELOG 查
- 4 个共享 skill 首次打包入 dist/

## 2026-07-23 — 纳管 ~/.agents/skills 共享 skill 池

- [新增] 4 个自有 skill 入库（以 ~/.agents/skills 版本为准，补齐 version 1.0.0）：`grsai-image-gen`（Grsai 付费图像 API）、`init-project`（项目 AGENTS.md 初始化）、`scope-guard`（语义失败捕获，流水线运行时采集器）、`vps-server-info`（VPS 连接信息）
- [修订] `vps-server-info` 分叉合并：~/.claude/skills 旧副本（77 行，visionguard 别名）已被 ~/.agents 新版（148 行，xgwnje 别名 + 2026-05-25 核验记录）覆盖，旧版备份于 backups/
- [框架] `security-review`（origin: ECC）物理引入 vendor/；`skill-creator`（anthropics/skills git clone）仅登记来源不入库；~/.claude/skills 大池约 30 个 skill 暂不计入管理——均见 vendor/SOURCES.md
- [框架] 新增 `scripts/publish_skills.py`：skills/ 目录镜像发布到 ~/.agents/skills/（+ Claude 池 vps 副本），--check 查漂移，覆盖前自动备份
- [框架] 看板新增「Skill 发布同步」区块

## 2026-07-23 — 全局规则多目标发布 + 看板

- [框架] 新增 `scripts/publish_global.py`：核心规则发布到 4 个位置（~/AGENTS.md、Codex、OpenCode、Claude Code）；Claude 目标拼接 `global/overlays/claude.md`（迁移自原 ~/.claude/CLAUDE.md 的专属内容，原规则零丢失）；`--check` 检查漂移，覆盖前自动备份；Kimi Code 无全局注入机制，确认为非发布目标
- [框架] 新增 `scripts/dashboard.py` + `dashboard.html`：单文件看板，扫描仓库自动生成——skill 清单与溯源、全局规则发布同步状态、笔记加工进度、加工历史；不维护自有状态

## 2026-07-23 — 全局规则纳入管理

- [框架] 新增 `global/AGENTS.md`：全局协作规则纳入仓库流水线，源文件在仓库维护，`~/AGENTS.md` 变为发布产物（单向加工）
- [修订] 全局规则整理为 v1.1.0：新增「全局 / 项目的边界」一节置顶（全局放跨项目通用规则，项目放仓库特有约束，一处事实只在一处维护）；原「文档边界」节精简为「文档维护」，去除重复条目；文件头加管理来源与版本标注
- 边界管理（哪些规则归全局、哪些归项目、何时上浮）后续视积累情况提炼为独立 skill

## 2026-07-23 — 首批规则提炼

- [新增] `ai-coding-workflow` v1.0.0：AI 编程工作流 Harness，6 条规则全部提炼自 notes/2026-07-vibe-coding-观察.md（Token≠产出、榜单不可信、双模型交叉验证、诚实失败、生成≠知识、Harness>Loop）
- [修订] `ai-stack-harness` v1.0.0 → v1.1.0：通用警示新增「封装层优先诚实失败」一条，速查区补交叉引用
- notes/2026-07-vibe-coding-观察.md 全部条目标注提炼去向，原料加工完毕

## 2026-07-23 — 框架完善

- [框架] 引入的第三方 skill 从 `skills/` 移入 `vendor/`，与自有 skill 物理分离；上游更新时整目录替换
- [框架] 确立规则生命周期约定：CHANGELOG 条目标注 新增/修订/废止；失效规则改写为废止块保留失败原因，不直接删除
- [框架] 确立规则溯源约定：规则标注来源笔记，便于废止与换代清理时回溯场景
- [框架] notes/ 增加最低结构要求：日期 + 场景两行元信息
- [框架] 新增 `scripts/pack.py` 打包脚本：读取 SKILL.md 版本号输出 `dist/<name>-<version>.skill`，同版本重复打包报错（强制版本 +1）

## 2026-07-23 — 仓库初始化

- 建立三层流水线结构：notes（原料）→ 仓库（加工）→ skills（生产）
- 新增自有 skill：`ai-stack-harness` v1.0.0（提炼自 lencx《编程心得：Vibe 上百亿 Token 后，我收获了什么？》，核心：选型看反馈闭环而非生成能力；Rust + TS + React/Tailwind + Electron 分层栈；Tauri 与自编译 Chromium 反面清单；长链路任务证据链收敛法）
- 引入第三方 skill：`keel` v1.0.0、`coding-protocol` v1.1.0（来源 github.com/lencx/skills，原样未改）
- 首批原料入库：notes/2026-07-vibe-coding-观察.md
