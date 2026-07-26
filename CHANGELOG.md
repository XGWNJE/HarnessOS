# CHANGELOG

条目标注类型：新增 / 修订 / 废止 / 框架。

## 2026-07-26 — 框架评定落地：全局规则减半、闲机器拆除、冷冻期与行为验证环

- [框架] 背景：owner 发起最终框架评定（原料 5 篇 171 行 vs 机器 914 行脚本+hook，框架/原料比失衡；建仓 4 天 6 次框架决策、3 次 48 小时内反转），五项改动由 owner 一句「执行」验收通过。本批次为冷冻期前最后一批框架变更
- [修订] `global/AGENTS.md` v1.8.0 → v1.9.0：协作目标 14 条 → 8 条，裁撤依据 = 失效测试反向应用（这条不在，模型真的会做错吗）。裁撤：「中文环境无乱码」「视觉资产一致」（场景触发非常驻级，模型基线已覆盖）；「工具链精简可逆」（上下文经济性由规则减量本身达成）；「自动化验证可视」（按归属判断只对特定项目成立，应迁入对应项目 AGENTS.md 而非 global）；「拿来主义」并入「投入产出匹配」；「事实可核验」与「交付真实」合并为「事实与交付皆可核验」。被裁条目如 owner 认为误判可一句话恢复
- [修订] `harness-observer` v1.2.0 → v1.3.0：拆除双门槛废止后的闲机器——重复计数从「支撑归纳门槛」降级为「owner 验收参考权重」；`提议` 类型更名 `待确认`（陈化期已废止，两者实际差别只是 owner 是否确认过）；归纳式原料描述删除「走三门槛」话术
- [框架] 框架冷冻期（owner-declared）：2026-07-26 起 14 天（至 2026-08-09）不做框架类变更（新增机制/改流程/立术语），只加原料、修 bug、验收规则条目；owner 可一句话豁免。写入项目 AGENTS.md 工作规则
- [框架] 行为验证环：规则/skill 固化时附一条可观测场景，评审时抽查最近会话日志对照「规则是否改变了 Agent 行为」；验不出行为差异的规则进入退役候选。此前全部验证都是发布体检（验文件对不对），无行为层验证。写入 README 评审流程（新增第 4 步）与月度评审（三问→四问）
- [修订] README：修「运行时适配块」漂移（该机制 07-26 已废止，实为「静默观察」固定块，init-project v1.4.0 起）——文档偏移的活标本；项目 AGENTS.md 文档地图删「双门槛」过时说法；「提议」相关措辞同步为「待确认」

## 2026-07-26 — 新机制首次验收：2 条合入 global、1 条 hook 承载闭环、1 条待定

- [框架] 处理原则（owner 2026-07-26 确认）：已由 hook 承载的规则不再转化为文字规则——机制已强制达成目标，文字版属同一事实两处维护；扩大覆盖 = 复制 hook 机制到其他仓库，而非把规则写进 global
- [修订] `global/AGENTS.md` v1.7.0 → v1.8.0：新增两条协作目标——「自动化验证可视」（owner 验收通过，owner-declared，原料 notes/2026-07-26-自动化验证预览窗口.md；冲突检查通过：global 与各 skill 无预览窗口相关条目）与「工具链精简可逆」（owner 验收通过，owner-declared，原料 notes/inbox/2026-07-26.md 工具偏好条目）
- [框架] 「文档偏移纠正时机分层」验收闭环：硬卡点已由 `hooks/pre-commit` 承载，不转规则；软时机（顺手改/落字记录）为边际效率优化，随 hook 兜底自然覆盖，不单独固化
- 待定：「Windows 下 WebBridge 一律文件体 + curl.exe」（owner 标待定，暂不合入，原料留在 notes/2026-07-webbridge-验收.md）

## 2026-07-26 — 废止双门槛陈化期：静态验证 + owner 验收

