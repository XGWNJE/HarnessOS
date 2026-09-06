# HarnessOS 受管资产目录

> 此文件由 `python scripts/catalog.py render` 生成，请修改原生事实源而不是本文件。

共 64 项资产、0 个配置档。

## development-tool

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `development-tool:android-sdk` | Android SDK | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Android 平台、构建工具、ADB、模拟器与 SDK 命令行管理能力。 |
| `development-tool:aws-cli` | AWS CLI | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 从命令行管理和自动化 Amazon Web Services 资源。 |
| `development-tool:azure-cli` | Azure CLI | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 从命令行管理和自动化 Microsoft Azure 资源。 |
| `development-tool:blender-mcp` | Blender MCP | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 通过 MCP 将 AI 客户端连接到 Blender，用于查询场景和调用 Blender Python API。 |
| `development-tool:bun` | Bun | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供独立的 JavaScript 运行时、包管理器、测试与打包工具。 |
| `development-tool:claude-code` | Claude Code | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Anthropic Claude 的终端 AI 编程代理入口。 |
| `development-tool:cmake` | CMake | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供跨平台原生项目配置、构建生成、测试与打包入口。 |
| `development-tool:deepseek-harness` | DeepSeek Harness CLI | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 DeepSeek Harness 的本地命令行与 Web 工作台启动入口。 |
| `development-tool:git` | Git for Windows | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供源代码版本控制、Git 仓库操作和 Windows Git 工具链。 |
| `development-tool:github-cli` | GitHub CLI | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 从命令行管理 GitHub 仓库、Issue、Pull Request、Release 与工作流。 |
| `development-tool:google-cloud-sdk` | Google Cloud SDK | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Google Cloud 资源、存储和 BigQuery 的命令行管理入口。 |
| `development-tool:jq` | jq | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 在脚本和终端中查询、转换与验证 JSON 数据。 |
| `development-tool:kubectl` | Kubernetes CLI | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 通过 kubectl 检查和管理 Kubernetes 集群资源与清单。 |
| `development-tool:lark-cli` | Lark/飞书 CLI | `communication` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 通过官方命令行工具访问飞书开放平台能力，并为人工或 AI Agent 提供结构化操作入口。 |
| `development-tool:llvm` | LLVM Toolchain | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Clang/LLVM 编译、链接、调试、格式化和语言服务工具。 |
| `development-tool:nodejs` | Node.js | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 JavaScript/TypeScript 运行时及 npm 生态的基础开发环境。 |
| `development-tool:openssl` | OpenSSL Developer Tools | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 TLS、证书、密钥格式和密码学相关的开发与诊断命令。 |
| `development-tool:php` | PHP | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 PHP 命令行运行、调试和服务端项目开发环境。 |
| `development-tool:pnpm` | pnpm | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供高效、严格的 Node.js 包依赖安装与工作区管理。 |
| `development-tool:poetry` | Poetry | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 管理 Python 项目的依赖、虚拟环境、构建与发布元数据。 |
| `development-tool:python` | Python | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Python 解释器、脚本运行、自动化与包管理基础环境。 |
| `development-tool:ripgrep` | ripgrep | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供高速递归文本与代码搜索能力。 |
| `development-tool:ruby` | RubyInstaller | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Ruby 解释器、RubyGems 与常用 Ruby 项目工具。 |
| `development-tool:rust-toolchain` | Rust Toolchain | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Rust 编译、包管理、格式化、静态检查和语言服务工具链。 |
| `development-tool:sqlite` | SQLite CLI | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供本地 SQLite 数据库查询、差异与分析命令。 |
| `development-tool:temurin-jdk` | Eclipse Temurin JDK | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Java LTS 运行时、编译器、打包、诊断和调试工具。 |
| `development-tool:terraform` | Terraform | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 以基础设施即代码方式规划和管理云与服务资源。 |
| `development-tool:uv` | uv | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供独立的 Python 包、项目、工具和解释器管理能力。 |
| `development-tool:winlibs-mingw` | WinLibs MinGW-w64 Toolchain | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Windows 原生 GCC/MinGW-w64 编译、链接、调试和配套构建工具链。 |
| `development-tool:yarn` | Yarn Classic | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 兼容仍使用 Yarn Classic 锁文件与命令的 Node.js 项目。 |
| `development-tool:yq` | yq | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 在脚本和终端中查询、转换与验证 YAML 数据。 |

