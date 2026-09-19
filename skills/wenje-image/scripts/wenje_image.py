#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wenje-image 引擎：密钥配置、出图调用、本地设置页、用量记录。

单文件、仅依赖标准库（Pillow 可选，仅用于 MCP 预览缩略图）。

子命令：
    setup     启动本地设置页（127.0.0.1），由用户在浏览器里填密钥，不走对话
    status    密钥来源、端点连通性、鉴权有效性、输出目录、今日用量
    generate  一次调用走完提交→轮询→下载→命名，输出机器可读结果
    install   把 MCP server 注册到本机 Agent 配置（备份后合并）
    mcp       以 stdio MCP server 运行（见 wenje_mcp.py）

密钥永不出现在参数、日志与标准输出：只从配置文件或 GRSAI_API_KEY 读取。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "2.4.0"
SKILL_NAME = "wenje-image"

CONFIG_DIR = Path(os.environ.get("WENJE_IMAGE_HOME") or (Path.home() / ".wenje-image"))
CONFIG_PATH = CONFIG_DIR / "config.json"
USAGE_PATH = CONFIG_DIR / "usage.jsonl"

KEY_ENV = "GRSAI_API_KEY"
KEY_ENV_ALT = "WENJE_IMAGE_API_KEY"
DEFAULT_ENDPOINT = "https://grsaiapi.com"
CN_ENDPOINT = "https://grsai.dakka.com.cn"
KEY_PAGE = "https://grsai.ai/zh/dashboard/api-keys"
MODELS_PAGE = "https://grsai.ai/zh/dashboard/models"

# 退出码：让调用方无需解析文本即可分支
EXIT_OK = 0
EXIT_PARAM = 2
EXIT_CONFIG = 3
EXIT_AUTH = 4
EXIT_PAYMENT = 5
EXIT_VIOLATION = 6
EXIT_NETWORK = 7
EXIT_TIMEOUT = 8
EXIT_SERVER = 9

# ---------------------------------------------------------------- 模型目录
#
# credits 与价格摘自 Grsai 公开模型列表（2026-09），只作路由参考，不是报价。
#   widths: 该模型 aspectRatio 接受哪些比例键
#   sizes:  该模型是否接受 imageSize（1K/2K/4K）
#   pixels: aspectRatio 需换算成像素串（非比例串）
RATIO_STANDARD = ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"]
RATIO_EXTREME = ["1:4", "4:1", "1:8", "8:1"]

# gpt-image-2-vip 只接受像素串，按文档的比例表换算
VIP_PIXELS = {
    "1:1": {"1K": "1024x1024", "2K": "2048x2048", "4K": "2880x2880"},
    "16:9": {"1K": "1280x720", "2K": "2048x1152", "4K": "3840x2160"},
    "9:16": {"1K": "720x1280", "2K": "1152x2048", "4K": "2160x3840"},
    "4:3": {"1K": "1152x864", "2K": "2304x1728", "4K": "3264x2448"},
    "3:4": {"1K": "864x1152", "2K": "1728x2304", "4K": "2448x3264"},
    "3:2": {"1K": "1536x1024", "2K": "2048x1360", "4K": "3504x2336"},
    "2:3": {"1K": "1024x1536", "2K": "1360x2048", "4K": "2336x3504"},
    "5:4": {"1K": "1120x896", "2K": "2240x1792", "4K": "3200x2560"},
    "4:5": {"1K": "896x1120", "2K": "1792x2240", "4K": "2560x3200"},
    "21:9": {"1K": "1456x624", "2K": "2912x1248", "4K": "3840x1648"},
    "9:21": {"1K": "624x1456", "2K": "1248x2912", "4K": "1648x3840"},
    "1:3": {"1K": "688x2048", "2K": "1280x3840"},
    "3:1": {"1K": "2048x688", "2K": "3840x1280"},
    "2:1": {"1K": "1536x768", "2K": "3072x1536", "4K": "3840x1920"},
    "1:2": {"1K": "768x1536", "2K": "1536x3072", "4K": "1920x3840"},
}

# 限定模型集：只有下列 5 个模型可用，其余一律拒绝。
#   sizes  该模型**实际支持**的 imageSize 档位——不是可选项，是能力事实。
#          用户要了模型不支持的档位时，按这张表落到最接近的受支持档位，绝不硬塞。
#   prices 取自 Grsai 控制台模型页（2026-09-13 核验），易变，成本决策前重新核验。
MODELS = {
    "gpt-image-2.5": {
        "credits": 600, "price": "￥0.03", "sizes": ["1K"],
        "ratios": sorted(VIP_PIXELS) + ["auto"], "pixels": True,
    },
    "gpt-image-2.5-flare": {
        "credits": 2000, "price": "￥0.10", "sizes": ["1K", "2K", "4K"],
        "ratios": sorted(VIP_PIXELS) + ["auto"], "pixels": True,
    },
    "gpt-image-2.5-sunburst": {
        "credits": 2400, "price": "￥0.12", "sizes": ["1K", "2K", "4K"],
        "ratios": sorted(VIP_PIXELS) + ["auto"], "pixels": True,
    },
    "nano-banana-2": {
        "credits": 1200, "price": "￥0.06", "sizes": ["1K", "2K", "4K"],
        "ratios": RATIO_STANDARD + RATIO_EXTREME,
    },
    "nano-banana-pro-4k-vip": {
        "credits": 18000, "price": "￥0.90", "sizes": ["4K"],
        "ratios": RATIO_STANDARD,
    },
}

# 用户没点名模型时，按任务档位挑：draft 最便宜、standard 日常、premium 质量优先。
TIER_MODEL = {
    "draft": "gpt-image-2.5",
    "standard": "gpt-image-2.5-flare",
    "premium": "gpt-image-2.5-sunburst",
}

# 极端比例只有 nano-banana-2 支持；未点名模型时改用它，不报错。
EXTREME_MODEL = "nano-banana-2"

SIZE_RANK = {"1K": 1, "2K": 2, "4K": 3}

