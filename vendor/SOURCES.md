# 引入 Skill 来源清单

本文件记录第三方 Skill 的引入来源与本地差异。可静态拷贝的 Skill 存放在 `vendor/`；体积大或自带 Git 的来源可以只登记、不复制。默认保留上游原样；本地补丁只有在用户明确授权并按[项目规则](../AGENTS.md#源与边界)登记后才允许存在。

## 物理引入

| Skill | 来源 | 引入时间 | 说明 |
|---|---|---|---|
| vibehub | https://github.com/oil-oil/vibe-hub-skill （skills/vibehub 目录 + LICENSE） | 2026-07-24 | Vibe Coding 术语学习助手（面向普通人的教学流程，依赖 VibeHub 网站知识源）；2026-09-12 整目录更新至上游 8d77154（2026-09-10），上游重构后 SKILL.md 不再引用 references/ 与 assets/，旧目录随之移除 |
| archify | https://github.com/tt-a1i/archify （archify/ 目录 + LICENSE，MIT，SKILL metadata v2.17） | 2026-08-28 | 架构、流程、时序、数据流和生命周期图的本地渲染与校验技能；从 Codex 试点安装副本原样回收。迁移时保留完整目录，目标需 Node.js >=18；核心渲染不需安装 node_modules，视觉检查另需本机 Chrome/Chromium。2026-09-12 整目录更新至上游 c1443b3（2026-09-11，metadata 2.16 → 2.17），随上游新增 THIRD_PARTY_NOTICES.md 与 JetBrains Mono 字体许可 |
| quarkclouddrive | 夸克网盘（Quark Drive）官方 Skill，版本 1.0.20-5be3987；经夸克开放平台 API（`@ali/qkop-*` SDK）操作网盘；非 git 仓库，预编译 minified 包（约 796KB），从已部署的 skill 目录（`~/.agents/skills` 等）回收 | 2026-09-02 | 夸克网盘文件操作：上传/下载（断点续传）、分享与转存、搜索、相册整理、AI 助手（文件总结与知识问答，支持万级文件）。运行依赖 Node.js（`scripts/install.sh` 装 CLI）。2026-09-13 整目录更新至上游 1.0.20-5be3987（引入时 1.0.15）：新增 `references/file-rename.md`（批量重命名与整批撤销），`file-saveas`、`file-share`、`file-ops` 文档扩充，`SKILL.md` 与 CLI 包同步更新；该技能无本地补丁，故只做整目录替换 |

本文件当前没有登记本地补丁；若以后出现补丁，在本节对应行记录上游提交、原因、差异范围、验证结果以及移除或重放条件，并明确标为补丁版。

## 核对上游更新

用户要求检查或更新时，以 `vibehub` 为例：

1. 从[上游仓库](https://github.com/oil-oil/vibe-hub-skill)取指定提交，核对 `skills/vibehub/`（含许可证及运行依赖）与 `vendor/vibehub/`。
2. 没有本地补丁时，若上游有变化则整目录替换，在 `CHANGELOG.md` 记录上游提交和修订，并运行 `python scripts/sync.py` 发布；无变化则报告当前副本对应的上游提交。
3. 有本地补丁时，先检查上游是否已吸收补丁；已吸收则替换目录并移除补丁记录，未吸收则基于新上游重新验证并重放补丁，同步更新本文件。不得用上游更新覆盖本地差异。

## 仅登记来源（不拷贝实体）

当前无此类登记。`skill-creator` 曾登记于此，2026-09-13 经 owner 确认不属于其管理的技能，撤销登记。

## 不受管的池内技能（2026-09-13 确认）

以下技能在 2026-09-13 经 owner 明确确认不属于其管理范围，因此不登记、不纳入发布与对账；再次核对时不要据此重新登记：

| Skill | 位置 | 说明 |
|---|---|---|
| playwright | `~/.codex/skills/playwright` | 无顶层 `SKILL.md`（仅 agents/assets/references/scripts），不参与本仓库 skill 扫描与发布 |
| skill-creator | `~/.agents/skills/skill-creator` | Anthropic 官方仓库内容，当前不是 git 工作树，`SKILL.md` 位于下一层 `skills/<name>/`，不由本仓库维护 |

## 历史池对账（2026-09-13）

2026-09-13 复核时，`~/.claude/skills` 中 9 个技能均为 HarnessOS 发布产物。这是当日的对账结果；以后仅在用户要求对账时重新核验实际池内容，先查上节排除名单，再处理新来源。