## rule

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `rule:global-agents` | 全局 Agent Rules | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 跨项目协作约束 |

## skill

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `skill:ai-stack-harness` | ai-stack-harness | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | AI 编程技术栈选型与判断基线的参考事实来源（目标模式）。global/AGENTS.md「AI 协作与工程判断基线」给出判断句与验收红线；本 skill 保留其详细验收清单、推荐分层栈与证据链回路作为可核验参考。触发时以全局 Rules… |
| `skill:archify` | archify | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | Create polished, validated architecture, workflow, sequence, data-flow, and lifecycle/state diagrams as explorable stan… |
| `skill:codex-session-recovery` | codex-session-recovery | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 诊断与恢复 Codex Desktop 历史会话。用于切换 Provider 或账号后任务列表缺失、rollout 正文缺失、SQLite 索引与文件不一致、旧会话不可见或需要从备份安全合并历史记录的场景。 |
| `skill:electron-runtime-debugging` | electron-runtime-debugging | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 诊断 Electron 桌面应用中类型声明与运行时不一致、IPC 重复监听或过早发送、ESM 迁移连带故障、打包遗漏运行时数据，以及 globalShortcut/RegisterHotKey 自动重复导致的交互异常。 |
| `skill:grsai-image-gen` | grsai-image-gen | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | HarnessOS 默认绘图/图片生成能力。当默认模型或 Agent 不具备原生绘图能力时，用此技能生成图片、插图、素材、封面、海报等视觉内容。托管在 Grsai API（付费 API，需 GRSAI_API_KEY），支持异步轮询、参考… |
| `skill:image-understand` | image-understand | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 识图/图像理解能力。当默认模型不支持图片输入（如纯文本模型）或需要独立视觉分析时，把本地图片/图片 URL 转成文字描述、OCR 文本、图表解读交给主模型使用。默认通道智谱 GLM-4V-Flash（永久免费）；免费通道结果不佳时提醒用户… |
| `skill:kimi-webbridge` | kimi-webbridge | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | Kimi WebBridge lets AI control the user's real browser — navigate, click, type, read, screenshot, and interact with any… |
| `skill:mini-vault` | mini-vault | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | 中转站（get.xgwnje.cn / mini-vault）文件上传与下载核验。当需要把构建产物（APK/安装包/截图/日志等）传到中转站供用户自行下载到真机测试，或核验中转站可用性时使用。目标：上传前已获用户明确同意（问过才传，不擅自… |
| `skill:quarkclouddrive` | quarkclouddrive | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | 夸克网盘官方(Quark Drive)Skill，用于文件上传/下载（支持断点续传）、文件分享与转存、网盘文件搜索、相册整理、AI助手（文件总结与知识问答，支持万级文件）。当用户需要操作夸克网盘文件或进行身份验证时使用。 |
| `skill:vibehub` | vibehub | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | — | 帮助人们获取并学习 Vibe Coding 相关知识，包括 UI、网页、软件、Git、AI Agent 与设计概念。适用于用户明确调用 VibeHub、在 Vibe Coding 过程中看不懂 Agent 回复里的术语并要求通俗解释、描述… |
| `skill:vps-server-info` | vps-server-info | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | VPS 服务器连接信息（IP/端口/SSH/部署路径）。当项目需要 SSH 连接 VPS、部署 server、查询服务器配置时使用，目标是安全、准确地完成 VPS 相关操作。 |
| `skill:webbridge-acceptance` | webbridge-acceptance | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | — | Kimi WebBridge（浏览器控制）可用性验收。当需要在新环境/新机器验收 WebBridge 是否可用、或验收类操作后清理现场时使用。验收目标：守护进程连通、navigate、snapshot、evaluate、screensho… |