# 常见场景的比例与尺寸默认值
SCENE_PRESETS = {
    "avatar": ("1:1", "1K"),
    "wallpaper-phone": ("9:16", "2K"),
    "wallpaper-desktop": ("16:9", "2K"),
    "social": ("1:1", "1K"),
    "cover": ("16:9", "1K"),
    "banner": ("21:9", "1K"),
    "poster": ("2:3", "2K"),
}


class WenjeError(Exception):
    """带退出码与脱敏消息的调用失败。"""

    def __init__(self, message: str, code: int = EXIT_SERVER, detail: str = ""):
        super().__init__(message)
        self.code = code
        self.detail = detail


# ---------------------------------------------------------------- 基础工具

def force_utf8() -> None:
    """控制台默认代码页 936 会让中文乱码，能改则改成 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def redact(text: str, secret: str | None) -> str:
    """任何要落盘或回显的文本都先过一遍，防止密钥被服务端错误信息带出来。"""
    out = str(text)
    if secret and len(secret) >= 8:
        out = out.replace(secret, secret[:6] + "***")
    return re.sub(r"(sk-[A-Za-z0-9_\-]{4})[A-Za-z0-9_\-]{6,}", r"\1***", out)


def mask_key(key: str | None) -> str:
    if not key:
        return "(未配置)"
    if len(key) <= 12:
        return key[:3] + "***"
    return f"{key[:6]}...{key[-4:]}"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(text: str, fallback: str = "image", maxlen: int = 28) -> str:
    """把提示词压成可读文件名片段，保留中文，剔除 Windows 非法字符。"""
    s = re.sub(r"[\x00-\x1f]", "", text or "")
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-{2,}", "-", s).strip("-. ")
    s = s[:maxlen].strip("-. ")
    return s or fallback


# ---------------------------------------------------------------- 配置存取

def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, CONFIG_PATH)
    try:  # POSIX 下收紧到仅本人可读；Windows 由用户目录 ACL 承担
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def resolve_key(cfg: dict) -> tuple[str | None, str]:
    """返回 (密钥, 来源)。环境变量优先，便于 CI 或临时覆盖。"""
    for name in (KEY_ENV_ALT, KEY_ENV):
        value = os.environ.get(name, "").strip()
        if value:
            return value, f"环境变量 {name}"
    key = (cfg.get("api_key") or "").strip()
    if key:
        return key, "配置文件"
    return None, "(未配置)"


def resolve_endpoint(cfg: dict) -> str:
    return (os.environ.get("GRSAI_ENDPOINT") or cfg.get("endpoint") or DEFAULT_ENDPOINT).rstrip("/")


def default_output_dir(cfg: dict) -> Path:
    configured = cfg.get("output_dir")
    if configured:
        return Path(configured).expanduser()
    pictures = Path.home() / "Pictures"
    base = pictures if pictures.is_dir() else Path.home()
    return base / SKILL_NAME


def log_usage(record: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with USAGE_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_usage(day: str | None = None) -> list[dict]:
    if not USAGE_PATH.is_file():
        return []
    day = day or datetime.now().strftime("%Y-%m-%d")
    out = []
    try:
        for line in USAGE_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(rec.get("at", "")).startswith(day):
                out.append(rec)
    except OSError:
        return []
    return out


# ---------------------------------------------------------------- HTTP 层

def http_json(url: str, payload: dict | None, headers: dict, timeout: int, method: str = "POST"):
    """返回 (status, body_text)。HTTP 错误码不抛异常——Grsai 用 400 表达业务失败。"""
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise WenjeError(f"网络不可达：{exc.reason}", EXIT_NETWORK)


def parse_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def api_error_message(body: dict) -> str:
    err = body.get("error")
    if isinstance(err, dict):
        return str(err.get("message") or err)
    if isinstance(err, str):
        return err
    return str(body.get("message") or body.get("msg") or "")


def probe_key(key: str, endpoint: str, timeout: int = 20) -> tuple[bool, str]:
    """用不存在的模型名探一次鉴权层：鉴权失败才有 apikey error，成功路径不产生费用。"""
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": "__wenje_probe__", "stream": False, "messages": [{"role": "user", "content": "hi"}]}
    try:
        status, text = http_json(f"{endpoint}/v1/chat/completions", payload, headers, timeout)
    except WenjeError as exc:
        return False, f"无法验证（{exc}）"
    body = parse_json(text)
    message = api_error_message(body).lower()
    if "apikey" in message or "api key" in message or "unauthor" in message or "invalid key" in message:
        return False, "密钥无效"
    if status in (401, 403):
        return False, f"密钥被拒（HTTP {status}）"
    if status == 200:
        return True, "密钥有效（探测模型意外返回成功）"
    return True, f"鉴权层已接受（HTTP {status}：{redact(message, key)[:120]}）"


# ---------------------------------------------------------------- 出图流程

def encode_reference(path: str) -> str:
    """参考图转 data URI。只在调用方明确给出本地文件时才会走到这里。"""
    p = Path(path).expanduser()
    if not p.is_file():
        raise WenjeError(f"参考图不存在：{path}", EXIT_PARAM)
    suffix = p.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "gif": "image/gif"}.get(suffix, "image/png")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def resolve_model(tier: str | None, model: str | None, ratio: str) -> str:
    """用户点名就用它；没点名按档位挑；比例不被该档模型支持时改走支持它的模型。"""
    if model:
        if model not in MODELS:
            raise WenjeError(
                f"模型不在可用集内：{model}。可用：{', '.join(MODELS)}", EXIT_PARAM)
        return model
    chosen = TIER_MODEL.get((tier or "standard").lower())
    if not chosen:
        raise WenjeError(f"未知档位：{tier}。可用：{', '.join(TIER_MODEL)}", EXIT_PARAM)
    if ratio not in MODELS[chosen]["ratios"]:
        for name, spec in MODELS.items():
            if ratio in spec["ratios"]:
                return name
    return chosen


def resolve_size(model: str, size: str | None) -> tuple[str, str]:
    """按模型能力决定规格档位，返回 (档位, 变更说明)。

    模型原生没有的档位不会被硬塞进去——要 4K 但模型最高 2K 就落到 2K，要 1K 但模型
    只有 4K 就落到 4K。说明非空时由调用方展示，让规格变化可见，不做静默替换。
    """
    sizes = MODELS[model]["sizes"]
    want = (size or "1K").upper()
    if want in sizes:
        return want, ""
    if want not in SIZE_RANK:
        raise WenjeError(f"未知尺寸：{size}。可用：1K / 2K / 4K", EXIT_PARAM)
    chosen = min(sizes, key=lambda s: (abs(SIZE_RANK[s] - SIZE_RANK[want]), SIZE_RANK[s]))
    return chosen, f"请求 {want}，但 {model} 只支持 {'/'.join(sizes)}；已按模型能力改用 {chosen}。"


def build_payload(model: str, prompt: str, ratio: str, size: str, refs: list[str]) -> dict:
    spec = MODELS[model]
    ratio = ratio or "1:1"
    if ratio != "auto" and ratio not in spec["ratios"]:
        raise WenjeError(
            f"模型 {model} 不支持比例 {ratio}。支持：{', '.join(spec['ratios'])}", EXIT_PARAM)
    payload = {"model": model, "prompt": prompt, "images": refs, "replyType": "async"}
    if spec.get("pixels"):
        # GPT-Image 系在 Grsai 上用像素串表达规格；auto 交给服务端决定，不传该字段。
        # 像素串是比值串更宽的写法：gpt-image-2 两种都收，像素专用的通道只收像素串。
        if ratio != "auto":
            table = VIP_PIXELS.get(ratio, {})
            pixels = table.get(size)
            if not pixels:
                raise WenjeError(
                    f"模型 {model} 的 {ratio} 不支持 {size}。可选：{', '.join(table) or '无'}", EXIT_PARAM)
            payload["aspectRatio"] = pixels
    else:
        payload["aspectRatio"] = ratio
        payload["imageSize"] = size
    return payload


def submit(endpoint: str, key: str, payload: dict, timeout: int) -> str:
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    status, text = http_json(f"{endpoint}/v1/api/generate", payload, headers, timeout)
    body = parse_json(text)
    message = api_error_message(body)
    task_id = str(body.get("id") or "").strip()
    if "apikey" in message.lower():
        raise WenjeError("密钥无效或已过期，请重新运行 setup 更新密钥。", EXIT_AUTH)
    low = message.lower()
    if "balance" in low or "insufficient" in low or "余额" in message or "quota" in low:
        raise WenjeError("账户余额不足，请充值后重试。", EXIT_PAYMENT)
    if status >= 500:
        raise WenjeError(f"服务端临时故障（HTTP {status}）：{redact(message, key)[:200]}", EXIT_SERVER)
    if not task_id:
        # 实测：异步模式下密钥无效会返回 HTTP 200 + 空响应体（不是文档写的 401），
        # 直接把这个含糊结果报出去会误导调用方，所以补一次零费用鉴权探测来定性。
        if not message:
            ok, why = probe_key(key, endpoint)
            if not ok:
                raise WenjeError(f"密钥无效或已过期（{why}），请重新运行 setup 更新密钥。", EXIT_AUTH)
        raise WenjeError(
            f"提交失败（HTTP {status}）：{redact(message or text, key)[:200] or '响应为空'}", EXIT_SERVER)
    return task_id


def poll(endpoint: str, key: str, task_id: str, timeout: int, interval: float, on_tick=None) -> dict:
    headers = {"Authorization": f"Bearer {key}"}
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        time.sleep(interval)
        url = f"{endpoint}/v1/api/result?" + urllib.parse.urlencode({"id": task_id})
        status, text = http_json(url, None, headers, 60, method="GET")
        body = parse_json(text)
        if not body and status >= 400:
            # 结果只在服务端保留 2 小时，且查询失败不代表任务失败，继续等
            last = {"status": "unknown", "error": redact(text, key)[:200]}
        else:
            last = body
        state = str(last.get("status") or "running")
        if on_tick:
            on_tick(state, last.get("progress"))
        if state in ("succeeded", "failed", "violation"):
            return last
    raise WenjeError(
        f"轮询超时（{int(timeout)}s），任务 {task_id} 仍在运行。可稍后用 status 命令查询同一 id。",
        EXIT_TIMEOUT)


def extract_url(result: dict) -> str:
    for item in (result.get("results") or []):
        if isinstance(item, dict) and item.get("url"):
            return str(item["url"])
        if isinstance(item, str) and item.startswith("http"):
            return item
    for item in (result.get("data") or []):
        if isinstance(item, dict) and item.get("url"):
            return str(item["url"])
    return ""


def download(url: str, out_dir: Path, stem: str, timeout: int = 180) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm"):
        ext = ".png"
    target = out_dir / f"{stem}{ext}"
    if target.exists():
        target = out_dir / f"{stem}-{secrets.token_hex(2)}{ext}"
    req = urllib.request.Request(url, headers={"User-Agent": f"{SKILL_NAME}/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, target.open("wb") as fh:
            while chunk := resp.read(65536):
                fh.write(chunk)
    except urllib.error.URLError as exc:
        raise WenjeError(f"结果下载失败：{exc.reason}", EXIT_NETWORK)
    return target


def is_video(path: Path) -> bool:
    return path.suffix.lower() in (".mp4", ".webm")


def run_generation(args, cfg: dict, on_tick=None) -> dict:
    """提交→轮询→下载→命名，返回结构化结果。"""
    key, key_source = resolve_key(cfg)
    if not key:
        raise WenjeError(
            f"未配置 API 密钥。请运行：python {Path(__file__).name} setup", EXIT_CONFIG)
    endpoint = resolve_endpoint(cfg)
    ratio = args.ratio
    size = args.size
    if args.scene:
        scene_ratio, scene_size = SCENE_PRESETS[args.scene]
        ratio = ratio or scene_ratio
        size = size or scene_size
    ratio = ratio or cfg.get("default_ratio") or "1:1"
    size = (size or cfg.get("default_size") or "1K").upper()
    model = resolve_model(getattr(args, "tier", None) or cfg.get("default_tier"), args.model, ratio)
    size, size_note = resolve_size(model, size)

    refs = [encode_reference(p) for p in (args.ref or [])]
    payload = build_payload(model, args.prompt, ratio, size, refs)
    estimate = MODELS[model].get("credits", 0)

    if args.dry_run:
        preview = dict(payload)
        preview["images"] = [f"<{len(r)} chars data uri>" for r in refs]
        return {"dry_run": True, "endpoint": endpoint, "key_source": key_source,
                "model": model, "credits": estimate, "estimated_price": MODELS[model].get("price"),
                "sizes_supported": MODELS[model]["sizes"], "size_note": size_note, "payload": preview}

    task_id = submit(endpoint, key, payload, args.timeout)
    result = poll(endpoint, key, task_id, args.timeout, args.poll_interval, on_tick)
    state = str(result.get("status") or "unknown")
    if state != "succeeded":
        detail = redact(result.get("error") or json.dumps(result, ensure_ascii=False), key)[:300]
        log_usage({"at": datetime.now().isoformat(timespec="seconds"), "model": model,
                   "status": state, "credits": 0, "task": task_id})
        code = EXIT_VIOLATION if state == "violation" else EXIT_SERVER
        hint = "内容被判定违规，请调整提示词后重试。" if state == "violation" else f"生成失败：{detail}"
        raise WenjeError(hint, code, detail=detail)

    url = extract_url(result)
    if not url:
        raise WenjeError(f"任务成功但响应中没有结果 URL：{redact(json.dumps(result, ensure_ascii=False), key)[:200]}",
                         EXIT_SERVER)

    out_dir = Path(args.out).expanduser() if args.out else default_output_dir(cfg)
    stem = args.name or slugify(args.prompt)
    if not args.no_download:
        path = download(url, out_dir, f"{stem}-{now_stamp()}")
    else:
        path = None

    record = {"at": datetime.now().isoformat(timespec="seconds"), "model": model, "status": "succeeded",
              "credits": estimate, "task": task_id, "ratio": ratio, "size": size,
              "path": str(path) if path else ""}
    log_usage(record)
    return {"task": task_id, "status": state, "model": model, "ratio": ratio, "size": size,
            "size_note": size_note, "url": url, "path": str(path) if path else "", "credits": estimate,
            "estimated_price": MODELS[model].get("price"), "kind": "video" if path and is_video(path) else "image"}


def render_result(result: dict) -> str:
    """给人看的输出：本机文件用绝对路径 Markdown 直接渲染，视频不假装成图片。"""
    path = result.get("path") or ""
    posix = Path(path).as_posix() if path else ""
    lines = [f"模型 {result['model']} · {result['ratio']} · {result['size']} · {result.get('estimated_price') or '见控制台'}/张"]
    if result.get("size_note"):
        lines.append(f"规格变更：{result['size_note']}")
    if path and result.get("kind") == "video":
        lines.append(f"[生成结果]({posix})")
    elif path:
        lines.append(f"![生成结果]({posix})")
    else:
        lines.append(f"![生成结果]({result['url']})")
    if path:
        lines.append(f"文件：{posix}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 设置页 UI

SETUP_HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wenje Image 配置</title>
<style>
 :root{color-scheme:dark}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
      background:#14121b;color:#e9e6f2;font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
 .card{width:min(560px,92vw);background:#1d1a26;border:1px solid #302b3f;border-radius:16px;padding:28px 30px 24px;
       box-shadow:0 18px 50px rgba(0,0,0,.45)}
 h1{margin:0 0 4px;font-size:19px}
 .sub{margin:0 0 22px;color:#9d97b3;font-size:13px}
 label{display:block;margin:16px 0 6px;font-size:13px;color:#c3bdd6}
 input,select{width:100%;padding:10px 12px;border-radius:9px;border:1px solid #3a3549;background:#14121b;
              color:#e9e6f2;font-size:14px;font-family:inherit}
 input:focus,select:focus{outline:none;border-color:#9373ee}
 .row{display:flex;gap:10px;align-items:center}
 .row>*{flex:1}
 .hint{color:#8b85a0;font-size:12px;margin-top:6px}
 .hint a{color:#a992ff}
 button{margin-top:22px;width:100%;padding:12px;border:0;border-radius:10px;background:#9373ee;color:#fff;
        font-size:15px;font-weight:600;cursor:pointer}
 button:hover{background:#a184f5}
 button:disabled{opacity:.6;cursor:default}
 .msg{margin-top:16px;padding:11px 13px;border-radius:9px;font-size:13px;display:none}
 .msg.ok{display:block;background:#14301f;border:1px solid #2c6b43;color:#8ee2ac}
 .msg.err{display:block;background:#331a1e;border:1px solid #7a3040;color:#f2a3b2}
 .msg.wait{display:block;background:#241f33;border:1px solid #4a4166;color:#c0b6e0}
 .foot{margin-top:18px;color:#6f6985;font-size:12px;text-align:center}
</style></head><body>
<div class="card">
  <h1>Wenje Image 配置</h1>
  <p class="sub">密钥只写入本机 __CONFIG_HINT__，不出现在对话、命令或日志里。</p>
  <form id="f" method="post" action="__ACTION__">
    <input type="hidden" name="csrf" value="__CSRF__">
    <label for="key">Grsai API 密钥</label>
    <div class="row">
      <input id="key" name="api_key" type="password" autocomplete="off" spellcheck="false"
             placeholder="sk-..." value="__KEY_PLACEHOLDER__">
      <button type="button" id="peek" style="flex:0 0 74px;margin:0;padding:10px;font-size:13px;background:#2d2840">显示</button>
    </div>
    <div class="hint">还没有密钥？<a href="__KEY_PAGE__" target="_blank" rel="noreferrer">去 Grsai 控制台创建</a>（__KEY_PAGE__）</div>

    <label for="endpoint">接入节点</label>
    <select id="endpoint" name="endpoint">
      <option value="__EP_GLOBAL__">全球 grsaiapi.com</option>
      <option value="__EP_CN__">国内 grsai.dakka.com.cn</option>
    </select>

    <label for="tier">默认档位</label>
    <select id="tier" name="default_tier">
      <option value="draft">draft — 便宜快速（nano-banana-fast）</option>
      <option value="standard">standard — 均衡默认（gpt-image-2）</option>
      <option value="premium">premium — 更高质量（nano-banana-pro）</option>
    </select>

    <label for="out">默认输出目录</label>
    <input id="out" name="output_dir" type="text" value="__OUT_DIR__" spellcheck="false">

    <button type="submit" id="go">验证并保存</button>
  </form>
  <div class="msg" id="m"></div>
  <div class="foot">此页面只监听本机 127.0.0.1，保存成功后自动退出。</div>
</div>
<script>
 const f=document.getElementById('f'), go=document.getElementById('go'), m=document.getElementById('m');
 document.getElementById('peek').onclick=()=>{
   const k=document.getElementById('key'); k.type = k.type==='password'?'text':'password';
   document.getElementById('peek').textContent = k.type==='password'?'显示':'隐藏';
 };
 f.onsubmit=async (e)=>{
   e.preventDefault(); m.className='msg wait'; m.textContent='正在验证密钥…'; go.disabled=true;
   try{
     const r=await fetch(f.action,{method:'POST',body:new URLSearchParams(new FormData(f))});
     const j=await r.json();
     m.className = 'msg ' + (j.ok?'ok':'err'); m.textContent=j.message;
     if(j.ok){ go.textContent='已保存 ✓'; } else { go.disabled=false; document.getElementById('key').focus(); }
   }catch(err){ m.className='msg err'; m.textContent='本地服务无响应：'+err; go.disabled=false; }
 };
 __TIER_DEFAULT__
</script>
</body></html>
"""


