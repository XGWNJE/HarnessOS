#!/usr/bin/env python3
"""把 global/AGENTS.md（核心规则）发布到各 Agent 的全局规则位置。

用法：
    python scripts/publish_global.py            # 发布全部目标
    python scripts/publish_global.py --check    # 只检查同步状态，不写入

发布映射（源 = global/AGENTS.md）：
    ~/AGENTS.md                         home 根
    ~/.codex/AGENTS.md                  Codex
    ~/.config/opencode/AGENTS.md        OpenCode
    ~/.claude/CLAUDE.md                 Claude Code
    ~/.dsh/AGENTS.md                    DSH（$DSH_HOME/AGENTS.md）
Kimi Code 无全局规则注入机制，不发布（规则走项目级 AGENTS.md / skills）。

目标文件被视为发布产物：与源不一致时直接覆盖。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
CORE = ROOT / "global" / "AGENTS.md"
TARGETS = [
    ("home",     HOME / "AGENTS.md"),
    ("codex",    HOME / ".codex" / "AGENTS.md"),
    ("opencode", HOME / ".config" / "opencode" / "AGENTS.md"),
    ("claude",   HOME / ".claude" / "CLAUDE.md"),
    ("dsh",      HOME / ".dsh" / "AGENTS.md"),
]


def build() -> str:
    return CORE.read_text(encoding="utf-8")


def main() -> None:
    check_only = "--check" in sys.argv
    drift = False
    for name, target in TARGETS:
        want = build()
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == want:
            print(f"[同步] {name:9s} {target}")
            continue
        drift = True
        if check_only:
            state = "不存在" if current is None else "与源文件不一致"
            print(f"[漂移] {name:9s} {target}（{state}）")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(want, encoding="utf-8")
        print(f"[发布] {name:9s} {target}")
    if check_only and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