- [废止] 规则固化的「双门槛」机制废止（owner 2026-07-26 决策）：声明式的「陈化 ≥ 2 天」与归纳式的「重复 ≥ 2 次 + 陈化 ≥ 14 天 + 实战验证」全部取消。新机制：只保留基础静态验证（冲突检查，冲突由 owner 裁决），最终决定权归 owner 验收——owner 明确说某条可验收通过，即直接固化。历史条目中的陈化记录保留当时说法不回改
- [框架] 同步改写：项目 AGENTS.md 铁律 #2；README 加工段（「双门槛 + 一道分界」→「静态验证 + owner 验收 + 一道分界」）、一句话口号（删「耐得住陈化」）、喂料方式 2、评审条目；`global/AGENTS.md` v1.6.0 → v1.7.0 术语段（两类规则统一通道：冲突检查 + owner 验收）
- 影响在途条目：「文档偏移纠正时机分层」（原陈化截止 2026-07-27）与「自动化验证预览窗口」（原陈化截止 2026-07-28）不再受期限约束，随时可由 owner 一句话验收合入

## 2026-07-26 — hook 统一管理：公共源归位 + 全机登记表 + 体检进 sync

- [框架] 背景与事实：kimi-code 无默认 hook 加载目录、无项目级配置，`[[hooks]]` 注册是唯一加载通道（官方文档确认）；此前公共适配器 kimi-codex-hook-adapter.py 躺在 `~/.kimi-code/hooks/` 无源管理，项目私有 hook（Server-infra / Codex-Journal）与各运行时注册点（kimi config.toml、codex hooks.json）无统一视图
- [框架] 公共源归位：adapter 源迁入 `global/hooks/`，config.toml 6 处引用改直引仓库源（与 observer_reminder 同一模式：直引、无拷贝、改源即生效）；`~/.kimi-code/hooks/` 空目录已清理——「公共位」从用户目录约定转为 HarnessOS 源目录
- [新增] `global/hooks/registry.json`：全机 hook 登记单一事实源（kimi 7 条 + codex 5 条，含属主与 matcher；claude 无 hook）；新增/改/删 hook 的流程 = 先改登记表 → 再改注册点 → `sync.py --check` 验证
- [新增] `scripts/check_hooks.py`：对照登记表体检注册点与源文件（只读不写，注册点含活配置不做自动覆盖，漂移手工修复），已并入 `sync.py` 两种模式；负向测试通过（篡改 matcher 检出漂移 exit 1，还原 exit 0）

## 2026-07-26 — observer 通道二次断点修复：项目内嵌观察块 + kimi-code 收口 hook 保底

- [框架] 背景：observer 在 Vigil 会话再次漏捕工具链变更——wire 时间线证实全部落盘发生在 owner 提醒之后（前 5 个 turn 零观察）；2026-07-25 的「运行时适配指针」对策未铺到任何存量项目，owner 判定「引导整体读全局文件」上下文成本不可接受，指针方案废止。原料：notes/inbox/2026-07-25.md 通道断点条目（重复计数 1→2）+ 2026-07-26 工具偏好条目
- [修订] `init-project` v1.3.0 → v1.4.0：「运行时适配」固定块（读全局指针）替换为「静默观察」固定块——项目 AGENTS.md 开头直接内嵌 harness-observer 常驻职责（目标模式，约 10 行），不再引导读全局文件；有全局注入的运行时仍跳过
- [新增] kimi-code `UserPromptSubmit` 收口 hook 保底：`global/hooks/observer_reminder.py`——matcher 命中收口关键词（收口/可以 push/提交吧/差不多了）时向上下文注入观察提醒，纯提醒不拦截；config.toml 直引仓库源路径、无发布拷贝、改源即生效（已注册）；与项目内嵌块互补（块管常驻在场，hook 管收口兜底）
- [框架] 内嵌块全量铺开：16 个存量项目 AGENTS.md 补齐「静默观察」固定块（此前仅 HarnessOS 自身有旧指针块，已同步替换）；README 与项目 AGENTS.md 登记 `global/hooks/` 目录约定
- 实施插曲（留档）：批量铺块脚本中 `\n` 转义被 Python 解释为换行，16 个项目文件路径断行，同批次脚本修复并全量校验通过——教训：生成含 Windows 路径的批量内容，写入后必须逐文件校验产物