class SetupServer:
    """一次性本地设置页：绑定 127.0.0.1，随机路径令牌，保存成功即退出。"""

    def __init__(self, cfg: dict, port: int, timeout: int, verify: bool):
        self.cfg = cfg
        self.port = port
        self.timeout = timeout
        self.verify = verify
        self.token = secrets.token_urlsafe(16)
        self.csrf = secrets.token_urlsafe(16)
        self.result: dict | None = None
        self.httpd: ThreadingHTTPServer | None = None
        self.done = threading.Event()
        self._page = self._build_page()

    def _build_page(self) -> str:
        cfg = self.cfg
        html = (SETUP_HTML
                .replace("__ACTION__", f"/{self.token}/save")
                .replace("__CSRF__", self.csrf)
                .replace("__KEY_PAGE__", KEY_PAGE)
                .replace("__EP_GLOBAL__", DEFAULT_ENDPOINT)
                .replace("__EP_CN__", CN_ENDPOINT)
                .replace("__OUT_DIR__", str(default_output_dir(cfg)).replace("\\", "/"))
                .replace("__CONFIG_HINT__", str(CONFIG_PATH).replace("\\", "/"))
                .replace("__TIER_DEFAULT__", f"document.getElementById('tier').value='{cfg.get('default_tier') or 'standard'}';\n"
                                             f"document.getElementById('endpoint').value='{cfg.get('endpoint') or DEFAULT_ENDPOINT}';")
                .replace("__KEY_PLACEHOLDER__", ""))
        return html

    def _handle_save(self, form: dict) -> dict:
        if form.get("csrf") != self.csrf:
            return {"ok": False, "message": "校验令牌不匹配，请刷新页面重试。"}
        key = (form.get("api_key") or "").strip()
        if not key:
            return {"ok": False, "message": "请先填入 API 密钥。"}
        if not key.startswith("sk-"):
            return {"ok": False, "message": "密钥格式看起来不对：Grsai 密钥以 sk- 开头。"}
        endpoint = (form.get("endpoint") or DEFAULT_ENDPOINT).rstrip("/")
        if self.verify:
            ok, why = probe_key(key, endpoint)
            if not ok:
                return {"ok": False, "message": f"验证未通过：{why}。请确认密钥与节点是否匹配。"}
        new_cfg = dict(self.cfg)
        new_cfg.update({
            "schema": 1,
            "provider": "grsai",
            "api_key": key,
            "endpoint": endpoint,
            "default_tier": form.get("default_tier") or "standard",
            "output_dir": (form.get("output_dir") or "").strip(),
        })
        new_cfg.setdefault("default_ratio", "1:1")
        new_cfg.setdefault("default_size", "1K")
        save_config(new_cfg)
        self.cfg = new_cfg
        self.result = {"ok": True, "message": f"已保存到 {CONFIG_PATH.as_posix()}（{mask_key(key)}）。可以关闭此页面。"}
        self.done.set()
        return self.result

    def _handler_factory(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):  # 静默，避免把路径写进 stderr
                pass

            def _host_ok(self) -> bool:
                host = (self.headers.get("Host") or "").split(":")[0]
                return host in ("127.0.0.1", "localhost", "[::1]")

            def _send(self, code: int, body: bytes, ctype: str):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(body)

            def _json(self, payload: dict):
                self._send(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                           "application/json; charset=utf-8")

            def do_GET(self):
                if not self._host_ok():
                    self._send(403, b"forbidden", "text/plain")
                    return
                if self.path.rstrip("/") == f"/{server.token}":
                    self._send(200, server._page.encode("utf-8"), "text/html; charset=utf-8")
                else:
                    self._send(404, b"not found", "text/plain")

            def do_POST(self):
                if not self._host_ok():
                    self._send(403, b"forbidden", "text/plain")
                    return
                if self.path.rstrip("/") != f"/{server.token}/save":
                    self._send(404, b"not found", "text/plain")
                    return
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
                form = {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}
                self._json(server._handle_save(form))
                if server.done.is_set():
                    threading.Thread(target=server.shutdown, daemon=True).start()

        return Handler

    def serve(self) -> dict | None:
        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), self._handler_factory())
        self.port = self.httpd.server_address[1]
        threading.Timer(self.timeout, self.shutdown).start()
        self.httpd.serve_forever(poll_interval=0.3)
        return self.result

    def shutdown(self):
        self.done.set()
        if self.httpd:
            threading.Thread(target=self.httpd.shutdown, daemon=True).start()


