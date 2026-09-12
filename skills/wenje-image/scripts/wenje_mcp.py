#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wenje-image 的 stdio MCP server。

把出图能力变成一个原生工具调用，而不是"让模型写脚本再解析输出"：
    generate_image     出图/改图，返回落盘路径 + 可直接看的预览图
    image_status       密钥、端点、默认档位、今日用量
    open_setup_page    起本地设置页，由用户在浏览器里录入密钥

协议：JSON-RPC 2.0，换行分隔，UTF-8。仅标准库；Pillow 可选（只用于预览缩略图）。
"""

from __future__ import annotations

import base64
import io
import json
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wenje_image as core  # noqa: E402

PROTOCOL_DEFAULT = "2024-11-05"
PROTOCOL_KNOWN = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
PREVIEW_MAX_PX = 640

_setup_server: core.SetupServer | None = None


# ---------------------------------------------------------------- 工具实现

def make_preview(path: str) -> tuple[str, str] | None:
    """返回 (base64, mimeType)。模型要能当场看到结果，但不该把 1.4MB 原图塞进上下文。"""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((PREVIEW_MAX_PX, PREVIEW_MAX_PX))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"
    except Exception:
        return None


def tool_generate(args: dict) -> tuple[str, list[dict], bool]:
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return "缺少 prompt。", [], True
    ns = SimpleNamespace(
        prompt=prompt,
        tier=args.get("tier"),
        model=args.get("model"),
        ratio=args.get("aspect_ratio"),
        size=args.get("image_size"),
        scene=args.get("scene"),
        ref=args.get("reference_images") or [],
        out=args.get("output_dir"),
        name=args.get("filename_hint"),
        no_download=False,
        dry_run=bool(args.get("dry_run")),
        timeout=int(args.get("timeout_seconds") or 300),
        poll_interval=3.0,
    )
    result = core.run_generation(ns, core.load_config())
    if result.get("dry_run"):
        return "dry_run：以下请求未发送，不会产生费用。\n" + json.dumps(result, ensure_ascii=False, indent=2), [], False

    text = json.dumps(result, ensure_ascii=False, indent=2)
    blocks: list[dict] = []
    path = result.get("path")
    if path and result.get("kind") == "image":
        preview = make_preview(path)
        if preview:
            blocks.append({"type": "image", "data": preview[0], "mimeType": preview[1]})
        else:
            text += "\n（未安装 Pillow，未附带预览图；用 Read 工具查看落盘文件即可。）"
    elif path and result.get("kind") == "video":
        text += "\n（结果是视频，不是图片，请以链接形式展示。）"
    return text, blocks, False


def tool_status(_: dict) -> tuple[str, list[dict], bool]:
    ns = SimpleNamespace(json=True, verify=True, timeout=20)
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = core.cmd_status(ns)
    try:
        info = json.loads(buf.getvalue())
    except json.JSONDecodeError:
        info = {"raw": buf.getvalue(), "exit": code}
    if not info.get("configured"):
        info["next_step"] = "调用 open_setup_page 让用户在浏览器里录入密钥。"
    return json.dumps(info, ensure_ascii=False, indent=2), [], bool(code) and not info.get("configured")


def tool_setup(args: dict) -> tuple[str, list[dict], bool]:
    global _setup_server
    if _setup_server and not _setup_server.done.is_set():
        return (f"设置页已经在运行：http://127.0.0.1:{_setup_server.port}/{_setup_server.token}\n"
                "请让用户在该页面填入密钥；完成后再次调用 image_status 确认。"), [], False
    wait = float(args.get("wait_seconds") or 0)
    server = core.SetupServer(core.load_config(), 0, max(int(wait) + 60, 300), not args.get("skip_verify"))
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    for _ in range(60):
        if server.httpd:
            break
        time.sleep(0.05)
    if not server.httpd:
        return "本地设置页启动失败。", [], True
    _setup_server = server
    url = f"http://127.0.0.1:{server.port}/{server.token}"
    if not args.get("no_browser"):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    if wait <= 0:
        return (f"设置页已打开：{url}\n"
                "请在浏览器中填入 Grsai API 密钥（页面只监听本机 127.0.0.1，保存后自动退出）。\n"
                "完成后调用 image_status 确认 configured 为 true。"), [], False
    server.done.wait(timeout=wait)
    if server.result and server.result.get("ok"):
        _setup_server = None
        return "✓ " + str(server.result["message"]), [], False
    return "设置页等待超时或未保存，密钥未写入。", [], True


TOOLS = [
    {
        "name": "generate_image",
        "description": ("用 Grsai 生成或编辑图片，返回落盘绝对路径与预览图。属于付费外部调用："
                        "参数含糊、要求高分辨率或 -vip 模型、重复生成时先与用户确认。"
                        "reference_images 只上传用户为本次任务提供或确认使用的图。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "英文或中文视觉描述，含主体、风格、光照、构图"},
                "tier": {"type": "string", "enum": ["draft", "standard", "premium"],
                         "description": "成本档位，默认 standard（gpt-image-2）"},
                "model": {"type": "string", "description": "直接指定模型，覆盖 tier"},
                "aspect_ratio": {"type": "string", "description": "比例，如 1:1 / 16:9 / 9:16 / 21:9"},
                "image_size": {"type": "string", "enum": ["1K", "2K", "4K"], "description": "分辨率档"},
                "scene": {"type": "string", "enum": sorted(core.SCENE_PRESETS),
                          "description": "场景预设，自动决定比例与尺寸"},
                "reference_images": {"type": "array", "items": {"type": "string"},
                                     "description": "参考图本地绝对路径列表（改图/风格参考）"},
                "output_dir": {"type": "string", "description": "保存目录，默认 ~/Pictures/wenje-image"},
                "filename_hint": {"type": "string", "description": "文件名前缀，便于后续按名查找"},
                "dry_run": {"type": "boolean", "description": "只预览将发送的请求与预估价格，不调用 API"},
                "timeout_seconds": {"type": "integer", "description": "轮询总超时，默认 300"}
            },
            "required": ["prompt"]
        },
    },
    {
        "name": "image_status",
        "description": "查看 wenje-image 的密钥来源、端点连通性、鉴权有效性、默认档位、输出目录与今日用量。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_setup_page",
        "description": ("在浏览器中打开本地设置页，由用户自己录入 Grsai API 密钥——密钥不经过对话。"
                        "未配置密钥或密钥失效时调用。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "wait_seconds": {"type": "number", "description": "等待用户提交的秒数，0 表示立即返回 URL"},
                "no_browser": {"type": "boolean", "description": "只返回 URL，不自动打开浏览器"},
                "skip_verify": {"type": "boolean", "description": "保存前跳过密钥验证"}
            }
        },
    },
]


def dispatch(name: str, args: dict) -> tuple[str, list[dict], bool]:
    if name == "generate_image":
        return tool_generate(args)
    if name == "image_status":
        return tool_status(args)
    if name == "open_setup_page":
        return tool_setup(args)
    return f"未知工具：{name}", [], True


# ---------------------------------------------------------------- JSON-RPC

def send(message: dict) -> None:
    sys.stdout.buffer.write(json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n")
    sys.stdout.buffer.flush()


def reply(msg_id, result=None, error=None) -> None:
    payload = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    send(payload)


def handle(message: dict) -> None:
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        asked = params.get("protocolVersion")
        version = asked if asked in PROTOCOL_KNOWN else PROTOCOL_DEFAULT
        reply(msg_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": core.SKILL_NAME, "version": core.VERSION},
        })
        return
    if method in ("notifications/initialized", "initialized"):
        return
    if method == "ping":
        reply(msg_id, {})
        return
    if method == "tools/list":
        reply(msg_id, {"tools": TOOLS})
        return
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            text, blocks, is_error = dispatch(name, args)
        except core.WenjeError as exc:
            reply(msg_id, {"content": [{"type": "text", "text": f"× {exc}"}], "isError": True})
            return
        except Exception as exc:  # 不让任何异常打断 stdio 循环
            reply(msg_id, {"content": [{"type": "text", "text": f"× 内部错误：{exc}"}], "isError": True})
            return
        content = [{"type": "text", "text": text}] + blocks
        reply(msg_id, {"content": content, "isError": is_error})
        return
    if msg_id is not None:
        reply(msg_id, error={"code": -32601, "message": f"未实现的方法：{method}"})


def serve() -> int:
    core.force_utf8()
    for raw in sys.stdin.buffer:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(message, dict):
            handle(message)
    return 0


if __name__ == "__main__":
    sys.exit(serve())
