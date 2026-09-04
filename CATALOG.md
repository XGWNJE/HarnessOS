# HarnessOS 受管资产目录

> 此文件由 `python scripts/catalog.py render` 生成，请修改原生事实源而不是本文件。

共 17 项资产、0 个配置档。

## rule

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `rule:global-agents` | 全局 Agent Rules | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 跨项目协作约束 |

## skill

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `skill:ai-coding-workflow` | ai-coding-workflow | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | AI 编程的工作流 Harness（目标集合）：组织人、模型与验证环节要达到的结果与验收标准。当需要设计 AI 编程协作流程、评估模型真实干活水平、判断任务该用单模型还是多模型交叉验证、或反思 AI 产出效率时使用。核心：Token 消耗… |
| `skill:ai-stack-harness` | ai-stack-harness | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | AI 编程时代的技术栈选型与评估 Harness（目标模式）。当需要为项目（尤其是 Agent 应用、桌面应用、AI Coding 工作流）选择语言、框架、运行时或工具链时使用。核心判断标准：不只看 AI 能否生成代码，更看生成后能否快速… |
| `skill:archify` | archify | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | Create polished, validated architecture, workflow, sequence, data-flow, and lifecycle/state diagrams as explorable stan… |
| `skill:codex-session-recovery` | codex-session-recovery | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 诊断与恢复 Codex Desktop 历史会话。用于切换 Provider 或账号后任务列表缺失、rollout 正文缺失、SQLite 索引与文件不一致、旧会话不可见或需要从备份安全合并历史记录的场景。 |
| `skill:electron-runtime-debugging` | electron-runtime-debugging | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 诊断 Electron 桌面应用中类型声明与运行时不一致、IPC 重复监听或过早发送、ESM 迁移连带故障、打包遗漏运行时数据，以及 globalShortcut/RegisterHotKey 自动重复导致的交互异常。 |
| `skill:grsai-image-gen` | grsai-image-gen | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | HarnessOS 默认绘图/图片生成能力。当默认模型或 Agent 不具备原生绘图能力时，用此技能生成图片、插图、素材、封面、海报等视觉内容。托管在 Grsai API（付费 API，需 GRSAI_API_KEY），支持异步轮询、参考… |
| `skill:image-understand` | image-understand | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 识图/图像理解能力。当默认模型不支持图片输入（如纯文本模型）或需要独立视觉分析时，把本地图片/图片 URL 转成文字描述、OCR 文本、图表解读交给主模型使用。默认通道智谱 GLM-4V-Flash（永久免费）；免费通道结果不佳时提醒用户… |
| `skill:kimi-webbridge` | kimi-webbridge | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | Kimi WebBridge lets AI control the user's real browser — navigate, click, type, read, screenshot, and interact with any… |
| `skill:mini-vault` | mini-vault | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 中转站（get.xgwnje.cn / mini-vault）文件上传与下载核验。当需要把构建产物（APK/安装包/截图/日志等）传到中转站供用户自行下载到真机测试，或核验中转站可用性时使用。目标：上传前已获用户明确同意（问过才传，不擅自… |
| `skill:project-doc-boundary` | project-doc-boundary | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 管理项目文档的责任边界并纠正漂移。当 README、AGENTS.md、CHANGELOG、专题文档或文档导航出现重复、错位、过期或职责不清时使用；适用于文档重构、提交前文档体检失败和项目文档职责审查。只处理文档事实归属与漂移，不初始化项… |
| `skill:quarkclouddrive` | quarkclouddrive | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | 夸克网盘官方(Quark Drive)Skill，用于文件上传/下载（支持断点续传）、文件分享与转存、网盘文件搜索、相册整理、AI助手（文件总结与知识问答，支持万级文件）。当用户需要操作夸克网盘文件或进行身份验证时使用。 |
| `skill:vibehub` | vibehub | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | 帮助人们获取并学习 Vibe Coding 相关知识，包括 UI、网页、软件、Git、AI Agent 与设计概念。适用于用户明确调用 VibeHub、在 Vibe Coding 过程中看不懂 Agent 回复里的术语并要求通俗解释、描述… |
| `skill:vps-server-info` | vps-server-info | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | VPS 服务器连接信息（IP/端口/SSH/部署路径）。当项目需要 SSH 连接 VPS、部署 server、查询服务器配置时使用，目标是安全、准确地完成 VPS 相关操作。 |
| `skill:webbridge-acceptance` | webbridge-acceptance | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | Kimi WebBridge（浏览器控制）可用性验收。当需要在新环境/新机器验收 WebBridge 是否可用、或验收类操作后清理现场时使用。验收目标：守护进程连通、navigate、snapshot、evaluate、screensho… |

## workflow

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `workflow:register-managed-asset` | 登记受管资产 | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | owner-declared | 把用户明确指定的对象登记为可查看、可迁移、可恢复的受管资产。 |
| `workflow:restore-workstation` | 恢复工作站 | `system-hardware` | 用户自产 | 不适用 | `managed` | `current` | owner-declared | 依据已确认的资产与配置档，生成并验收一套符合用户习惯的工作站。 |

## 关系

暂无显式关系。

## 配置档

暂无配置档。

## 待复核

暂无。