def cmd_setup(args) -> int:
    cfg = load_config()
    server = SetupServer(cfg, args.port, args.timeout, not args.skip_verify)
    # 端口在 bind 之后才知道，先起服务、等它拿到真实端口再拼 URL 并开浏览器
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    for _ in range(50):
        if server.httpd:
            break
        time.sleep(0.05)
    if not server.httpd:
        print("本地设置页启动失败。", file=sys.stderr)
        return EXIT_SERVER
    url = f"http://127.0.0.1:{server.port}/{server.token}"
    print(f"设置页已就绪：{url}", flush=True)
    print(f"请在浏览器中填入 Grsai API 密钥（最长等待 {args.timeout} 秒）。", flush=True)
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    server.done.wait(timeout=args.timeout + 5)
    server.shutdown()
    thread.join(timeout=5)
    if server.result and server.result.get("ok"):
        print("✓ " + server.result["message"], flush=True)
        return EXIT_OK
    if server.result:
        print("× " + str(server.result.get("message")), file=sys.stderr)
        return EXIT_AUTH
    print("× 等待超时，未保存任何内容。可重新运行 setup。", file=sys.stderr)
    return EXIT_TIMEOUT


# ---------------------------------------------------------------- 状态查询

def cmd_status(args) -> int:
    cfg = load_config()
    key, source = resolve_key(cfg)
    endpoint = resolve_endpoint(cfg)
    out_dir = default_output_dir(cfg)
    info: dict = {
        "version": VERSION,
        "config_path": CONFIG_PATH.as_posix(),
        "configured": bool(key),
        "key_masked": mask_key(key),
        "key_source": source,
        "endpoint": endpoint,
        "default_tier": cfg.get("default_tier") or "standard",
        "output_dir": out_dir.as_posix(),
        "output_dir_writable": False,
    }
    try:
        probe = out_dir
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        info["output_dir_writable"] = os.access(probe, os.W_OK)
        info["output_dir_exists"] = out_dir.exists()
    except OSError as exc:
        info["output_dir_error"] = str(exc)
    if args.verify and key:
        ok, why = probe_key(key, endpoint, args.timeout)
        info["auth_ok"] = ok
        info["auth_detail"] = why
    today = read_usage()
    info["today_count"] = len(today)
    info["today_credits"] = sum(int(r.get("credits") or 0) for r in today)

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return EXIT_OK if key else EXIT_CONFIG
    print(f"wenje-image {VERSION}")
    print(f"配置文件  {info['config_path']}")
    print(f"密钥      {info['key_masked']}（来源：{source}）")
    print(f"端点      {endpoint}")
    print(f"默认档位  {info['default_tier']}  →  {TIER_MODEL.get(info['default_tier'], '?')}")
    print(f"输出目录  {info['output_dir']}{'' if info['output_dir_writable'] else '  [不可写]'}")
    if "auth_ok" in info:
        print(f"鉴权      {'有效' if info['auth_ok'] else '无效'} — {info['auth_detail']}")
    print(f"今日用量  {info['today_count']} 张 / {info['today_credits']} credits")
    if not key:
        print("\n尚未配置密钥，请运行：python wenje_image.py setup")
    return EXIT_OK if key else EXIT_CONFIG