## 2026-07-26 — 方向转型：全部自有生成物改目标模式（hook 豁免）

- [框架] owner 决策（2026-07-26，原料 notes/inbox/2026-07-26.md）：前沿模型原生能力持续吸收 skill 能力、规则内化增强，过多规定性 skill 与规则可能起反效果——全部自有生成物改**目标模式**：只描述目标与验收标准，不规定做法，做法由模型按情境自决。hook 是硬控制，豁免；vendor/ 按铁律原样不改，不在范围。同日拍板两个设计点：红线类约束全部目标化、转成可检验的验收标准；9 处自有生成物直接全量迁移
- [修订] 全局规则 v1.5.0 → v1.6.0：目标模式改写——11 条协作目标均带验收标准；文件头标注写法；全局/项目边界与规则体系术语作为框架事实保留
- [修订] claude overlay：目标模式改写（8 条目标含验收；sing-box DNS 顺序作为红线验收保留）
- [修订] `ai-coding-workflow` v1.1.0 → v1.2.0：9 条红线转验收，事实与来源标注保留
- [修订] `ai-stack-harness` v1.2.0 → v1.3.0：7 步选型流程转评估维度验收；证据链回路作为机制保留
- [修订] `grsai-image-gen` v1.0.0 → v1.1.0：12 条红线转验收；异步调用模板与价格/兼容性事实作为机制与事实保留
- [修订] `harness-observer` v1.1.1 → v1.2.0：静默纪律等 12 条红线转验收；落盘路径/查重数据源/记录格式作为机制保留
- [修订] `init-project` v1.2.0 → v1.3.0：六步流程转 9 条验收；运行时适配固定块原文保留（指针机制）
- [修订] `vps-server-info` v1.1.1 → v1.2.0：嵌入事实段的 6 条指令转 5 条验收；服务器事实全部原样
- [修订] `webbridge-acceptance` v1.0.0 → v1.1.0：六步流程转六项能力验收（删顺序规定）；截图目检/现场无残留红线转验收
- README 失效测试表加 hook 列与目标模式约定；项目 AGENTS.md 工作规则登记写法约定

## 2026-07-26 — hook 流水线试点：pre-commit 体检硬卡点

- [框架] 「文档偏移纠正时机分层」声明式规则登记并进入机制试点（原料 notes/inbox/2026-07-25.md，owner 2026-07-25 声明，2026-07-27 陈化期满 + 冲突检查已预先通过，候选去向 global/AGENTS.md）：硬卡点 = commit/push 前全量清零文档偏移；软时机 = 手边顺手改、不在手边先落字记录
- [框架] hook 流水线首个试点落地：新增 `hooks/pre-commit`——commit 前提醒文档偏移清零并跑 `sync.py --check`，漂移退出码 1 拦截提交；安装方式 `git config core.hooksPath hooks`（单点安装、源目录即生效点，免登记多处）。试点目的：验证「机制强制层」形态，跑过实战后再决定是否升格为规则/skill 之外的第三类产物
- 试点首问题（已修复）：hook 环境不继承终端 UTF-8 设置，Windows 下 sync 输出按 GBK 乱码——hook 内显式 `export PYTHONUTF8=1 PYTHONIOENCODING=utf-8`
- 验证闭环：干净状态 exit=0 → 临时制造 skill 源漂移 exit=1 拦截 → 恢复后 exit=0（已还原临时改动）；README 与项目 AGENTS.md 同步登记 hooks/ 目录约定

