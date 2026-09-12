#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wenje-image 的本地自检：MCP 协议握手、工具清单、设置页起停与密钥落盘。

不发起任何付费调用。用法：python tests/local_check.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ENGINE = SCRIPTS / "wenje_image.py"
MCP = SCRIPTS / "wenje_mcp.py"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'通过' if ok else '失败'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def mcp_session(messages: list[dict], timeout: int = 60) -> list[dict]:
    payload = "".join(json.dumps(m, ensure_ascii=False) + "\n" for m in messages)
    proc = subprocess.run([sys.executable, str(MCP)], input=payload.encode("utf-8"),
                          capture_output=True, timeout=timeout)
    out = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    if not out and proc.stderr:
        print(proc.stderr.decode("utf-8", errors="replace")[:1000])
    return out


def test_mcp() -> None:
    responses = mcp_session([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "local-check", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "image_status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "generate_image", "arguments": {"prompt": "", "dry_run": True}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "no_such_tool", "arguments": {}}},
    ])
    by_id = {r.get("id"): r for r in responses}

    init = by_id.get(1, {}).get("result", {})
    check("MCP initialize 回协议版本与工具能力",
          init.get("protocolVersion") == "2025-06-18" and "tools" in init.get("capabilities", {}),
          f"protocolVersion={init.get('protocolVersion')}")

    tools = [t["name"] for t in by_id.get(2, {}).get("result", {}).get("tools", [])]
    check("MCP tools/list 暴露三个工具",
          tools == ["generate_image", "image_status", "open_setup_page"], str(tools))

    status = by_id.get(3, {}).get("result", {})
    body = json.loads(status.get("content", [{}])[0].get("text", "{}"))
    check("image_status 回结构化状态",
          "configured" in body and "endpoint" in body, f"configured={body.get('configured')}")

    gt = by_id.get(4, {}).get("result", {})
    check("generate_image 空 prompt 被拒", gt.get("isError") is True)

    unknown = by_id.get(5, {}).get("result", {})
    check("未知工具返回 isError", unknown.get("isError") is True)


def test_mcp_dry_run() -> None:
    env = dict(os.environ, GRSAI_API_KEY="sk-local-check-not-a-real-key")
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                          "params": {"name": "generate_image",
                                     "arguments": {"prompt": "窗台上的橘猫", "tier": "premium",
                                                   "aspect_ratio": "16:9", "dry_run": True}}},
                         ensure_ascii=False) + "\n"
    proc = subprocess.run([sys.executable, str(MCP)], input=payload.encode("utf-8"),
                          capture_output=True, timeout=60, env=env)
    line = proc.stdout.decode("utf-8", errors="replace").strip().splitlines()[-1]
    text = json.loads(line)["result"]["content"][0]["text"]
    check("generate_image dry_run 走通且不落请求", "dry_run" in text and "nano-banana-pro" in text,
          text.splitlines()[1] if "\n" in text else text[:80])


def test_setup_page() -> None:
    """起设置页 → 模拟浏览器 POST → 校验密钥已写入临时配置 → 页面自行退出。"""
    tmp = Path(tempfile.mkdtemp(prefix="wenje-check-"))
    env = dict(os.environ, HOME=str(tmp), USERPROFILE=str(tmp), HOMEDRIVE=tmp.drive or "C:",
               HOMEPATH=str(tmp)[2:] if len(str(tmp)) > 2 else "", PYTHONUTF8="1")
    env.pop("GRSAI_API_KEY", None)
    env.pop("WENJE_IMAGE_API_KEY", None)
    env["WENJE_IMAGE_HOME"] = str(tmp / ".wenje-image")
    proc = subprocess.Popen([sys.executable, str(ENGINE), "setup", "--port", "0",
                             "--timeout", "40", "--no-browser", "--skip-verify"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)
    try:
        url = ""
        deadline = time.time() + 25
        while time.time() < deadline:
            line = proc.stdout.readline()
            if "http://127.0.0.1:" in line:
                url = line.split("：", 1)[-1].strip()
                break
        check("setup 打印本地设置页 URL", bool(url), url)
        if not url:
            return
        with urllib.request.urlopen(url, timeout=10) as resp:
            page = resp.read().decode("utf-8")
        check("设置页返回带表单的 HTML",
              resp.status == 200 and 'name="api_key"' in page and "csrf" in page)

        csrf = page.split('name="csrf" value="', 1)[1].split('"', 1)[0]
        bad = urllib.parse.urlencode({"csrf": "wrong", "api_key": "sk-local-check-000000"})
        with urllib.request.urlopen(urllib.request.Request(url + "/save", data=bad.encode()), timeout=10) as r:
            res = json.loads(r.read().decode("utf-8"))
        check("CSRF 不匹配被拒", res.get("ok") is False, res.get("message", ""))

        good = urllib.parse.urlencode({"csrf": csrf, "api_key": "sk-local-check-000000",
                                       "endpoint": "https://grsaiapi.com", "default_tier": "draft",
                                       "output_dir": str(tmp / "out")})
        with urllib.request.urlopen(urllib.request.Request(url + "/save", data=good.encode()), timeout=10) as r:
            res = json.loads(r.read().decode("utf-8"))
        check("合法提交保存成功", res.get("ok") is True, res.get("message", ""))

        cfg_path = tmp / ".wenje-image" / "config.json"
        saved = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
        check("密钥落入配置文件且档位生效",
              saved.get("api_key") == "sk-local-check-000000" and saved.get("default_tier") == "draft",
              f"keys={sorted(saved)}")

        proc.wait(timeout=15)
        check("保存后设置页自行退出", proc.returncode == 0, f"exit={proc.returncode}")
    finally:
        if proc.poll() is None:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def test_key_redaction() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import wenje_image as core
    secret = "sk-abcdefghijklmnopqrstuvwxyz012345"
    msg = core.redact(f"upstream said key={secret} is bad", secret)
    check("密钥在错误信息中被脱敏", secret not in msg and "sk-abc***" in msg, msg)
    check("未配置时 resolve_key 返回空", core.resolve_key({})[0] is None)


def main() -> int:
    print(f"引擎：{ENGINE}")
    test_mcp()
    test_mcp_dry_run()
    test_setup_page()
    test_key_redaction()
    print()
    if failures:
        print(f"× {len(failures)} 项未通过：" + "、".join(failures))
        return 1
    print("✓ 全部自检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
