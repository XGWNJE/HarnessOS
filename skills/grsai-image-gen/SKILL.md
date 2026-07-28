---
version: 1.3.0
name: grsai-image-gen
description: HarnessOS 默认绘图/图片生成能力。当默认模型或 Agent 不具备原生绘图能力时，用此技能生成图片、插图、素材、封面、海报等视觉内容。托管在 Grsai API（付费 API，需 GRSAI_API_KEY），支持异步轮询、参考图、多种比例/分辨率、视频。目标：在成本与质量间合理取舍，密钥零暴露，结果可预览可下载。注意：若当前模型/Agent 自身能画（如 Codex 原生出图），优先用原生能力；Grsai 为兜底/付费托管方案。
---

# Grsai 图片生成

> 写法：目标模式——只描述想要的目标与验收标准，不规定具体做法；做法由模型按情境自决。
> 标注「机制」的段落是无可替代的调用机制（离开它任务做不成），原样保留，不是规定。

## 环境前提

此段仅声明事实，不规定 Agent 行为。

- **运行时**：本 skill 的 API 调用模板需要 **PowerShell**（Windows）或 **Bash + curl + jq**（Linux/macOS/Git Bash）。两种模板并列提供，模型按当前运行时自选。
- **密钥**：环境变量 `GRSAI_API_KEY` 必须已设置且有效。缺失时本 skill 不可用。
- **网络**：需可达 `https://grsaiapi.com`（全球）或 `https://grsai.dakka.com.cn`（国内）。网络不可达时生成不可执行。
- **付费**：Grsai 是付费 API，每次调用消耗余额。余额不足时请求被拒（非本 skill 可修复）。

## 目标

- **密钥零暴露**。验收：skill 文件、命令、日志、最终回答中不存在明文 API key；密钥只从环境变量 `GRSAI_API_KEY` 读取；完整的 `Authorization` 头与原始请求头不被打印；报错信息含密钥时先脱敏再报告；`GRSAI_API_KEY` 缺失时不发起付费/API 调用，先请用户设置。
- **付费调用有意图确认**。验收：每次生成都按潜在付费的外部 API 调用对待；请求含糊、高分辨率、重复生成、或使用 `-vip`/4K 模型时，调用前用户已确认意图；用户说价格/成本重要时，选中的是满足需求的最低成本模型与参数，且调用前已说明取舍。
- **参考图不越权**。验收：本地/参考图只在用户为本次任务提供或明确确认使用时才上传。
- **歧义先澄清，其余直接推进**。验收：以下五种情况在发起调用前用户已被简短澄清——(1) 未提供具体视觉内容；(2) 提到多个输出场景且比例冲突；(3) 请求的比例/分辨率不受支持；(4) 要求"最好/最高/4K/`-vip`/大量图片"且成本可能敏感；(5) 提供了参考图但用途不明。其余情况按默认值直接推进，不反问。
- **内容合规**。验收：用户视觉意图被保留；过短提示词被扩写为 2-3 句含风格、光照、构图、主体细节的简洁英文描述；未主动加入版权角色、真人肖像、logo 或敏感内容（用户明确要求且合规的除外）；服务返回 `violation` 时请用户修改提示词，不尝试绕过审核。
- **成本路由不浪费**。验收：`-vip`、`-pro-cl`、4K、重复生成只在用户确认质量优先于成本时使用；普通 `16:9`/`9:16`/`1:1` 输出不选极端比例 `-cl` 模型；模型标价在 1K/2K/4K 相同时仍选满足用户的最小尺寸（可用性、延迟、下载/预览成本可能不同）。
- **调用结果可用、可见**。验收：响应中至少一个 URL 被校验存在（`results[].url` 或 `data[].url`）；远程结果用 Markdown 图片展示；图片同时下载到当前工作区或用户相关输出目录，并以绝对路径（正斜杠或完整 Windows 路径）展示，最终预览不用相对路径；结果是视频时以绝对路径 Markdown 链接展示，不假装成图片。
- **错误报告脱敏且可行动**。验收：错误报告只含脱敏后的 `id`、`status`、`error` 字段；各类错误的期望结果见下文「错误语义与期望结果」表。

## 事实

### API Basics

