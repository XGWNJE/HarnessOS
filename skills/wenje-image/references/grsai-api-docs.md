# Grsai API 接口文档

> 来源: https://qmy27nhsd9.apifox.cn  
> 更新时间: 2026-05-06

## 实测校准（2026-09-13）

以下几处与上游文档不一致，以实测为准；写代码前先看这里。

| 项 | 文档说法 | 实测行为 |
|---|---|---|
| 密钥无效 | HTTP 401 | `/v1/api/generate` + `replyType=json` → **HTTP 400** `{"id":"","status":"failed","error":"apikey error"}`；+ `replyType=async` → **HTTP 200 且响应体为空** |
| `/v1/images/generations` 密钥无效 | HTTP 401 | **HTTP 400** `{"error":{"message":"apikey error"}}` |
| `/v1/chat/completions` 密钥无效 | — | **HTTP 400** `{"error":{"message":"apikey error","type":"rix_api_error"}}` |
| 查询结果接口的鉴权 | 需 Authorization | 实测**不校验密钥**：`?id=probe` 直接返回 404 `{"error":"result not exist, valid for 2 hours"}`。所以不能用它判断密钥是否有效 |
| 结果 URL 有效期 | 未说明 | **仅 2 小时**（由上面的 404 消息得出）。必须下载落盘 |
| 是否退费 | 未说明 | 仅系统错误退积分；**内容违规不退** |

零费用的鉴权探测方式：用 `/v1/chat/completions` 配一个不存在的模型名，密钥无效会命中 `apikey error`，密钥有效则停在模型不存在，不产生生成费用。

## 基础信息

- **全球节点**: `https://grsaiapi.com`
- **国内节点**: `https://grsai.dakka.com.cn`
- **API Key 获取**: https://grsai.ai/zh/dashboard/api-keys
- **认证方式**: Header `Authorization: Bearer sk-xxxxxxxxxxx`

---

## 目录

