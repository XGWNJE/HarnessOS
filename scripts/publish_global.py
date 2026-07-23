#!/usr/bin/env python3
"""把 global/AGENTS.md（核心规则）发布到各 Agent 的全局规则位置。

用法：
    python scripts/publish_global.py            # 发布全部目标
    python scripts/publish_global.py --check    # 只检查同步状态，不写入

发布映射（核心 = global/AGENTS.md，overlay = global/overlays/<name>.md）：
    ~/AGENTS.md                        核心（home 根，供读取该位置的 Agent）
    ~/.codex/AGENTS.md                 核心（Codex）
    ~/.config/opencode/AGENTS.md       核心（OpenCode）
    ~/.claude/CLAUDE.md                核心 + overlays/claude.md（Claude Code）
Kimi Code 无全局规则注入机制，不发布（规则走项目级 AGENTS.md / skills）。

目标文件被视为发布产物：写入前若已有不同内容，先备份到 backups/ 再覆盖。
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
CORE = ROOT / "global" / "AGENTS.md"
OVERLAYS = ROOT / "global" / "overlays"
BACKUPS = ROOT / "backups"

TARGETS = [
    ("home",     HOME / "AGENTS.md",                    None),
    ("codex",    HOME / ".codex" / "AGENTS.md",         None),
    ("opencode", HOME / ".config" / "opencode" / "AGENTS.md", None),
    ("claude",   HOME / ".claude" / "CLAUDE.md",        "claude"),
]


def build(overlay: str | None) -> str:
    text = CORE.read_text(encoding="utf-8")
    if overlay:
        f = OVERLAYS / f"{overlay}.md"
        text = text.rstrip() + "\n\n---\n\n" + f.read_text(encoding="utf-8")
    return text


def main() -> None:
    check_only = "--check" in sys.argv
    drift = False
    for name, target, overlay in TARGETS:
        want = build(overlay)
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == want:
            print(f"[同步] {name:9s} {target}")
            continue
        drift = True
        if check_only:
            state = "不存在" if current is None else "与源文件不一致"
            print(f"[漂移] {name:9s} {target}（{state}）")
            continue
        if current is not None:
            BACKUPS.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(target, BACKUPS / f"{name}-{ts}.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(want, encoding="utf-8")
        print(f"[发布] {name:9s} {target}")
    if check_only and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