- Global endpoint: `https://grsaiapi.com`
- China endpoint: `https://grsai.dakka.com.cn`
- Auth header: `Authorization: Bearer $env:GRSAI_API_KEY`
- Detailed API reference: `references/grsai-api-docs.md`
- 常规用法走 `POST /v1/api/generate`；`/v1/images/generations` 仅在调用方明确需要 OpenAI 兼容格式时使用。

### API 校准源

- **Authoritative API reference**: [https://qmy27nhsd9.apifox.cn/](https://qmy27nhsd9.apifox.cn/)
- 本 skill 记录的模型、参数、比例、响应格式与 Apifox 文档冲突时，**以文档为准**；发现漂移时先把本 skill 更新到与文档一致，再继续调用。Apifox 文档可能比本 skill 新，它是端点路径、字段名、支持模型、合法取值的实时真相源。

### 模型与价格

Pricing changes over time. The rough order below is based on Grsai's public model list and should be treated as routing guidance, not a guaranteed quote. If exact cost matters, check the Grsai dashboard/model list before calling.

Approximate image model pricing:

| Model | Credits | Price example | Notes |
|---|---:|---:|---|
| `nano-banana-fast` | 440/time | ￥0.022~￥0.044/time | Cheapest image option; good for drafts and price-sensitive tasks |
| `gpt-image-2` | 600/time | ￥0.03~￥0.06/time | Default balanced option; low-cost 1K with good instruction following |
| `nano-banana-2` | 1200/time | ￥0.06~￥0.12/time | Alternative balanced option; 1K/2K/4K same listed price |
| `gpt-image-2-vip` | 1300/time | ￥0.065~￥0.13/time | Higher quality GPT Image option; supports 1K/2K/4K pixels |
| `nano-banana-pro` | 1800/time | ￥0.09~￥0.18/time | Higher quality; 1K/2K/4K same listed price |
| `nano-banana-2-cl` | 1600/time | ￥0.08~￥0.16/time | Use only for extreme ratios; supports 1K/2K |
| `nano-banana-2-4k-cl` | 3000/time | ￥0.15~￥0.3/time | Use only for 4K extreme-ratio needs |
| `nano-banana-pro-cl` | 6000/time | ￥0.3~￥0.6/time | Expensive extreme-ratio pro channel |
| `nano-banana-pro-vip` | 10000/time | ￥0.5~￥1/time | High-cost channel; avoid unless explicitly needed |
| `nano-banana-pro-4k-vip` | 16000/time | ￥0.8~￥1.6/time | Most expensive listed image option; use only when explicitly requested |

Models confirmed by the Apifox document but not yet priced here: `nano-banana-2-2k-cl`, `nano-banana-pro-vt`. Treat them as available; check Grsai dashboard for current pricing before routing.

Price-sensitive routing facts:

- Drafts, quick previews, or "便宜点/省钱/低成本" → `nano-banana-fast` at `1K`.
- Better instruction following while cost-sensitive → `gpt-image-2` at `1024x1024` or a supported 1K size.

Default choices:

| User intent | Model | Size rule |
|---|---|---|
| General image/material/illustration | `gpt-image-2` | Infer aspect ratio or use a supported 1K pixel size |
| Fast draft | `nano-banana-fast` | `1K` |
| High quality | `nano-banana-pro` | `2K` unless user asks otherwise |
| Print, poster, very high quality | `nano-banana-pro-vip` or `gpt-image-2-vip` | Confirm cost/quality first |
| Ultra-wide/ultra-tall | `nano-banana-2-cl` or `nano-banana-pro-cl` | Use only supported extreme ratios |

Aspect ratio defaults:

| Scenario | aspectRatio | imageSize |
|---|---|---|
| Avatar | `1:1` | `1K` |
| Phone wallpaper | `9:16` | `2K` |
| Desktop wallpaper | `16:9` | `2K` |
| Xiaohongshu/Instagram | `1:1` or `4:5` | `1K` |
| WeChat article cover | `16:9` | `1K` |
| Banner | `21:9` or `16:9` | `1K` |
| Poster | `2:3` or `3:4` | `2K` |
| Unspecified | `1:1` | `1K` |

Compatibility facts:

- `nano-banana` models use `aspectRatio` plus optional `imageSize`.
- Supported `aspectRatio` values per the Apifox document: `auto`, `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `5:4`, `4:5`, `21:9`.
- `nano-banana-2` series additionally supports extreme ratios: `1:4`, `4:1`, `1:8`, `8:1`.
- `gpt-image-2` accepts a ratio such as `16:9` or a 1K pixel value such as `1024x1024`.
- `gpt-image-2-vip` requires pixel dimensions such as `2048x2048`; ratios like `16:9` are not accepted.
- For `gpt-image-2-vip`, width/height must both be multiples of 16, max side <= 3840, long/short ratio <= 3:1, and total pixels between 655360 and 8294400.
- For `/v1/images/generations`, reference images use field `image`; for `/v1/api/generate`, reference images use field `images`.

### 错误语义与期望结果

| Case | 期望结果 |
|---|---|
| Missing `GRSAI_API_KEY` | 未发起 API 调用，用户被告知需要先设置密钥 |
| 400 / parameter error | 报告含所用模型、比例/尺寸与脱敏后的错误信息 |
| `violation` status | 用户被要求修改提示词 |
| 401 | 用户被告知密钥无效/过期；密钥本身不泄露 |
| 429 | 退避后重试一次，或请用户稍后重试 |
| Timeout | 改用下方标准异步机制；不盲目重试同步调用 |
| 5xx | 报告为临时性服务故障；有 task ID 时保留 |

## 机制

以下段落是无可替代的调用机制，原样保留，不是规定。

### 机制：PowerShell 执行环境

运行时 Bash 工具是 Git Bash，**不是** PowerShell，PowerShell 片段不能直接粘进 Bash。可行机制：脚本写入临时 `.ps1` 文件，用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>` 执行，用后删除临时 `.ps1` 文件。

PowerShell key check:

```powershell
if (-not $env:GRSAI_API_KEY) {
  throw 'Missing GRSAI_API_KEY. Set it before calling Grsai.'
}
```

### 机制：标准异步调用

同步调用在 1K+ 图片上经常超时，因此默认 `replyType: 'async'`；`replyType: 'json'` 只用于极快草稿或调用方明确要阻塞调用。请求体用 PowerShell hashtable 结构化构造（`ConvertTo-Json`），不拼接 JSON 字符串。

Write to a temp file, e.g. `grsai-call.ps1`:

```powershell
$body = @{
  model       = 'gpt-image-2'
  prompt      = '<prompt>'
  images      = @()
  aspectRatio = '1024x1024'
  replyType   = 'async'
} | ConvertTo-Json -Depth 8

$headers = @{
  Authorization = "Bearer $env:GRSAI_API_KEY"
  'Content-Type' = 'application/json'
}

# 1. Submit
$submit = Invoke-RestMethod -Uri 'https://grsaiapi.com/v1/api/generate' -Method Post -Headers $headers -Body $body -TimeoutSec 120
$taskId = $submit.id
if (-not $taskId) { throw "No task id returned: $($submit | ConvertTo-Json -Depth 4)" }

# 2. Poll
$final = $null
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 10
  $result = Invoke-RestMethod -Uri "https://grsaiapi.com/v1/api/result?id=$taskId" -Method Get -Headers $headers -TimeoutSec 60
  if ($result.status -in @('succeeded','failed','violation')) { $final = $result; break }
}
if (-not $final) { throw "Task $taskId still running after 30 polls" }
if ($final.status -ne 'succeeded') { throw "Task $taskId ended with status: $($final.status)" }

# 3. Download
$imageUrl = $final.results[0].url
$out = Join-Path (Get-Location) 'grsai-output.png'
Invoke-WebRequest -Uri $imageUrl -OutFile $out

# 4. Output for preview
[PSCustomObject]@{
  id       = $taskId
  status   = $final.status
  url      = $imageUrl
  localPath = $out
} | ConvertTo-Json -Depth 4
```

Run from Bash:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:/path/to/grsai-call.ps1"
```

### 机制：Bash 异步调用模板（curl + jq）

用于非 Windows 或 Bash-only 环境。与 PowerShell 模板并列——Agent 按当前运行时自选。

写入临时文件（如 `grsai-call.sh`）后 `bash grsai-call.sh` 执行：

```bash
#!/usr/bin/env bash
set -euo pipefail

API_KEY="${GRSAI_API_KEY:?GRSAI_API_KEY not set}"
ENDPOINT="${GRSAI_ENDPOINT:-https://grsaiapi.com}"

# 1. Submit
RESP=$(curl -sS --max-time 120 -X POST "${ENDPOINT}/v1/api/generate" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"<prompt>","images":[],"aspectRatio":"1024x1024","replyType":"async"}')

TASK_ID=$(echo "$RESP" | jq -r '.id // empty')
if [ -z "$TASK_ID" ]; then
  echo "[失败] 提交未返回 task id: $RESP" >&2
  exit 1
fi
echo "[提交] $TASK_ID"

# 2. Poll (max 30 attempts × 10s = 5 min)
for i in $(seq 1 30); do
  sleep 10
  RESULT=$(curl -sS --max-time 60 "${ENDPOINT}/v1/api/result?id=${TASK_ID}" \
    -H "Authorization: Bearer ${API_KEY}")
  STATUS=$(echo "$RESULT" | jq -r '.status // "pending"')
  echo "[轮询 $i/30] $STATUS"
  case "$STATUS" in
    succeeded|failed|violation) break ;;
  esac