1. [nano-banana接口](#1-nano-banana接口) — `POST /v1/api/generate`
2. [gpt-image-2接口](#2-gpt-image-2接口) — `POST /v1/api/generate`
3. [异步生成结果查询接口](#3-异步生成结果查询接口) — `GET /v1/api/result`
4. [/v1/chat/completions](#4-v1chatcompletions) — `POST /v1/chat/completions`
5. [/v1/images/generations](#5-v1imagesgenerations) — `POST /v1/images/generations`

---

## 1. nano-banana接口

**POST** `/v1/api/generate`

- 全球节点: `https://grsaiapi.com/v1/api/generate`
- 国内节点: `https://grsai.dakka.com.cn/v1/api/generate`

### 请求参数

#### Header 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | `Bearer sk-xxxxxxxxxxx`，API Key 获取: https://grsai.ai/zh/dashboard/api-keys |

#### Body 参数 (application/json)

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 是 | 模型名称 |
| prompt | string | 是 | 提示词 |
| images | array[string] | 否 | 参考图，支持 base64 与 url 链接 |
| aspectRatio | string | 否 | 图像比例 |
| imageSize | string | 否 | 分辨率: `1K`、`2K`、`4K` |
| replyType | string | 否 | 回复类型: `json`、`stream`、`async` |

##### model 支持的模型

- `nano-banana`
- `nano-banana-fast`
- `nano-banana-2`
- `nano-banana-2-cl`
- `nano-banana-2-4k-cl`
- `nano-banana-pro`
- `nano-banana-pro-cl`
- `nano-banana-pro-vip`
- `nano-banana-pro-4k-vip`

##### aspectRatio 支持的比例

- `auto`、`1:1`、`16:9`、`9:16`、`4:3`、`3:4`、`3:2`、`2:3`、`5:4`、`4:5`、`21:9`
- nano-banana-2 系列额外支持: `1:4`、`4:1`、`1:8`、`8:1`

##### replyType 说明

| 值 | 说明 |
|----|------|
| `json` | 返回 json |
| `stream` | 返回 stream |
| `async` | 异步轮询，结果通过 [异步生成结果查询接口](#3-异步生成结果查询接口) 获取 |

### 请求示例

```json
{
  "model": "nano-banana-2",
  "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
  "images": [],
  "aspectRatio": "1:1",
  "imageSize": "1K",
  "replyType": "json"
}
```

```bash
curl --location 'https://grsaiapi.com/v1/api/generate' \
  --header 'Authorization: Bearer sk-xxxxxxxxxxx' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "nano-banana-2",
    "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
    "images": [],
    "aspectRatio": "1:1",
    "imageSize": "1K",
    "replyType": "json"
  }'
```

### 响应

#### 200 成功

```json
{
  "id": "14-5f3cf761-a4bb-486a-8016-77f490998f80",
  "status": "succeeded",
  "results": [
    {
      "url": "https://file1.aitohumanize.com/file/fcdd2d07449d438d9d69d450f5626976.png"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 任务 ID |
| status | string | 状态: `running`(进行中)、`violation`(违规)、`succeeded`(生成成功)、`failed`(任务失败) |
| results | array | 结果数组，每项含 `url`(图片/视频链接) |
| progress | integer | 进度 0~100 |
| error | string | 报错信息 |

#### 200 异步生成返回结果 (replyType=async)

```json
{
  "id": "6-f671fc51-d5d7-4eff-a1c7-26e612fe08ab",
  "status": "running"
}
```

> 通过该 id 调用 [异步结果查询接口](#3-异步生成结果查询接口) 获取最终结果。

#### 400 报错

```json
{
  "id": "12-1f771fbf-f23a-4b89-a7d0-a98ba9862edb",
  "status": "failed",
  "error": "generate failed"
}
```

---

## 2. gpt-image-2接口

**POST** `/v1/api/generate`

- 全球节点: `https://grsaiapi.com/v1/api/generate`
- 国内节点: `https://grsai.dakka.com.cn/v1/api/generate`

### 请求参数

#### Header 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | `Bearer sk-xxxxxxxxxxx` |

#### Body 参数 (application/json)

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 是 | 模型名称 |
| prompt | string | 是 | 提示词 |
| images | array[string] | 否 | 参考图，支持 base64 与 url 链接 |
| aspectRatio | string | 否 | 分辨率/比例 |
| replyType | string | 否 | 回复类型: `json`、`stream`、`async` |

##### model 支持的模型

- `gpt-image-2`
- `gpt-image-2-vip`

##### aspectRatio 说明

- **gpt-image-2**: 支持比例（如 `16:9`）或 1K 像素值（如 `1024x1024`）
- **gpt-image-2-vip**: 支持 1-4K 像素值（如 `1024x1024`、`2048x2048`），不支持比例

**自定义像素值约束（仅限 vip 模型）:**
- 最大边长 ≤ 3840px
- 两条边都必须是 16 的倍数
- 长边与短边之比 ≤ 3:1
- 总像素数 ≥ 655,360 且 ≤ 8,294,400

##### gpt-image-2-vip 比例参考（1K、2K、4K）

| 比例 | 1K | 2K | 4K |
|------|-----|-----|-----|
| 1:1 | 1024x1024 | 2048x2048 | 2880x2880 |
| 16:9 | 1280x720 | 2048x1152 | 3840x2160 |
| 9:16 | 720x1280 | 1152x2048 | 2160x3840 |
| 4:3 | 1152x864 | 2304x1728 | 3264x2448 |
| 3:4 | 864x1152 | 1728x2304 | 2448x3264 |
| 3:2 | 1536x1024 | 2048x1360 | 3504x2336 |
| 2:3 | 1024x1536 | 1360x2048 | 2336x3504 |
| 5:4 | 1120x896 | 2240x1792 | 3200x2560 |
| 4:5 | 896x1120 | 1792x2240 | 2560x3200 |
| 21:9 | 1456x624 | 2912x1248 | 3840x1648 |
| 9:21 | 624x1456 | 1248x2912 | 1648x3840 |
| 1:3 | 688x2048 | 1280x3840 | - |
| 3:1 | 2048x688 | 3840x1280 | - |
| 2:1 | 1536x768 | 3072x1536 | 3840x1920 |
| 1:2 | 768x1536 | 1536x3072 | 1920x3840 |

##### gpt-image-2 比例参考

| 比例 | 分辨率 |
|------|--------|
| 1:1 | 1024x1024 |
| 16:9 | 1672x941 |
| 9:16 | 941x1672 |
| 4:3 | 1443x1090 |
| 3:4 | 1090x1443 |
| 3:2 | 1536x1024 |
| 2:3 | 1024x1536 |
| 5:4 | 1408x1120 |
| 4:5 | 1120x1408 |
| 21:9 | 1920x832 |
| 9:21 | 832x1920 |
| 1:2 | 896x1792 |
| 2:1 | 1792x896 |

### 请求示例

```json
{
  "model": "gpt-image-2",
  "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
  "images": [],
  "aspectRatio": "1024x1024",
  "replyType": "json"
}
```

### 响应

同 [nano-banana接口响应](#响应)（共享相同的响应结构）。

---

## 3. 异步生成结果查询接口

**GET** `/v1/api/result`

- 全球节点: `https://grsaiapi.com/v1/api/result`
- 国内节点: `https://grsai.dakka.com.cn/v1/api/result`

### 请求参数

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | 否 | 任务 ID，例: `1-6634fd9a-3086-4d92-9436-69e86fd23bf8` |

#### Header 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | `Bearer sk-xxxxxxxxxxx` |

### 请求示例

```bash
curl --location 'https://grsaiapi.com/v1/api/result?id=1-6634fd9a-3086-4d92-9436-69e86fd23bf8' \
  --header 'Authorization: Bearer sk-xxxxxxxxxxx'
```

### 响应

#### 200 成功

```json
{
  "id": "14-5f3cf761-a4bb-486a-8016-77f490998f80",
  "status": "succeeded",
  "results": [
    {
      "url": "https://file1.aitohumanize.com/file/fcdd2d07449d438d9d69d450f5626976.png"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 任务 ID |
| status | string | 状态: `running`(进行中)、`violation`(违规)、`succeeded`(生成成功)、`failed`(任务失败) |
| results | array | 结果数组，每项含 `url`(图片/视频链接) |
| progress | integer | 进度 0~100 |
| error | string | 报错信息 |

#### 400 报错

```json
{
  "id": "12-1f771fbf-f23a-4b89-a7d0-a98ba9862edb",
  "status": "failed",
  "error": "generate failed"
}
```

---

## 4. /v1/chat/completions

**POST** `/v1/chat/completions`

- 全球节点: `https://grsaiapi.com/v1/chat/completions`
- 国内节点: `https://grsai.dakka.com.cn/v1/chat/completions`

### 请求参数

#### Header 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | `Bearer sk-xxxxxxxxxxx` |

#### Body 参数 (application/json)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| model | string | 是 | - | 模型名称，支持所有模型 |
| messages | array | 是 | - | 消息数组 |
| stream | boolean | 是 | `true` | 是否流式返回 |

##### messages 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| role | string | 角色，如 `user` |
| content | string/array | 提示词内容，支持文本或多模态格式 |

### 请求示例

#### 文字提问

```json
{
  "model": "gemini-3.1-pro",
  "stream": false,
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ]
}
```

#### 传递图片提问

```json
{
  "model": "gemini-3.1-pro",
  "stream": false,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "这张图片内容是什么"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://xxxxxxx.png"
          }
        }
      ]
    }
  ]
}
```

### 响应

#### 200 成功 (stream=false)

```json
{
  "id": "1-c1e4db8a-fbd4-42a8-8bfa-4a7679416301",
  "object": "chat.completion",
  "created": 1777896910,
  "model": "gemini-3.1-pro",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么我可以帮你的吗？"
      },
      "finish_reason": "stop",
      "content_filter_results": {
        "hate": { "filtered": false },
        "self_harm": { "filtered": false },
        "sexual": { "filtered": false },
        "violence": { "filtered": false }
      }
    }
  ],
  "system_fingerprint": "",
  "usage": {
    "prompt_tokens": 2,
    "completion_tokens": 213,
    "total_tokens": 215,
    "prompt_tokens_details": null,
    "completion_tokens_details": null
  }
}
```

#### 200 stream 流响应 (stream=true)

响应格式为 SSE (Server-Sent Events)，每次返回一个 `data:` 块:

```json
data: {
    "id": "1-c1e4db8a-fbd4-42a8-8bfa-4a7679416301",
    "object": "chat.completion.chunk",
    "created": 1777896911,
    "model": "gemini-3.1-pro",
    "choices": [
        {
            "index": 0,
            "delta": {
                "content": "有什么我可以帮你的吗？",
                "role": "assistant"
            },
            "finish_reason": null,
            "content_filter_results": { ... }
        }
    ],
    "system_fingerprint": ""
}
```

最后一个 chunk 包含 `finish_reason: "stop"` 和 `usage` 信息。

---

## 5. /v1/images/generations

**POST** `/v1/images/generations`

- 全球节点: `https://grsaiapi.com/v1/images/generations`
- 国内节点: `https://grsai.dakka.com.cn/v1/images/generations`

### 请求参数

#### Header 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 否 | `Bearer sk-xxxxxxxxxxx` |

#### Body 参数 (application/json)

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 是 | 模型名称，支持所有图片生成模型 |
| prompt | string | 是 | 提示词 |
| image | array[string] | 否 | 参考图，支持 base64 与 url 链接 |
| size | string | 否 | 比例/分辨率，如 `1024x1024` |
| response_format | string | 否 | 响应格式，如 `url` |

##### size 说明

同 [gpt-image-2 的 aspectRatio 说明](#aspectratio-说明)，支持比例和自定义像素值。

### 请求示例

```json
{
  "model": "gpt-image-2",
  "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
  "image": [],
  "size": "1024x1024",
  "response_format": "url"
}
```

### 响应

#### 200 成功

```json
{
  "created": 1777689832,
  "data": [
    {
      "url": "https://file4.aitohumanize.com/file/dfa13fe60e7649e88f46037b968b54a3.png"
    }
  ],
  "usage": {
    "total_tokens": 6267,
    "input_tokens": 17,
    "output_tokens": 6250,
    "input_tokens_details": {}
  }
}
```

#### 400 报错

```json
{
  "error": {
    "message": "generation failed"
  }
}
```

---

## 通用状态码

> 下表是上游文档的原始说法；密钥相关的 401 已被实测推翻，见文首「实测校准」。

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功（异步模式下密钥无效也是 200 + 空响应体） |
| 400 | 请求参数错误 / 生成失败 / **apikey error** |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

## 通用任务状态

| 状态 | 说明 |
|------|------|
| `running` | 进行中 |
| `violation` | 违规 |
| `succeeded` | 生成成功 |
| `failed` | 任务失败 |
