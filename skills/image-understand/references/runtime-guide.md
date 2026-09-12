# 智谱视觉 API 调用参考

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