done

if [ "$STATUS" != "succeeded" ]; then
  echo "[失败] task $TASK_ID status=$STATUS" >&2
  exit 1
fi

# 3. Download
URL=$(echo "$RESULT" | jq -r '.results[0].url // .data[0].url // empty')
if [ -z "$URL" ]; then
  echo "[失败] 无结果 URL" >&2
  exit 1
fi
OUT="grsai-output.png"
curl -sS -o "$OUT" "$URL"
echo "[完成] $OUT  (task: $TASK_ID)"
```

### 机制：结果预览格式

远程结果用 Markdown 展示：

```markdown
![生成结果](https://example.com/result.png)
```

本地下载结果用绝对路径展示（标准异步机制已返回 `localPath`）：

```markdown
![生成结果](D:/ObjectCode/grsai-api/grsai-output.png)
```

## 环境自检

本 skill 被触发后，在发起第一次付费 API 调用前，先无声确认以下前提（不向用户展示自检细节，仅在条件不满足时报告）：

1. **密钥检查**：`$env:GRSAI_API_KEY`（PowerShell）或 `$GRSAI_API_KEY`（Bash）非空
2. **端点可达**：选一个端点发出轻量请求（如 HEAD `/`），确认不是网络不可达
3. **运行时可用**：至少存在 PowerShell 或 Bash+curl+jq 之一的调用路径

自检通过 → 直接进入生成流程，不向用户报告自检结果。
任一前提不满足 → 见下方「失效模式」对应的降级行为。

## 失效模式

以下为环境前提不满足时的降级行为——不是流程建议，是必须遵守的失效契约：

| 前提失败 | 降级行为 |
|---|---|
| `GRSAI_API_KEY` 缺失或为空 | **不发起任何 API 调用**。向用户报告："请在环境变量中设置 GRSAI_API_KEY（Grsai API 密钥）。获取方式见 https://grsai.com 。"不猜测密钥、不尝试其他 API。 |
| 端点网络不可达（连接超时/DNS 失败） | 尝试另一个端点（全球↔国内切换）一次。两次均失败则报告："Grsai API 当前不可达（已尝试全球/国内端点）。请检查网络或稍后重试。"不无限重试。 |
| 当前运行时既无 PowerShell 也无 Bash+curl+jq | 报告："当前环境缺少 Grsai API 调用所需的运行时（PowerShell 或 Bash+curl+jq）。"不尝试用非标准工具构造 HTTP 请求。 |
| API 返回 401（密钥无效） | 报告密钥无效，请用户更新 `GRSAI_API_KEY`。**密钥值本身不出现在任何输出中。** |
| API 返回 402/余额不足 | 报告余额不足，请用户充值。不尝试切换模型——低余额时不同模型可能同样被拒。 |
| 提交成功但轮询超时（30 次×10s 后仍未完成） | 报告 task ID，请用户稍后手动查询。不盲目重试——超时通常意味着服务排队，重试只会重复排队。 |
