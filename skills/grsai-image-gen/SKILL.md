---
version: 1.0.0
name: grsai-image-gen
description: Grsai API 图片/视频生成。Use only when the user explicitly asks to use Grsai, `$grsai-image-gen`, Grsai API, an external paid image API, Grsai-specific models such as nano-banana or gpt-image-2, Grsai price/cost routing, or OpenAI-compatible Grsai image endpoints. Do not trigger for generic image creation requests; let Codex native image generation handle ordinary "draw/generate an image" tasks unless Grsai is named or API/price/model control is required. Supports aspect ratio, resolution, async polling, reference-image handling, and Codex preview compatibility.
---

# Grsai 图片生成

## Safety First

- Never hard-code API keys in this skill, commands, logs, or final answers.
- Read the API key from environment variable `GRSAI_API_KEY`. If it is missing, ask the user to set it before making a paid/API call.
- Do not print the full `Authorization` header or raw request headers. If an error includes secrets, redact them before reporting.
- Treat each generation as a potentially paid external API call. If the request is ambiguous, high-resolution, repeated, or uses `-vip`/4K models, confirm intent before calling.
- Do not upload local/reference images unless the user provided them for this task or explicitly confirmed they should be used.
- If the user says price/cost is important, choose the lowest-cost model/parameters that satisfy the request and state the tradeoff before calling.

PowerShell key check:

```powershell
if (-not $env:GRSAI_API_KEY) {
  throw 'Missing GRSAI_API_KEY. Set it before calling Grsai.'
}
```

## API Basics

- Global endpoint: `https://grsaiapi.com`
- China endpoint: `https://grsai.dakka.com.cn`
- Auth header: `Authorization: Bearer $env:GRSAI_API_KEY`
- Detailed API reference: `references/grsai-api-docs.md`

Prefer `POST /v1/api/generate` for normal skill usage. Use `/v1/images/generations` only when the caller explicitly needs the OpenAI-compatible format.

## API Calibration Source

- **Authoritative API reference**: [https://qmy27nhsd9.apifox.cn/](https://qmy27nhsd9.apifox.cn/)
- When this skill's recorded models, parameters, ratios, or response format conflict with the Apifox document, **the document wins**.
- On any detected drift, update this skill to match the document before making further calls.
- The Apifox document may be newer than this skill; treat it as the live source of truth for endpoint paths, field names, supported models, and allowed values.

## Model And Size Selection

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

Price-sensitive routing:

- For drafts, quick previews, or "便宜点/省钱/低成本", prefer `nano-banana-fast` at `1K`.
- If the user needs better instruction following but remains cost-sensitive, use `gpt-image-2` at `1024x1024` or a supported 1K size.
- Avoid `-vip`, `-pro-cl`, 4K, and repeated generations unless the user confirms quality matters more than cost.
- Do not choose extreme-ratio `-cl` models just for normal `16:9`, `9:16`, or `1:1` outputs.
- When the model's listed price is the same across 1K/2K/4K, still prefer the smallest size that satisfies the user because availability, latency, and downstream download/preview cost can differ.

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

Compatibility rules:

- `nano-banana` models use `aspectRatio` plus optional `imageSize`.
- Supported `aspectRatio` values per the Apifox document: `auto`, `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `5:4`, `4:5`, `21:9`.
- `nano-banana-2` series additionally supports extreme ratios: `1:4`, `4:1`, `1:8`, `8:1`.
- `gpt-image-2` accepts a ratio such as `16:9` or a 1K pixel value such as `1024x1024`.
- `gpt-image-2-vip` requires pixel dimensions such as `2048x2048`; do not send ratios like `16:9`.
- For `gpt-image-2-vip`, ensure width/height are both multiples of 16, max side <= 3840, long/short ratio <= 3:1, and total pixels between 655360 and 8294400.
- For `/v1/images/generations`, reference images use field `image`; for `/v1/api/generate`, reference images use field `images`.

## Ask Before Calling

Ask a short clarifying question when:

1. The user has not provided concrete visual content.
2. The user mentions multiple output scenarios with conflicting ratios.
3. The requested ratio/resolution is unsupported.
4. The user asks for "best", "highest", 4K, `-vip`, or many images and cost may matter.
5. The user provides reference images and it is unclear whether to use them as source material.

Otherwise infer defaults and proceed.

## Prompt Handling

- Preserve the user's visual intent.
- If the prompt is very short, expand it to 2-3 concise English sentences with style, lighting, composition, and subject details.
- Do not add copyrighted characters, real-person likeness, logos, or sensitive content unless the user clearly requested something permitted and appropriate.
- If the service returns `violation`, ask the user to revise the prompt instead of trying to bypass the policy.

## Execution Environment

- The runtime Bash tool is Git Bash, **not** PowerShell. Do not paste PowerShell snippets directly into Bash.
- Write the script to a temporary `.ps1` file, then execute with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>`.
- Always delete the temporary `.ps1` file after use.

## Call Pattern

Use structured JSON through PowerShell hashtables; do not concatenate JSON strings.

**Default to `replyType: 'async'`** — synchronous calls often time out on 1K+ images. Use `replyType: 'json'` only for very fast drafts or when the caller explicitly wants a blocking call.

### Standard async template

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

Then display the result in Markdown using the returned `localPath` with forward slashes or an absolute Windows path.

## Codex Preview Compatibility

For generated image URLs:

1. Validate that the response contains at least one URL in `results[].url` or `data[].url`.
2. Show the remote result with Markdown:

```markdown
![生成结果](https://example.com/result.png)
```

3. For more reliable Codex desktop preview, also download the image to the current workspace or a user-relevant output folder and display it with an absolute path (the standard async template already does this):

```markdown
![生成结果](D:/ObjectCode/grsai-api/grsai-output.png)
```

4. Use forward slashes or a full absolute Windows path in Markdown image tags. Do not use relative paths for final preview images.
5. If the result is a video URL, return the URL and, when downloaded locally, display it with an absolute path Markdown link instead of pretending it is an image.

## Error Handling

| Case | Action |
|---|---|
| Missing `GRSAI_API_KEY` | Ask user to set it; do not call API |
| 400 / parameter error | Show the model, ratio/size, and sanitized error |
| `violation` status | Ask user to revise the prompt |
| 401 | Tell user the key is invalid/expired; do not reveal the key |
| 429 | Wait and retry once with backoff, or ask user to retry later |
| Timeout | Switch to the standard async template above; do not retry synchronous blindly |
| 5xx | Report transient service failure and keep the task ID if available |

When reporting errors, include only sanitized `id`, `status`, and `error` fields.
