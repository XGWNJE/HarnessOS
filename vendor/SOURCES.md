# 引入 Skill 来源清单

本文件记录第三方 Skill 的引入来源与本地差异。可静态拷贝的 Skill 存放在 `vendor/`；体积大、自带 Git 或由宿主应用自动维护的来源可以只登记、不复制。默认保留上游原样；本地补丁只有在用户明确授权并按[项目规则](../AGENTS.md#源与边界)登记后才允许存在。

## 物理引入

| Skill | 来源 | 引入时间 | 说明 |
|---|---|---|---|
| vibehub | https://github.com/oil-oil/vibe-hub-skill （skills/vibehub 目录 + LICENSE） | 2026-07-24 | 当前受管提交 8d77154（2026-09-10），2026-09-12 核验；Vibe Coding 术语学习助手，依赖 VibeHub 网站知识源 |
| archify | https://github.com/tt-a1i/archify （archify/ 目录 + LICENSE，MIT，SKILL metadata v2.17） | 2026-08-28 | 当前受管提交 c1443b3（2026-09-11），2026-09-12 核验；架构、流程、时序、数据流和生命周期图的本地渲染与校验。迁移须保留完整目录、THIRD_PARTY_NOTICES.md 与字体许可；需 Node.js >=18，核心渲染不需安装 node_modules，视觉检查另需 Chrome/Chromium |
| quarkclouddrive | 夸克网盘（Quark Drive）官方 Skill；非 git 来源，从部署副本回收；通过 `@ali/qkop-*` SDK 操作网盘 | 2026-09-02 | 当前受管版本 1.0.20-5be3987，2026-09-13 核验；上传/下载、分享与转存、搜索、批量重命名与撤销、相册整理、AI 助手。需 Node.js，`scripts/install.sh` 安装 CLI |

本文件当前没有登记本地补丁；若以后出现补丁，在本节对应行记录上游提交、原因、差异范围、验证结果以及移除或重放条件，并明确标为补丁版。

## 核对上游更新

用户要求检查或更新时，以 `vibehub` 为例：

1. 从[上游仓库](https://github.com/oil-oil/vibe-hub-skill)取指定提交，核对 `skills/vibehub/`（含许可证及运行依赖）与 `vendor/vibehub/`。
2. 没有本地补丁时，若上游有变化则整目录替换，在本文件更新当前上游提交、版本及核验日期，并运行 `python scripts/sync.py` 发布；无变化则报告当前副本对应的上游提交。
3. 有本地补丁时，先检查上游是否已吸收补丁；已吸收则替换目录并移除补丁记录，未吸收则基于新上游重新验证并重放补丁，同步更新本文件。不得用上游更新覆盖本地差异。

## 仅登记来源（不拷贝实体）

| Skill | 来源 | 登记时间 | 说明 |
|---|---|---|---|
| ego-browser | [Citro Labs 官方仓库](https://github.com/citrolabs/ego-lite/tree/d392204d1ea1a8027a591ab2b0129c2e11d85f26/skills/ego-browser)（MIT） | 2026-10-22 | Skill 2.1.0，22 个文件与该上游提交一致。由 Ego（lite）首次设置安装并维护目录链接，随应用更新；HarnessOS 不复制或发布。恢复时先安装 Ego、完成首次设置并重开 Agent，再运行 `ego-browser skill`。 |

## 不受管的池内技能（2026-09-13 确认）

以下技能在 2026-09-13 经 owner 明确确认不属于其管理范围，因此不登记、不纳入发布与对账；再次核对时不要据此重新登记：

| Skill | 位置 | 说明 |
|---|---|---|
| playwright | `~/.codex/skills/playwright` | 无顶层 `SKILL.md`（仅 agents/assets/references/scripts），不参与本仓库 skill 扫描与发布 |
| skill-creator | `~/.agents/skills/skill-creator` | Anthropic 官方仓库内容，当前不是 git 工作树，`SKILL.md` 位于下一层 `skills/<name>/`，不由本仓库维护 |

池内副本是否一致以 `python scripts/sync.py --check` 的本次结果为准；该检查不代表整机技能盘点，也不自动纳管池内其他来源。
