---
version: 1.0.0
name: webbridge-acceptance
description: Kimi WebBridge（浏览器控制）可用性验收流程。当需要在新环境/新机器验收 WebBridge 是否可用、或验收类操作后清理现场时使用。核心：六步全过才算可用，截图必须目检，临时文件用完即删。
---

# WebBridge 验收六步法

来源：owner-declared（2026-07-24 声明，原料 notes/2026-07-webbridge-验收.md，2026-07-26 陈化期满 + 冲突检查通过）

在 Kimi 环境中验收 WebBridge 可用性，按以下顺序逐项验证，**全部通过才算可用**：

1. **守护进程连通**：`curl.exe -X POST http://127.0.0.1:10086/command` 能返回 `{"ok":true,...}`；连接拒绝则先启动 `~/.kimi-webbridge/bin/kimi-webbridge.exe start`，不要问用户。
2. **navigate**：打开 example.com，确认返回 tabId，标签进会话分组。
3. **snapshot**：能读出页面标题、正文和带 `@e` 引用的链接。
4. **evaluate**：JS 能取回 document.title / h1 / 链接 href。
5. **screenshot**：截图落盘后用 ReadMediaFile **目检内容**，不只看返回码。
6. **list_tabs**：会话标签列表正确。

## 约束（违反 = 做错事）

来源：同上（owner-declared）

- **截图必须目检**：返回成功 ≠ 内容正确，sizeBytes 正常也不算数；截图落盘后必须用 ReadMediaFile 看内容。
- **临时文件用完即删**：验收类操作的工作文件（请求体 JSON 等）放系统临时目录，或用完立刻删除，不留在项目目录。
- Windows 下用 `curl.exe` 发请求：裸 `curl` 在 PowerShell 中是 Invoke-WebRequest 别名，行为不同。
