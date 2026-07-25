# 原料笔记：scope-guard 的跨 Agent 适用性（2026-07-24）

> 日期：2026-07-24
> 场景：scope-guard、codex hooks、跨工具 skill 机制

## 坑 + 判断 + 结果

- 以为 skill 发布到 3 个池就"到处可用"了，实际 scope-guard 只在 Codex 真正生效：它依赖 hooks 注入触发标记 + `~/.codex/scope-guard/app/` 的命令程序，SKILL.md 只是规程说明书。→ 教训：**带运行时机制的 skill（hooks/命令/状态目录）≠ 纯文档 skill，发布目录只解决了后者**。
- 同类还有隐忧：skill 里写死了 Codex 路径（`py -3 "...\.codex\scope-guard\..."`），即使在 Claude Code 里被触发也会调错位置。
- 待验证：Claude Code 支持 hooks，理论上可复用同一 state dir 扩展——下次在 Claude 里实际装一次再下结论。

## 待观察

- 若扩展成功，提炼规则："skill 分两类——纯规程类（目录发布即可）与机制类（需同步安装 hooks/命令），机制类在发布映射里要登记安装步骤"。

## 补充：hook 安装/卸载的清理完整性（2026-07-24 晚）

- 事故：scope-guard 卸载后，Kimi Code 提交任何提示词都被 `UserPromptSubmit hook blocked` 拦死，重启电脑无效。
- 根因：卸载程序只清理了 `~/.codex/`（hooks.json、AGENTS.md、skill、运行时目录），但 Kimi Code 有自己**独立的钩子配置** `~/.kimi-code/config.toml`（`[[hooks]]` 表），里面残留 5 条指向已删除 `scope_guard_hook.py` 的条目。卸载脚本根本不知道这份配置的存在。
- 排查教训：报 "hook blocked" 时，**先确定是哪个 runtime 拦的，再找它自己的钩子配置**，别只看 Codex 的 hooks.json。同一台机器上 hook 配置至少有三处：`~/.codex/hooks.json`、`~/.kimi-code/config.toml`、各项目的 `.claude` 配置——安装/卸载必须全量登记、全量清理。
- 修复动作（已验证）：从 `~/.kimi-code/config.toml` 删除 5 条残留（备份 `config.toml.backup-scope-guard-removal-20260724`），保留 server-infra / codex-journal 钩子；验证 TOML 可解析、引用文件全存在、按 Kimi Code 调用方式模拟运行钩子 exit=0 放行。
- 沉淀规则（给 scope-guard  reinstall 时用）：
  1. **安装登记表**：install.py 每写一处配置就记录到清单（文件路径 + 条目标记），uninstall 按清单逐项回滚，不允许"只管自己知道的运行时"。
  2. **卸载自检**：卸载后扫描各 runtime 配置中是否还残留指向已删路径的命令（grep `scope_guard_hook` / `scope-guard\app`），有残留则报错而非静默成功。
  3. **验证闭环**：卸载后必须模拟一次真实 hook 调用（构造 hook event JSON 走一遍 adapter），确认 exit=0，而不是只看配置文件干净了。
