# 原料笔记：Kimi WebBridge 验收流程（2026-07-24）

> 日期：2026-07-24
> 场景：kimi 环境、工具验收、WebBridge 浏览器控制
> 类型：混合（验收六步法为声明式规则，坑 1-3 为归纳式）

## 验收规则（实测通过版）

在 Kimi 环境中验收 WebBridge 可用性，按以下顺序逐项验证，全部通过才算可用：

1. **守护进程连通**：`curl.exe -X POST http://127.0.0.1:10086/command` 能返回 `{"ok":true,...}`；连接拒绝则先启动 `~/.kimi-webbridge/bin/kimi-webbridge.exe start`，不要问用户。
2. **navigate**：打开 example.com，确认返回 tabId，标签进会话分组。
3. **snapshot**：能读出页面标题、正文和带 `@e` 引用的链接。
4. **evaluate**：JS 能取回 document.title / h1 / 链接 href。
5. **screenshot**：截图落盘后用 ReadMediaFile **目检内容**，不只看返回码。
6. **list_tabs**：会话标签列表正确。

## 坑 + 当时判断 + 实际结果

- **坑 1：Windows 下中文请求体会被 shell 腐蚀成 `?`**。判断：所有请求写 JSON 文件再 `curl.exe --data-binary "@file"`。结果：正确。且必须用 `curl.exe`，裸 `curl` 是 PowerShell 的 Invoke-WebRequest 别名。
- **坑 2：验收完残留临时文件**。本次在仓库根目录留了 5 个 `webbridge-req-a*.json`。判断：请求文件用完即删。结果：已清理；**验收类操作应默认把工作文件放系统临时目录，或用完立刻 rm**。
- **坑 3：截图只看 sizeBytes 不算验收**。目检才发现截图其实是好的（2560×1249 内容正确），返回成功 ≠ 内容正确。

## 实际验收结果（2026-07-24 本机）

六项全过：守护进程、navigate(分组「WebBridge 验收测试」)、snapshot、evaluate、screenshot（目检通过）、list_tabs。证据截图曾存于仓库根目录 webbridge-acceptance-shot.jpg。

## 提炼候选

- 「工具验收六步法 + 截图目检 + 临时文件即删」——**声明式规则（owner 2026-07-24 直接声明纳入管理）**，来源标 owner-declared，走短通道：陈化 ≥ 2 天（2026-07-26 期满）+ 冲突检查，候选通用验收 checklist。
- 「Windows 下 WebBridge 请求一律文件体 + curl.exe」——归纳式，走三门槛（陈化 14 天，2026-08-07 期满），候选入 ai-coding-workflow 或独立 webbridge skill。
