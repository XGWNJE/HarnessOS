"""Kimi Code -> Codex hook payload adapter.

Reads a Kimi Code hook payload from stdin, translates it into the
Claude/Codex-style payload shape that the legacy hook scripts expect,
pipes it to the legacy hook command given after `--`, then forwards the
child's stdout, stderr and exit code.

Translation rules:
- tool_call_id           -> also exposed as tool_use_id
- prompt content blocks  -> flattened to a plain string (UserPromptSubmit)
- PostToolUse            -> synthesizes tool_response {success: true, exit_code: 0}
- PostToolUseFailure     -> re-emitted as PostToolUse with
                            tool_response {success: false, exit_code: 1}
- everything else passes through untouched

Output JSON is ASCII-escaped (ensure_ascii=True) so PowerShell children that
decode stdin with the system codepage still get correct Unicode after
ConvertFrom-Json.

The adapter itself is fail-open: any internal error exits 0 so hooks never
block the session because of the shim.

--emit-event-once <EventName>: on the first event seen for a session, first
pipe a synthetic `EventName` event (source=startup) to the child and prepend
its stdout to the output. Used to move SessionStart-style context injection
onto the UserPromptSubmit event, because Kimi Code treats SessionStart hook
output as observation-only and never shows it to the model.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

CHILD_TIMEOUT_SEC = 18
EMIT_STATE_DIR = os.path.join(tempfile.gettempdir(), "kimi-codex-hook-adapter")
EMIT_MARKER_MAX_AGE_SEC = 7 * 24 * 3600


def flatten_prompt(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def translate(event):
    name = event.get("hook_event_name")
    if not event.get("tool_use_id") and event.get("tool_call_id"):
        event["tool_use_id"] = event["tool_call_id"]
    if name == "UserPromptSubmit" and not isinstance(event.get("prompt"), str):
        event["prompt"] = flatten_prompt(event.get("prompt"))
    elif name == "PostToolUseFailure":
        event["hook_event_name"] = "PostToolUse"
        if not isinstance(event.get("tool_response"), dict):
            event["tool_response"] = {
                "success": False,
                "exit_code": 1,
                "error": event.get("error") or event.get("tool_output") or "",
                "output": event.get("tool_output"),
            }
    elif name == "PostToolUse":
        if not isinstance(event.get("tool_response"), dict):
            event["tool_response"] = {
                "success": True,
                "exit_code": 0,
                "output": event.get("tool_output"),
            }
    return event


def run_child(child, payload):
    proc = subprocess.run(
        child,
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=CHILD_TIMEOUT_SEC,
    )
    return proc


def marker_path(session_id, event_name):
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in session_id)
    return os.path.join(EMIT_STATE_DIR, f"{safe}.{event_name}.done")


def prune_markers():
    try:
        os.makedirs(EMIT_STATE_DIR, exist_ok=True)
        cutoff = time.time() - EMIT_MARKER_MAX_AGE_SEC
        for name in os.listdir(EMIT_STATE_DIR):
            path = os.path.join(EMIT_STATE_DIR, name)
            try:
                if name.endswith(".done") and os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass
    except OSError:
        pass


def main():
    argv = sys.argv[1:]
    emit_once = None
    if len(argv) >= 2 and argv[0] == "--emit-event-once":
        emit_once = argv[1]
        argv = argv[2:]
    if not argv or argv[0] != "--" or len(argv) < 2:
        sys.stderr.write(
            "usage: kimi-codex-hook-adapter.py [--emit-event-once <EventName>] -- <child command...>\n"
        )
        return 0
    child = argv[1:]
    raw = sys.stdin.buffer.read()
    event = None
    try:
        event = translate(json.loads(raw.decode("utf-8", errors="replace")))
        payload = json.dumps(event, ensure_ascii=True).encode("ascii")
    except Exception:
        payload = raw  # unparsable input: forward untouched, stay fail-open

    # Kimi treats SessionStart hook output as observation-only, so a child that
    # relies on SessionStart stdout reaching the model (e.g. scope-guard) would
    # silently lose it. --emit-event-once replays a synthetic SessionStart
    # through the child on the first real event of each session instead, where
    # stdout does get appended to the context.
    prefix_out = b""
    if emit_once and event is not None:
        try:
            session_id = str(event.get("session_id") or "unknown-session")
            marker = marker_path(session_id, emit_once)
            if not os.path.exists(marker):
                os.makedirs(EMIT_STATE_DIR, exist_ok=True)
                synthetic = {
                    "hook_event_name": emit_once,
                    "session_id": session_id,
                    "cwd": event.get("cwd") or "",
                    "source": "startup",
                }
                proc0 = run_child(child, json.dumps(synthetic, ensure_ascii=True).encode("ascii"))
                if proc0.stdout:
                    prefix_out = proc0.stdout
                with open(marker, "w", encoding="ascii") as fh:
                    fh.write(str(int(time.time())))
            prune_markers()
        except Exception:
            prefix_out = b""  # fail-open: never block on replay errors

    try:
        proc = run_child(child, payload)
    except Exception:
        if prefix_out:
            sys.stdout.buffer.write(prefix_out)
            sys.stdout.buffer.flush()
        return 0
    if prefix_out:
        sys.stdout.buffer.write(prefix_out)
    if proc.stdout:
        sys.stdout.buffer.write(proc.stdout)
    if proc.stderr:
        sys.stderr.buffer.write(proc.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