# ---------------------------------------------------------------- MCP 注册

MCP_AGENT_NAMES = ("zcode", "claude", "codex", "dsh")
DSH_PLUGIN = "@deepseek-ai/dsh-mcp-client"
DSH_PROFILE_DEFAULT = "web"
# 出图是长任务（提交→轮询→下载，默认最长 300 秒），多数 Agent 默认 60 秒级调用超时会把调用掐断，
# 所以注册时就写死一个足够大的值：Codex 用秒，DSH 用毫秒。
TOOL_TIMEOUT_SEC = 360
STARTUP_TIMEOUT_SEC = 30


def agent_home() -> Path:
    """Agent 配置根目录；WENJE_IMAGE_AGENT_HOME 供自检指向临时目录。"""
    override = os.environ.get("WENJE_IMAGE_AGENT_HOME")
    return Path(override).expanduser() if override else Path.home()


def mcp_targets(dsh_profile: str = DSH_PROFILE_DEFAULT) -> dict:
    """各 Agent 的 MCP 落点：JSON / TOML 是配置树，dsh 是 YAML 补丁层（数组追加条目）。"""
    home = agent_home()
    return {
        "zcode": {"kind": "json", "path": home / ".zcode" / "cli" / "config.json", "key": ["mcp", "servers"]},
        "claude": {"kind": "json", "path": home / ".claude.json", "key": ["mcpServers"]},
        "codex": {"kind": "toml", "path": home / ".codex" / "config.toml"},
        "dsh": {"kind": "dsh", "profile": dsh_profile,
                "path": home / ".dsh" / "profiles" / dsh_profile / "cordis.patch.yml"},
    }


