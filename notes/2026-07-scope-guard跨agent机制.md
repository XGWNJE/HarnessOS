# 原料笔记：scope-guard 的跨 Agent 适用性（2026-07-24）

> 日期：2026-07-24
> 场景：scope-guard、codex hooks、跨工具 skill 机制

## 坑 + 判断 + 结果

- 以为 skill 发布到 3 个池就"到处可用"了，实际 scope-guard 只在 Codex 真正生效：它依赖 hooks 注入触发标记 + `~/.codex/scope-guard/app/` 的命令程序，SKILL.md 只是规程说明书。→ 教训：**带运行时机制的 skill（hooks/命令/状态目录）≠ 纯文档 skill，发布目录只解决了后者**。
- 同类还有隐忧：skill 里写死了 Codex 路径（`py -3 "...\.codex\scope-guard\..."`），即使在 Claude Code 里被触发也会调错位置。
- 待验证：Claude Code 支持 hooks，理论上可复用同一 state dir 扩展——下次在 Claude 里实际装一次再下结论。

## 待观察

- 若扩展成功，提炼规则："skill 分两类——纯规程类（目录发布即可）与机制类（需同步安装 hooks/命令），机制类在发布映射里要登记安装步骤"。
