---
version: 1.2.0
name: webbridge-acceptance
description: Kimi WebBridge（浏览器控制）可用性验收。当需要在新环境/新机器验收 WebBridge 是否可用、或验收类操作后清理现场时使用。验收目标：守护进程连通、navigate、snapshot、evaluate、screenshot、list_tabs 六项全部实际通过才算可用；截图内容经过目检；临时文件不残留。
---

# WebBridge 验收目标与标准

来源：owner-declared（2026-07-24 声明，原料 notes/2026-07-webbridge-验收.md，2026-07-26 陈化期满 + 冲突检查通过）
写法：目标模式——只描述想要的目标与验收标准，不规定具体做法。

## 环境前提

此段仅声明事实，不规定 Agent 行为。

- **WebBridge 守护进程**已安装：二进制位于 `~/.kimi-webbridge/bin/kimi-webbridge.exe`（Windows）或等效位置。未安装时本 skill 不可用。
- **端口 10086 可用**：守护进程默认监听 `http://127.0.0.1:10086`。端口被占用或进程未启动时需先诊断再验收。
- **curl.exe 可用**（Windows 环境事实）：裸 `curl` 在 PowerShell 中是 `Invoke-WebRequest` 别名，行为不同——所有 HTTP 请求必须用 `curl.exe`。Linux/macOS 环境裸 `curl` 即为原生 curl，直接用。
- **ReadMediaFile 工具**可用（用于截图目检）。不可用时截图验收退化为人工判断。

## 目标

在 Kimi 环境中得出可信的 WebBridge 可用性结论：可用的每项能力都经过真实调用验证，结论不含"应该能用"式的推断；验收过程不在项目目录留下痕迹。

## 验收标准（全部通过才可判定"可用"）

- **守护进程连通**：`curl.exe -X POST http://127.0.0.1:10086/command` 返回 `{"ok":true,...}`。连接拒绝时，已先启动 `~/.kimi-webbridge/bin/kimi-webbridge.exe start` 再重试，而不是直接中断或问用户。
- **navigate 可用**：实际打开 example.com，返回 tabId，且标签进入会话分组。
- **snapshot 可用**：实际读出了页面标题、正文和带 `@e` 引用的链接。
- **evaluate 可用**：JS 实际取回了 document.title / h1 / 链接 href。
- **screenshot 可用且内容经目检**：截图落盘后，图像内容被实际查看确认（标题/页面主体与目标页一致）。返回成功、sizeBytes 正常均不算数——这两项不构成"内容正确"的证据。
- **list_tabs 可用**：会话标签列表与实际打开的标签一致。

## 验收红线（转成可检验标准）

来源：同上（owner-declared）

- **截图目检**：截图结论由图像内容本身支撑，而非由返回码或 sizeBytes 支撑。
- **现场无残留**：验收结束后，项目目录中不存在验收产生的工作文件（请求体 JSON 等）；临时文件在系统临时目录，或已被删除。

## 机制（事实，不是规定）

- Windows 下发请求用 `curl.exe` 而非裸 `curl`：裸 `curl` 在 PowerShell 中是 Invoke-WebRequest 别名，行为不同。这是环境事实，改别名行为前此结论不变。
- 查看截图内容用 ReadMediaFile：当前环境中它是唯一能把图像内容呈现给模型的读取手段，属机制而非流程规定；出现等效手段时可替代。

## 环境自检

本 skill 被触发后，在执行验收六项检查前，无声确认：

1. **守护进程存活**：检查端口 10086 是否在 listen——`curl.exe -s --max-time 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:10086/command`（Windows）或 `curl -s --max-time 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:10086/command`（Linux/macOS）。连接拒绝 → 尝试启动进程
2. **进程可启动**（上一步拒绝时）：`~/.kimi-webbridge/bin/kimi-webbridge.exe start`（Windows）或等效命令。启动后等 2 秒再回到第 1 步
3. **curl 路径正确**：`curl.exe --version`（Windows）或 `curl --version`（Linux/macOS）能输出版本号

自检通过 → 直接进入六项验收。
任一前提不满足 → 见下方「失效模式」。

## 失效模式

| 前提失败 | 降级行为 |
|---|---|
| 端口 10086 无进程，且 `kimi-webbridge.exe start` 执行失败（二进制不存在/启动报错） | 向 owner 报告："WebBridge 守护进程未运行且启动失败。请确认 WebBridge 已正确安装（路径：`~/.kimi-webbridge/bin/kimi-webbridge.exe`），或从 Kimi 设置中重新安装。"不尝试从其他路径查找二进制。 |
| 端口 10086 被非 WebBridge 进程占用 | 向 owner 报告端口冲突："端口 10086 已被进程（进程名）占用，WebBridge 可能需要更换端口。"不尝试 kill 占用进程。 |
| `curl.exe` 不存在（Windows，如旧版 Win10） | 报告："未找到 curl.exe。WebBridge 验收需要在 Windows 上使用原生 curl。请从 https://curl.se/windows/ 安装。" |
| ReadMediaFile 工具不可用 | 截图项降级为**人工验证**：截完图后请 owner 实际打开图像文件目检内容是否正确。在验收报告中标注"截图目检：人工（ReadMediaFile 不可用）"。 |
| 单项检查失败（如 navigate 成功但 snapshot 超时） | 继续执行其余检查——不因此中断。验收结束时报告全部通过/失败项，不因一项失败下"不可用"的全局结论。 |