## software

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `software:android-studio` | Android Studio | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Android 项目的官方 IDE、Gradle 集成、调试与设备管理入口。 |
| `software:codex-desktop` | Codex 桌面端 | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Codex 桌面任务、工作区、浏览器与本地代理协作入口。 |
| `software:feishu-desktop` | 飞书桌面客户端 | `communication` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 在 Windows 工作站提供飞书即时沟通、会议、日历、文档与协作入口。 |
| `software:fontbase` | FontBase | `creative-media` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供字体预览、分类与启用管理。 |
| `software:genshin-impact` | 原神 | `entertainment` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Windows 版原神客户端及其本地游戏资源。 |
| `software:google-chrome` | Google Chrome | `browser-web` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供网页浏览、账号登录与 Web 应用访问。 |
| `software:krita` | Krita | `creative-media` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供数字绘画、图像编辑与绘画资源管理。 |
| `software:mi-hoyo-launcher` | 米哈游启动器 | `entertainment` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 统一管理米哈游 PC 游戏的安装、更新、修复与启动。 |
| `software:mpv` | mpv | `entertainment` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供本地音视频播放。 |
| `software:obsidian` | Obsidian | `productivity` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供本地 Markdown 知识库编辑与链接式笔记管理。 |
| `software:opencode-desktop` | OpenCode Desktop | `ai-agent` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 OpenCode 的桌面 AI 编程与本地项目交互入口。 |
| `software:soda-music` | 汽水音乐 | `entertainment` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供音乐播放、发现与账号内容服务。 |
| `software:tuba-toolbox` | 图吧工具箱 | `system-hardware` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Windows 硬件检测、信息查看与性能测试工具集合。 |
| `software:uu-remote` | UU远程 | `network-remote` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供远程桌面连接与远程控制。 |
| `software:visual-studio-community` | Visual Studio Community | `development` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Windows 与 .NET 桌面应用的集成开发、编译、调试和 SDK 工作负载。 |
| `software:wechat` | 微信 | `communication` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供桌面即时通信、文件传输与扫码登录入口。 |
| `software:wechat-input` | 微信输入法 | `productivity` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供中文文字输入与词库服务。 |
| `software:zenless-zone-zero` | 绝区零 | `entertainment` | 第三方 | 跟踪 | `managed` | `current` | owner-declared | 提供 Windows 版绝区零客户端及其本地游戏资源。 |

## workflow

| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |
|---|---|---|---|---|---|---|---|---|
| `workflow:register-managed-asset` | 登记受管资产 | `ai-agent` | 用户自产 | 不适用 | `managed` | `current` | owner-declared | 把用户明确指定的对象登记为可查看、可迁移、可恢复的受管资产。 |
| `workflow:restore-workstation` | 恢复工作站 | `system-hardware` | 用户自产 | 不适用 | `managed` | `current` | owner-declared | 依据已确认的资产与配置档，生成并验收一套符合用户习惯的工作站。 |

## 关系

| 来源 | 关系 | 目标 |
|---|---|---|
| `development-tool:blender-mcp` | `depends-on` | `development-tool:uv` |
| `development-tool:claude-code` | `depends-on` | `development-tool:nodejs` |
| `development-tool:deepseek-harness` | `depends-on` | `development-tool:nodejs` |
| `development-tool:github-cli` | `uses` | `development-tool:git` |
| `development-tool:lark-cli` | `depends-on` | `development-tool:nodejs` |
| `development-tool:pnpm` | `depends-on` | `development-tool:nodejs` |
| `development-tool:poetry` | `depends-on` | `development-tool:python` |
| `development-tool:yarn` | `depends-on` | `development-tool:nodejs` |
| `software:android-studio` | `uses` | `development-tool:android-sdk` |

## 配置档

暂无配置档。

## 待复核

暂无。
