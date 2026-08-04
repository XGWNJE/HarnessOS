---
version: 1.0.0
name: image-understand
description: 识图/图像理解能力。当默认模型不支持图片输入（如纯文本模型）或需要独立视觉分析时，把本地图片/图片 URL 转成文字描述、OCR 文本、图表解读交给主模型使用。默认通道智谱 GLM-4V-Flash（永久免费）；免费通道结果不佳时提醒用户可切换付费通道 GLM-4V-Plus（4 元/百万 token）。密钥零暴露，付费调用先确认。
---

# 识图（图像理解）

> 写法：目标模式——只描述想要的目标与验收标准，不规定具体做法；做法由模型按情境自决。
> 标注「机制」的段落是无可替代的调用机制（离开它任务做不成），原样保留，不是规定。

## 环境前提

此段仅声明事实，不规定 Agent 行为。

- **运行时**：API 调用模板需要 **PowerShell**（Windows）或 **Bash + curl**（Linux/macOS/Git Bash）。两种模板并列，模型按当前运行时自选。
- **密钥**：环境变量 `ZHIPU_API_KEY`（智谱开放平台 API Key）必须已设置且有效。缺失时本 skill 不可用。注册地址：https://open.bigmodel.cn
- **网络**：需可达 `https://open.bigmodel.cn`。
- **付费**：默认通道 GLM-4V-Flash 永久免费；付费通道 GLM-4V-Plus 每次调用消耗余额，仅在用户确认后使用。

## 目标

- **免费优先，付费兜底**。验收：简单/常规识图任务（图片描述、OCR、图表粗读、视觉问答）默认走免费通道 `glm-4v-flash`；付费通道 `glm-4v-plus` 只在用户确认后使用。
- **体验不佳时提醒切换，不静默升级**。验收：以下任一情况出现时，明确告诉用户「免费通道能力不足，可切换付费通道 glm-4v-plus（4 元/百万 token，一张图约几厘钱），是否切换？」——用户确认才调用付费通道：(1) 任务复杂（长文 OCR、图表数值细节、多步视觉推理）且免费通道结果明显错误/含糊；(2) 免费通道结果与图片内容明显不符；(3) 用户主动说结果不行。付费通道调用后若仍不佳，如实报告，不继续烧钱。
- **密钥零暴露**。验收：skill 文件、命令、日志、最终回答中无明文 API key；密钥只从环境变量 `ZHIPU_API_KEY` 读取；完整 Authorization 头不被打印；报错含密钥时先脱敏再报告。
- **图片输入不越权**。验收：本地图片只在用户为本次任务提供或明确确认使用时才读取并转码上传；不扫描用户磁盘找图片。
- **结果可核验、可追溯**。验收：返回的视觉结果标注所用通道与模型（免费/付费）；本地图片分析时展示原图路径，让用户能核对「分析的是哪张图」。
- **错误报告脱敏且可行动**。验收：错误报告不含密钥；各类错误按下方「失效模式」处理。

## 事实

### API 基础

- 端点：`https://open.bigmodel.cn/api/paas/v4/chat/completions`（OpenAI 兼容格式）
- 鉴权：`Authorization: Bearer $env:ZHIPU_API_KEY`
- 模型名：免费 `glm-4v-flash`；付费 `glm-4v-plus`
- 官方文档（权威源）：https://docs.bigmodel.cn —— 模型列表、限流、图片大小限制以官方文档为准；发现本 skill 与文档冲突时以文档为准并更新本 skill
- 扩展：如需接其他 OpenAI 兼容供应商（如阿里百炼 Qwen3-VL、中转网关），改端点与模型名即可，消息格式不变

### 模型与价格

| 通道 | 模型 | 价格 | 适用 |
|---|---|---|---|
| 免费（默认） | `glm-4v-flash` | 永久免费 | 图片描述、OCR、图表粗读、常规视觉问答 |
| 付费（备选） | `glm-4v-plus` | 4 元/百万 token（输入输出同价） | 复杂推理、长文 OCR、图表细节数值、多图/视频帧理解 |

白话成本参考：一张图约消耗 1~2 千 token，付费通道一张图约 0.005~0.01 元；免费通道 0 元。实际以官方价格页为准。

### 图片输入

- 本地图片：转 Base64 后以 data URI 传入（`data:image/png;base64,...`）
- 网络图片：直接传 URL
- 图片过大（报错或超时）时：先压缩/裁剪再传；不盲目重试

## 机制

以下段落是无可替代的调用机制，原样保留，不是规定。

### 机制：PowerShell 调用模板（本地图片）

