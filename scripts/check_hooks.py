#!/usr/bin/env python3
"""hook 登记体检：对照 global/hooks/registry.json 校验全机 Agent hook 注册状态。

用法：
    python scripts/check_hooks.py     # 只体检不写入，漂移退出码 1

校验项（对每条登记）：
    1. 源文件存在；
    2. 注册点（kimi config.toml / codex hooks.json）中存在该 event 的条目，
       其 command 引用该源文件；
    3. 登记了 matcher 的，注册点中的 matcher 与登记一致。

本脚本只读不写：注册点含 API key 等活配置，漂移由人按 registry.json 修复，
不做自动覆盖。公共 hook 源（global/hooks/）被 config.toml 直引，改源即生效。
"""

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "global" / "hooks" / "registry.json"
KIMI_CONFIG = Path.home() / ".kimi-code" / "config.toml"
CODEX_HOOKS = Path.home() / ".codex" / "hooks.json"


def kimi_entries() -> list[dict]:
    with open(KIMI_CONFIG, "rb") as f:
        return tomllib.load(f).get("hooks", [])


def codex_entries() -> list[dict]:
    """摊平 hooks.json 为与 kimi 类似的条目列表。"""
    data = json.loads(CODEX_HOOKS.read_text(encoding="utf-8")).get("hooks", {})
    out = []
    for event, groups in data.items():
        for g in groups:
            for h in g.get("hooks", []):
                out.append({
                    "event": event,
                    "matcher": g.get("matcher"),
                    "command": h.get("command", ""),
                })
    return out


def main() -> None:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = {"kimi-code": kimi_entries(), "codex": codex_entries()}
    drift = False
    for r in reg["registrations"]:
        label = f"{r['runtime']:9s} {r['event']:18s} {Path(r['source']).name}"
        if not Path(r["source"]).exists():
            print(f"[漂移] {label} —— 源文件不存在：{r['source']}")
            drift = True
            continue
        base = Path(r["source"]).name
        hit = next(
            (e for e in entries[r["runtime"]]
             if e.get("event") == r["event"] and base in e.get("command", "")),
            None,
        )
        if hit is None:
            print(f"[漂移] {label} —— 注册点中找不到该 event 且引用源文件的条目")
            drift = True
            continue
        if r.get("matcher") is not None and hit.get("matcher") != r["matcher"]:
            print(f"[漂移] {label} —— matcher 不一致：登记 {r['matcher']!r}，注册点 {hit.get('matcher')!r}")
            drift = True
            continue
        print(f"[同步] {label}")
    sys.exit(1 if drift else 0)


if __name__ == "__main__":
    main()