def mcp_entry() -> dict:
    return {
        "type": "stdio",
        "command": sys.executable,
        "args": [str((Path(__file__).resolve().parent / "wenje_mcp.py").as_posix())],
    }


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def codex_block(entry: dict) -> str:
    return (f"[mcp_servers.{SKILL_NAME}]\n"
            f"command = {json.dumps(entry['command'])}\n"
            f"args = {json.dumps(entry['args'])}\n"
            f"tool_timeout_sec = {TOOL_TIMEOUT_SEC}\n"
            f"startup_timeout_sec = {STARTUP_TIMEOUT_SEC}\n")


def dsh_block(entry: dict) -> str:
    """DSH 的补丁层按 id 定向：新增插件要挂在 `- insert:` 下，无 id 的 insert 追加到顶层数组。"""
    args = ", ".join(yaml_quote(item) for item in entry["args"])
    return ("- insert:\n"
            f"    - id: mcp-{SKILL_NAME}\n"
            f"      name: {yaml_quote(DSH_PLUGIN)}\n"
            f"      config:\n"
            f"        serverName: {SKILL_NAME}\n"
            f"        transport: stdio\n"
            f"        command: {yaml_quote(entry['command'])}\n"
            f"        args: [{args}]\n"
            f"        toolCallTimeoutMs: {TOOL_TIMEOUT_SEC * 1000}\n")