运行时 Bash 工具是 Git Bash，**不是** PowerShell，PowerShell 片段不能直接粘进 Bash。可行机制：脚本写入临时 `.ps1` 文件，用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>` 执行，用后删除临时 `.ps1` 文件。

```powershell
param(
  [Parameter(Mandatory=$true)][string]$ImagePath,  # 本地图片绝对路径
  [string]$Question = '请详细描述这张图片的内容。'  # 想问的问题/要做的任务
)

if (-not $env:ZHIPU_API_KEY) { throw 'Missing ZHIPU_API_KEY. Set it before calling Zhipu vision API.' }
if (-not (Test-Path $ImagePath)) { throw "Image not found: $ImagePath" }

$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path $ImagePath)))
$mime = switch ([IO.Path]::GetExtension($ImagePath).ToLower()) {
  '.png'  { 'image/png' }
  '.jpg'  { 'image/jpeg' }
  '.jpeg' { 'image/jpeg' }
  '.gif'  { 'image/gif' }
  '.webp' { 'image/webp' }
  default { 'image/png' }
}

$body = @{
  model = 'glm-4v-flash'  # 付费备选：改为 glm-4v-plus（须先经用户确认）
  messages = @(@{
    role = 'user'
    content = @(
      @{ type = 'image_url'; image_url = @{ url = "data:$mime;base64,$b64" } },
      @{ type = 'text'; text = $Question }
    )
  })
} | ConvertTo-Json -Depth 10

$headers = @{
  Authorization = "Bearer $env:ZHIPU_API_KEY"
  'Content-Type' = 'application/json'
}

$resp = Invoke-RestMethod -Uri 'https://open.bigmodel.cn/api/paas/v4/chat/completions' -Method Post -Headers $headers -Body $body -TimeoutSec 120

[PSCustomObject]@{
  model   = $resp.model
  content = $resp.choices[0].message.content
} | ConvertTo-Json -Depth 4
```

### 机制：Bash 调用模板（curl）

用于非 Windows 或 Bash-only 环境。写入临时文件（如 `vision-call.sh`）后 `bash vision-call.sh <图片路径> "<问题>"` 执行；图片为 URL 时把 `$DATA_URI` 换成真实 URL 即可：

```bash
#!/usr/bin/env bash
set -euo pipefail
API_KEY="${ZHIPU_API_KEY:?ZHIPU_API_KEY not set}"
IMG="$1"                      # 本地图片路径
QUESTION="${2:-请详细描述这张图片的内容。}"
MIME="image/png"              # 按扩展名调整为 image/jpeg、image/webp 等
B64=$(base64 -w0 "$IMG")
DATA_URI="data:${MIME};base64,${B64}"

RESP=$(curl -sS --max-time 120 -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg img "$DATA_URI" --arg q "$QUESTION" \
    '{model:"glm-4v-flash", messages:[{role:"user", content:[{type:"image_url", image_url:{url:$img}}, {type:"text", text:$q}]}]}')")

echo "$RESP" | jq -r '.choices[0].message.content // .error.message'
```

### 机制：结果展示

- 视觉结果文本直接作为主模型的推理材料，同时向用户交代「识图通道：免费 glm-4v-flash」或「付费 glm-4v-plus」。
- 本地图片分析时，展示原图绝对路径，便于用户核对。

## 环境自检

本 skill 被触发后，在发起第一次 API 调用前，先无声确认以下前提（不向用户展示自检细节，仅在条件不满足时报告）：

1. `ZHIPU_API_KEY` 非空
2. 端点可达（轻量请求确认）
3. 运行时可用（PowerShell 或 Bash+curl 至少其一）

## 失效模式

| 前提失败 | 降级行为 |
|---|---|
| `ZHIPU_API_KEY` 缺失 | **不发起任何 API 调用**。报告：「请先注册智谱开放平台（https://open.bigmodel.cn）获取 API Key，并设置为环境变量 ZHIPU_API_KEY（系统环境变量，或 Claude Code settings.json 的 env）。」 |
| 端点不可达 | 检查网络后重试一次，仍失败则报告服务不可达，不反复重试 |
| 401 | 密钥无效/过期，请用户更新 ZHIPU_API_KEY；密钥值不出现在任何输出中 |
| 429 | 退避后重试一次，仍 429 则请用户稍后重试 |
| 图片过大/超时 | 压缩或裁剪图片后重试一次 |
| 免费通道结果质量差（答错、含糊、与图片明显不符） | 按「目标」中的提醒规则向用户说明并请求确认是否切换付费通道 glm-4v-plus；用户未确认前不调用付费通道 |
| 付费通道结果仍不佳 | 如实报告，不再继续调用烧钱 |
