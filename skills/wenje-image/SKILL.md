---
version: 2.1.0
name: wenje-image
description: 需要生成或编辑图片而默认模型不能原生出图时，用本 skill 出图（Grsai，按张付费）；调用前需确认付费意图。
---

# wenje-image

默认模型没有原生出图能力时，本 skill 提供出图与改图。全部能力由 `scripts/wenje_image.py` 一个引擎承担，按张计费，密钥只从本机配置或环境变量读取。

**模型与规格由用户声明决定；用户没点名的部分由 Agent 直接定，不反问。** 详见下方「目标」。

## 入口：优先用 MCP 工具，其次用 CLI

两条入口能力等价，走同一条引擎。**先看工具列表里有没有 `generate_image`**。

### 入口一：MCP 工具（有则必用）

| 工具 | 用途 |
|---|---|
| `generate_image` | 出图/改图；内部走完提交→轮询→下载→命名，并把预览图直接返回 |
| `image_status` | 密钥来源、端点、鉴权是否有效、默认档位、今日用量 |
| `open_setup_page` | 打开本地设置页，由用户自己在浏览器里录入密钥 |

用 MCP 时**不要**再写临时脚本、不要自己拼 URL 或轮询、也不要把提示词塞进 shell 命令——提示词是结构化参数，中文与引号不需要转义。

工具没出现时先注册（写配置前自动备份，需重启 Agent 生效）：

```bash
python <本skill目录>/scripts/wenje_image.py install --agent zcode   # 也可 codex / claude / all
python <本skill目录>/scripts/wenje_image.py install --print        # 只打印配置片段，不改文件
```

### 入口二：CLI（MCP 不可用时）

```bash
python <本skill目录>/scripts/wenje_image.py status
python <本skill目录>/scripts/wenje_image.py generate --prompt "窗台上的橘猫，暖色调" --ratio 16:9
python <本skill目录>/scripts/wenje_image.py generate --prompt-file ./prompt.txt --scene poster
python <本skill目录>/scripts/wenje_image.py generate --prompt "…" --tier draft --dry-run
python <本skill目录>/scripts/wenje_image.py setup
```

- `--tier draft|standard|premium` 选成本档位（默认 standard → `gpt-image-2`）；`--model` 直接点名模型并覆盖 `--tier`。
- `--ratio`、`--size 1K|2K|4K`、`--scene` 定比例与分辨率；`--ref <路径>` 传参考图（可重复）。
- 提示词长、含换行或引号时写进文件用 `--prompt-file`，不要在命令行里做转义。
- `--dry-run` 只打印将发送的请求与预估价格，不调用 API——用它自查成本，不要靠猜。
- 默认下载到 `~/Pictures/wenje-image/`，文件名由提示词摘要加时间戳生成。

## 目标

- **密钥零暴露**。验收：skill 文件、命令、日志与最终回答中不存在明文密钥；密钥只来自本机配置或 `GRSAI_API_KEY`；**不让用户在对话里粘贴密钥**，缺密钥时走 `open_setup_page`（或 `setup`）让用户在浏览器里填；报错信息含密钥时先脱敏再报告。
- **模型与规格：用户声明优先，未声明由 Agent 决定**。验收：用户在请求里点名的模型、档位、比例、尺寸被原样采用，不被替换成"更便宜"或"更保险"的选项；用户未声明的部分由 Agent 按默认路由直接决定，**不为此反问用户**；用户的两项声明互相冲突时（如点名的模型不支持该比例），Agent 在同模型内改选最接近的受支持取值，并在结果里说明改了什么，不中断流程。
- **不把选择题推回用户**。验收：不单独为"用哪个模型、多大、什么比例"发起澄清；只有"对什么内容出图"完全没给、且无法从上下文推断时才问一次。
- **参考图不越权**。验收：`--ref`/`reference_images` 只接收用户为本次任务提供或明确确认使用的图。
- **内容合规**。验收：用户视觉意图被保留；过短提示词被扩写为 2-3 句含主体、风格、光照、构图的描述；不主动加入版权角色、真人肖像、logo 或敏感内容；被判违规时请用户改提示词，不尝试绕过审核。
- **成本自控而不请示**。验收：未声明档位时默认走 standard（`gpt-image-2`，约 ￥0.03~0.06/张），不默认选高价通道；`-vip`、`-pro-cl`、4K 只在用户点名或明确要求质量优先时使用；普通比例不选极端比例通道；同一标价下选满足需求的最小尺寸；用户说成本敏感时选最低成本档并用 `--dry-run` 自查预估价格；用户点名高价模型时照做，不二次确认。
- **结果可用、可见**。验收：本机文件用**绝对路径**（正斜杠或完整 Windows 路径）Markdown 展示，不用相对路径；视频结果用链接展示，不假装成图片；远端 URL 只在未下载时使用。
- **失败可定性**。验收：失败时给出退出码对应的类别与下一步动作（见下表），不把"响应为空"这类含糊结果直接抛给用户。

## 退出码

CLI 与 MCP 用同一套分类，便于按类处置：

| 码 | 含义 | 处置 |
|---|---|---|
| 0 | 成功 | — |
| 2 | 参数错误 | 报错会列出合法取值；由 Agent 依据用户意图改选受支持取值后继续，不把选择题交回用户 |
| 3 | 未配置密钥 | 走 `open_setup_page` / `setup` |
| 4 | 密钥无效 | 重新配置密钥 |
| 5 | 余额不足 | 请用户充值，不切换模型重试 |
| 6 | 内容违规 | 请用户改提示词 |
| 7 | 网络不可达 | 换端点（全球↔国内）重试一次，仍失败则报网络问题 |
| 8 | 轮询超时 | 报 task id，让用户稍后查询；不盲目重投 |
| 9 | 服务端错误 | 报为临时故障，保留 task id |

## 失效模式

环境前提不满足时的降级行为——是失效契约，不是流程建议：

| 前提失败 | 降级行为 |
|---|---|
| 未配置密钥 | 不发起任何 API 调用。调 `open_setup_page`（或提示运行 `setup`），由用户在浏览器填入；不猜测密钥、不让用户在对话里粘贴、不尝试其他 API。 |
| 端点不可达 | 切换另一个端点重试一次。两次均失败则报告网络不可达，不无限重试。 |
| 无 Python 3.9+ | 本 skill 不可用。报告缺少运行时，不用非标准工具手工拼 HTTP 请求。 |
| 未注册 MCP | 退回 CLI 入口，功能不降级。 |
| 返回违规状态 | 请用户修改提示词。不换模型重试同一提示词——低余额或换模型同样会被拒。 |

## 按需参考

- 选型、价格、比例与路由规则：[references/providers.md](references/providers.md)
- 端点、字段、响应结构与实测校准：[references/grsai-api-docs.md](references/grsai-api-docs.md)
- MCP 注册与故障排查：[references/mcp.md](references/mcp.md)
- 架构图（给人看的独立 HTML，用浏览器打开，含可切换视图）：[references/architecture.html](references/architecture.html)
- 本地自检（不产生费用）：`python <本skill目录>/tests/local_check.py`
