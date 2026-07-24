# CHANGELOG

条目标注类型：新增 / 修订 / 废止 / 框架。

## 2026-07-24 — 声明式规则入口（短通道）

- [复审改造] 按新理念复审全部资产并改造：
  - [废止] `scope-guard`：职责与 harness-observer 重叠（同为静默观察记录），按 owner 决定统一整合进 harness-observer，源目录移入 archive/skills/，已撤出三个读取池；归档可复活
  - [新增] `harness-observer` v1.0.0 → v1.1.0：整合原 scope-guard 信号——Agent 自身语义失败（假设被违反/目标错误/路径错误/范围错误）记为归纳式原料，重复计数累计根因
  - [修订] `ai-stack-harness` v1.1.0 → v1.2.0：补齐全部来源标注（notes/2026-07-vibe-coding-观察.md 与 owner-declared）
  - [修订] `ai-coding-workflow` v1.0.0 → v1.1.0：description 标明「规则集合」性质（按失效测试分界，约束规则可驻留 skill 约束段）
  - [修订] 全局规则 v1.4.0 → v1.5.0：文件头声明规则性质为声明式（owner-declared），废止标准是 owner 改主意
  - [修订] `vps-server-info` v1.0.0 → v1.1.0：只读核验发现 VPS 已换新机（C20260629016451，1C/1G/20G），服务分工全面刷新：webhome→xgwnje-home、新增 api/m/mail/sub 站点、Uptime Kuma 与 Docker 已退役、VisionGuard 工作目录迁至 /opt/visionguard-server

- [新增] `harness-observer` v1.0.0：常驻静默观察 skill——在任何项目/任务中观察 owner 重复纠正（→提议）、明确偏好（→声明式）、可复用踩坑（→归纳式原料），静默追加到 notes/inbox/ 按日归档；静默纪律：不提及、不确认、不跑 git/sync；查重累加重复计数服务归纳式门槛；全局规则 v1.3.0 → v1.4.0 加常驻生效指引
- [修订] `publish_skills.py`：自有 skill 列表由硬编码改为自动扫描 skills/ 目录（本次新增 skill 漏发布即硬编码所致，属流程缺陷修复）

- [框架] 新增「提议态」：Agent 观察到 owner 重复纠正但未明说的规则，记 `> 类型：提议`；复述时机仅两个——owner 主动要求自检时、每周评审时；确认后转声明式（确认日起算 2 天陈化），否认则丢弃或留作归纳式原料；复述前不得固化
- [框架] 新增「规则与技能的分界」：失效测试——去掉它 Agent 会做错事 → 约束规则（global 或 skill 约束段），不会做某事 → 技能（skills/ 独立目录）；混合笔记提炼时拆开各走各路

- [修订] 全局规则 v1.2.0 → v1.3.0：新增「规则体系术语」——声明式规则（declared）与归纳式规则（induced）统一说法写入 global/AGENTS.md，所有 Agent 讨论规则体系时使用同一术语
- [修订] 术语精确化：白话「明说规则」→「声明式规则」，「经验型」→「归纳式」

- [框架] notes/ 新增「声明式规则」入口：owner 直接声明的意图型规则以 `> 类型：声明式规则` 标注；豁免「重复 2 次」门槛，陈化期缩短为 ≥ 2 天（防随口一说固化），合入前加做冲突检查（对照现有 skill 与 global，冲突由 owner 裁决）；来源标注 owner-declared，废止标准为「owner 是否改主意」而非「场景是否失效」
- 首条适用：notes/2026-07-webbridge-验收.md 中的「工具验收六步法」（owner 2026-07-24 明说），陈化 2026-07-26 期满

## 2026-07-24 — 提炼陈化期 + skill 生命周期管理

- [框架] 提炼门槛升级：notes 条目须同时满足 重复 2 次以上 + 陈化 ≥ 14 天 + 至少 1 次实战验证，才可固化为规则（防止冲动固化）
- [框架] 新增 skill 生命周期机制：月度评审三问（最近用过吗 / 被工具原生能力取代了吗 / 与其他 skill 或规则冲突吗）；退役流程 = 撤出全部发布点 + 源目录移入 archive/skills/ + CHANGELOG 记废止；归档可复活
- [框架] 看板新增「使用热度」列：扫描 ~/.claude/projects、~/.codex/sessions、~/.kimi/sessions 会话日志，统计每个 skill 的近似使用次数与最后使用时间；>90 天零使用进入「待处理」预警
- 首次扫描基线：scope-guard 966 次、vps-server-info 744 次、grsai-image-gen 54 次（均为日志出现近似值，含索引注入）；新建 3 个 skill 为 0（正常，刚创建）

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