## 2026-07-26 — webbridge 声明式条目提炼 + 两篇笔记销毁

- [框架] 提炼流程补「归属判断」：约束规则提炼时区分全局与项目特有——换个项目还有意义 → global 或 skill 约束段；只对特定项目成立 → 写入该项目 AGENTS.md（标注来源与日期），不进 global。写入 README「评审与提炼」与项目 AGENTS.md 工作规则（owner 2026-07-26 确认）

- [框架] 新声明式规则登记：`notes/2026-07-26-自动化验证预览窗口.md`——自动化验证（ADB / 虚拟机调试安卓项目）默认打开预览窗口、调试结束关闭（owner 2026-07-26 声明，2026-07-28 陈化期满 + 冲突检查后合入，候选去向 global/AGENTS.md 约束规则）

- [新增] `webbridge-acceptance` v1.0.0：WebBridge 验收六步法（技能）+ 约束段（截图必须目检、临时文件用完即删、Windows 用 curl.exe），来源 owner-declared（原料 notes/2026-07-webbridge-验收.md，2026-07-26 陈化期满，冲突检查通过——skills 与 global 无同类条目）。该笔记的归纳式条目「Windows 下一律文件体 + curl.exe」未到期（08-07，缺重复次数），留在原笔记继续陈化
- [框架] owner 指示销毁两篇笔记：`notes/2026-07-kimi-code-skill加载验证.md`（事实记录，全量实测欠账一并作废）、`notes/2026-07-vibe-coding-观察.md`（已全部提炼完毕）。注意：ai-coding-workflow 与 ai-stack-harness 中「来源：notes/2026-07-vibe-coding-观察.md」标注此后指向已销毁文件，溯源链断——换代清理时按「无来源标注」规则优先检查这些条目

## 2026-07-25 — 取消定时评审 + 清除退役 VPS 记录

- [框架] 取消每周日 21:12 定时评审：owner 几乎每天主动质检，定时评审属冗余；评审改为按需（owner 主动发起），observer 复述时机从「主动自检 + 每周评审」收窄为「仅 owner 主动自检」。README、项目 AGENTS.md 同步更新
- [修订] `harness-observer` v1.1.0 → v1.1.1：复述时机收窄（见上）
- [修订] `vps-server-info` v1.1.0 → v1.1.1：删除旧数据中心 VPS（66.154.112.91）记录——该机已停用，owner 指示清除全部相关记录；reviews/2026-07-24 归档中对应遗留事项一并移除。Server-infra/CURRENT.md 无该机记录，无需处理
- 排查确认：Windows 任务计划程序与本会话 cron 中均未找到该定时任务的实体；如曾在其他工具/会话中创建，需 owner 在该处取消

## 2026-07-25 — observer 断点修复：项目级运行时适配

- [修订] `init-project` v1.1.0 → v1.2.0：新增「运行时适配」固定块——按 Agent 全局规则注入能力区分：Claude Code / Codex / OpenCode 自动注入全局规则，跳过；Kimi Code 无全局注入机制（~/AGENTS.md 不被加载），由项目级 AGENTS.md 开头固定块引导其先读全局规则文件，harness-observer 常驻指引随之生效。块为指针非副本，不违反「一处事实只在一处维护」
- 原料：notes/inbox/2026-07-25.md（observer 上线一天零产出 → 排查出 Kimi 无全局注入 + skill 正文懒加载两个断点，owner 质检发现）

## 2026-07-24 — 声明式规则入口（短通道）

- [复审改造] 按新理念复审全部资产并改造：
  - [废止] `scope-guard`：职责与 harness-observer 重叠（同为静默观察记录），按 owner 决定统一整合进 harness-observer，源目录移入 archive/skills/，已撤出三个读取池；运行时钩子目录 `~/.codex/scope-guard/` 及 hooks.json 中 4 处注册（PostToolUse/SessionStart/SubagentStart/SubagentStop）已一并清除；归档可复活
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
