# 原料笔记：Vibe Coding 观察（2026-07）

> 来源：lencx《编程心得：Vibe 上百亿 Token 后，我收获了什么？》（公众号「浮之静」）+ 个人批注。粗糙记录，待加工。
> 日期：2026-07-23
> 场景：技术栈选型（tauri/electron/rust）、长链路 agent 任务、模型工作流（双模型交叉验证）

## 待观察 / 待验证

- Token 消耗量不是产出指标：实际落到代码的可能只有 1%~3%，大部分是上下文/推理/重写。→ 提醒自己别陷入「烧得多 = 干得多」的错觉。→ 已提炼进 ai-coding-workflow 第 1 条。
- 榜单不可信，模型真实干活水平要踩坑才知道。Fable 创造性方案强但细节有逻辑缺陷；Sol 长任务推理强，Computer-Use 适合 UI/Debug。→ 结论：复杂任务可以用「一个生成 + 另一个 review」的双模型交叉验证。→ 已提炼进 ai-coding-workflow 第 2、3 条。
- 最危险的不是 API 缺失，而是「半实现」：调用不报错但语义只做了一半，在很远的下游才炸。→ 做兼容/封装层时优先保证「诚实失败」。→ 已提炼进 ai-stack-harness 通用警示 + ai-coding-workflow 第 4 条。
- OpenCode 桌面端从 Tauri 迁回 Electron。Tauri 硬伤是系统 webview 不可控。→ 已提炼进 ai-stack-harness。
- 自编译 Chromium ≈ 维护浏览器厂商级发行链路，不要轻率尝试。
- 长链路任务靠证据链收敛：文档 → 源码 → 实现 → 自动化测试 → 真实运行 → 视觉回放 → 回文档。模型、工具、多模态三要素缺一不可。→ 已提炼进 ai-stack-harness。
- Harness > Loop：推翻重写的成本在 AI 时代大降，历史包袱是负债；但重写前先确认新底座可验证。→ 已提炼进 ai-coding-workflow 第 6 条。
- AI 生成内容 ≠ 知识，耗时的是人的搜集、交叉验证、反复确认。→ 已提炼进 ai-coding-workflow 第 5 条。

## 我的批注

- （待补充：结合 VisionGuard-RemoteAlarm / OpenCode 研究过程中的实际体感验证上述规则）