def _separator(text: str) -> str:
    return "\n" if text.endswith("\n") else ("\n\n" if text else "")


def upsert_block(text: str, header: str, block: str) -> tuple[str, bool]:
    """TOML 节写入：已有同头部节就整节替换（便于补字段），否则追加。

    返回 (新文本, 是否已经是最新内容)——已经是最新时调用方不写文件、不留备份。
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(header)), None)
    if start is None:
        return text + _separator(text) + block, False
    end = start + 1
    while end < len(lines) and not lines[end].startswith("["):
        end += 1
    if "".join(line + "\n" for line in lines[start:end]) == block:
        return text, True
    new = ("".join(line + "\n" for line in lines[:start]) + block
           + "".join(line + "\n" for line in lines[end:]))
    return new, False


def upsert_dsh_block(text: str, block: str) -> tuple[str, bool]:
    """DSH 补丁层写入：按条目特征行定位整块替换，兼作旧写法的升级。

    早期版本把插件条目直接写成顶层 `- id: ...`，那是「改已有条目」的写法，DSH 会报
    `patch: entry ... not found`；这里两种情况都能被替换成正确的 `- insert:` 写法。
    """
    lines = text.splitlines()
    marker = f"- id: mcp-{SKILL_NAME}"
    hit = next((i for i, line in enumerate(lines) if line.strip() == marker), None)
    if hit is None:
        return text + _separator(text) + block, False
    start = hit
    while start > 0 and not lines[start].startswith("- "):
        start -= 1
    end = hit + 1
    while end < len(lines) and not lines[end].startswith("- "):
        end += 1
    if "".join(line + "\n" for line in lines[start:end]) == block:
        return text, True
    new = ("".join(line + "\n" for line in lines[:start]) + block
           + "".join(line + "\n" for line in lines[end:]))
    return new, False


def verify_written(path: Path, kind: str, entry: dict) -> str:
    """写完立刻回读解析：Agent 配置写坏会让它起不来，宁可回滚。"""
    try:
        text = path.read_text(encoding="utf-8")
        if kind == "json":
            json.loads(text)
        elif kind == "toml":
            import tomllib
            tomllib.loads(text)
        else:
            return verify_dsh_block(text, entry)
        return ""
    except (OSError, ValueError) as exc:
        return str(exc)


def verify_dsh_block(text: str, entry: dict) -> str:
    """标准库没有 YAML 解析器：按行核对写入块的结构与缩进，别把补丁层写坏。"""
    lines = text.splitlines()
    marker = f"- id: mcp-{SKILL_NAME}"
    hit = next((i for i, line in enumerate(lines) if line.strip() == marker), None)
    if hit is None:
        return f"找不到 {marker} 条目"
    start = hit
    while start > 0 and not lines[start].startswith("- "):
        start -= 1
    end = hit + 1
    while end < len(lines) and not lines[end].startswith("- "):
        end += 1
    block = lines[start:end]
    args = ", ".join(yaml_quote(item) for item in entry["args"])
    expected = [
        (0, "- insert:"),
        (4, marker),
        (6, f"name: {yaml_quote(DSH_PLUGIN)}"),
        (6, "config:"),
        (8, f"serverName: {SKILL_NAME}"),
        (8, "transport: stdio"),
        (8, f"command: {yaml_quote(entry['command'])}"),
        (8, f"args: [{args}]"),
        (8, f"toolCallTimeoutMs: {TOOL_TIMEOUT_SEC * 1000}"),
    ]
    for indent, content in expected:
        if " " * indent + content not in block:
            return f"条目缺少或缩进不对：{content}"
    return ""


def cmd_install(args) -> int:
    entry = mcp_entry()
    targets = mcp_targets(getattr(args, "dsh_profile", DSH_PROFILE_DEFAULT))
    if args.print_only or args.agent == "print":
        print("# Claude / ZCode 类客户端（JSON）")
        print(json.dumps({"mcpServers": {SKILL_NAME: entry}}, ensure_ascii=False, indent=2))
        print(f"\n# Codex（~/.codex/config.toml）\n{codex_block(entry)}")
        print(f"# DSH（~/.dsh/profiles/<profile>/cordis.patch.yml）\n{dsh_block(entry)}")
        return EXIT_OK
    names = list(targets) if args.agent == "all" else [args.agent]
    failed = False
    for name in names:
        spec = targets[name]
        path: Path = spec["path"]
        if not path.is_file():
            print(f"[跳过] {name}：{path.as_posix()} 不存在")
            continue
        try:
            if spec["kind"] == "json":
                raw = path.read_text(encoding="utf-8")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise WenjeError(f"配置不是合法 JSON，未修改：{exc}", EXIT_PARAM)
                node = data
                for part in spec["key"]:
                    node = node.setdefault(part, {})
                if node.get(SKILL_NAME) == entry:
                    print(f"[已存在] {name}：{path.as_posix()}")
                    continue
                node[SKILL_NAME] = entry
                backup = backup_config(path)
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                problem = verify_written(path, "json", entry)
                if problem:
                    restore(path, backup)
                    raise WenjeError(f"写入后无法解析，已回滚：{problem}", EXIT_SERVER)
                print(f"[注册] {name}：{path.as_posix()} → {'.'.join(spec['key'])}.{SKILL_NAME}")
            elif spec["kind"] == "toml":
                text = path.read_text(encoding="utf-8")
                updated, done = upsert_block(text, f"[mcp_servers.{SKILL_NAME}]", codex_block(entry))
                if done:
                    print(f"[已存在] {name}：{path.as_posix()}")
                    continue
                backup = backup_config(path)
                path.write_text(updated, encoding="utf-8")
                problem = verify_written(path, "toml", entry)
                if problem:
                    restore(path, backup)
                    raise WenjeError(f"写入后 TOML 无法解析，已回滚：{problem}", EXIT_SERVER)
                print(f"[注册] {name}：{path.as_posix()} → [mcp_servers.{SKILL_NAME}]")
            else:
                text = path.read_text(encoding="utf-8")
                updated, done = upsert_dsh_block(text, dsh_block(entry))
                if done:
                    print(f"[已存在] {name}：{path.as_posix()}（profile {spec['profile']}）")
                    continue
                backup = backup_config(path)
                path.write_text(updated, encoding="utf-8")
                problem = verify_written(path, "dsh", entry)
                if problem:
                    restore(path, backup)
                    raise WenjeError(f"写入后补丁层结构不对，已回滚：{problem}", EXIT_SERVER)
                print(f"[注册] {name}：{path.as_posix()} → mcp-{SKILL_NAME} 条目"
                      f"（profile {spec['profile']}，MCP 插件 {DSH_PLUGIN}）")
        except (OSError, WenjeError) as exc:
            failed = True
            print(f"[失败] {name}：{exc}", file=sys.stderr)
    print("\n生效方式：DSH 保存后热应用补丁层；其余 Agent 需重启。"
          f"验证：工具列表出现 generate_image（DSH 下为 mcp__{SKILL_NAME}__generate_image）。")
    return EXIT_SERVER if failed else EXIT_OK


def backup_config(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.wenje-backup-{stamp}")
    try:
        backup.write_bytes(path.read_bytes())
        print(f"       已备份 {backup.as_posix()}")
    except OSError as exc:
        print(f"       备份失败（继续）：{exc}", file=sys.stderr)
    return backup


def restore(path: Path, backup: Path) -> None:
    try:
        path.write_bytes(backup.read_bytes())
        print(f"       已从 {backup.as_posix()} 回滚", file=sys.stderr)
    except OSError as exc:
        print(f"       回滚失败：{exc}", file=sys.stderr)


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wenje_image.py", description="wenje-image 引擎（Grsai 出图）")
    p.add_argument("--version", action="version", version=f"wenje-image {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("setup", help="启动本地设置页录入 API 密钥")
    s.add_argument("--port", type=int, default=0, help="监听端口，0 表示随机端口")
    s.add_argument("--timeout", type=int, default=300, help="等待提交的秒数")
    s.add_argument("--no-browser", action="store_true", help="不自动打开浏览器，只打印 URL")
    s.add_argument("--skip-verify", action="store_true", help="保存前不做密钥验证")

    s = sub.add_parser("status", help="查看配置与用量")
    s.add_argument("--json", action="store_true")
    s.add_argument("--verify", action="store_true", help="顺带探一次鉴权（不产生费用）")
    s.add_argument("--timeout", type=int, default=20)

    s = sub.add_parser("generate", help="生成或编辑图片")
    s.add_argument("--prompt", "-p", help="提示词")
    s.add_argument("--prompt-file", help="从文件读提示词，避免 shell 转义；与 --prompt 二选一")
    s.add_argument("--tier", choices=sorted(TIER_MODEL), help="draft/standard/premium，仅在未点名模型时生效")
    s.add_argument("--model", choices=sorted(MODELS), help="点名模型，覆盖 --tier")
    s.add_argument("--ratio", help="比例，如 16:9；省略则用配置默认")
    s.add_argument("--size", choices=sorted(SIZE_RANK), help="1K/2K/4K；模型不支持时按能力落到最接近的档位")
    s.add_argument("--scene", choices=sorted(SCENE_PRESETS), help="场景预设，自动定比例与尺寸")
    s.add_argument("--ref", action="append", help="参考图路径，可重复；仅上传调用方明确给出的图")
    s.add_argument("--out", help="输出目录")
    s.add_argument("--name", help="文件名前缀")
    s.add_argument("--no-download", action="store_true", help="只返回远端 URL")
    s.add_argument("--dry-run", action="store_true", help="只打印将发送的请求，不调用 API")
    s.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    s.add_argument("--timeout", type=int, default=300, help="轮询总超时秒数")
    s.add_argument("--poll-interval", type=float, default=3.0, help="轮询间隔秒数")

    s = sub.add_parser("install", help="把 MCP server 注册到本机 Agent 配置")
    s.add_argument("--agent", choices=[*MCP_AGENT_NAMES, "all", "print"], default="all",
                   help="目标 Agent；all 自动跳过本机不存在的配置，print 只打印片段")
    s.add_argument("--dsh-profile", default=DSH_PROFILE_DEFAULT,
                   help="DSH profile 名，决定 ~/.dsh/profiles/<name>/cordis.patch.yml")
    s.add_argument("--print", dest="print_only", action="store_true", help="只打印配置片段，不写文件")

    s = sub.add_parser("mcp", help="以 stdio MCP server 运行")
    return p


def main(argv: list[str] | None = None) -> int:
    force_utf8()
    args = build_parser().parse_args(argv)
    try:
        if args.command == "setup":
            return cmd_setup(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "install":
            return cmd_install(args)
        if args.command == "mcp":
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import wenje_mcp
            return wenje_mcp.serve()
        if args.command == "generate":
            if args.prompt_file:
                try:
                    args.prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8").strip()
                except OSError as exc:
                    print(f"× 提示词文件读取失败：{exc}", file=sys.stderr)
                    return EXIT_PARAM
            if not (args.prompt or "").strip():
                print("× 需要 --prompt 或 --prompt-file。", file=sys.stderr)
                return EXIT_PARAM
            cfg = load_config()
            result = run_generation(args, cfg,
                                    on_tick=lambda s, pg: print(f"[轮询] {s} {pg if pg is not None else ''}".rstrip(),
                                                                file=sys.stderr, flush=True))
            if result.get("dry_run"):
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return EXIT_OK
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(render_result(result))
            return EXIT_OK
    except WenjeError as exc:
        print(f"× {exc}", file=sys.stderr)
        return exc.code
    except KeyboardInterrupt:
        return 130
    return EXIT_PARAM


if __name__ == "__main__":
    sys.exit(main())
