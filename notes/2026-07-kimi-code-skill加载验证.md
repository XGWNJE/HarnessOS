# 原料笔记：Kimi Code skill 读取机制验证（2026-07-24）

> 日期：2026-07-24
> 场景：kimi-cli 1.39.0、skill 发布通道验证、跨工具 skill 加载

## 事实记录

- Kimi Code CLI 官方文档：skill 分层 Project > User > Extra > Built-in；用户级品牌组 `~/.kimi/skills` → `~/.claude/skills` → `~/.codex/skills`，通用组 `~/.config/agents/skills` → `~/.agents/skills`；`merge_all_available_skills`（默认 true）控制品牌组是否合并全部存在目录。
- 本机配置 merge=false：品牌组互斥选一（本机实际命中 .claude），通用组不受影响。
- **验证结论**：2026-07-18 会话的 context.jsonl 系统提示词含 grsai-image-gen（当时仅在 ~/.agents/skills），证明通用组被加载，共享池发布对 Kimi Code 有效。→ 已提炼进 publish 通道设计（共享池覆盖 Kimi Code）。
- **不要在 merge=false 时创建 ~/.kimi/skills/**：品牌组互斥，它会顶掉 .claude 池导致丢失 30 个 Claude 池 skill 的加载。想让 Kimi 吃全部品牌池应改 merge=true。
- 新版 Kimi Code 数据根为 ~/.kimi-code（随 KIMI_CODE_HOME 移动）；本机仍是旧布局 ~/.kimi。

## 待办

- [ ] Kimi Code CLI 重新登录后（当前报 API 404，凭据疑似过期），跑新会话确认 6 个自有 skill 全部注入；若确认，本笔记可闭环。
