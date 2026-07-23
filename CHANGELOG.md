# CHANGELOG

条目标注类型：新增 / 修订 / 废止 / 框架。

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
