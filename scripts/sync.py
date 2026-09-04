#!/usr/bin/env python3
"""刷新或检查受管资产目录，并发布全局 AGENTS 与 skills。"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
CHILD_ENV = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def configure_output_encoding() -> None:
    """Keep Chinese status output readable in Windows terminals and runners."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def run(script: str, *args: str) -> bool:
    result = subprocess.run(
        [PY, str(ROOT / "scripts" / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=CHILD_ENV,
    )
    output = (result.stdout or "") + (result.stderr or "")
    for line in output.splitlines():
        if line.strip():
            print(f"  {line}")
    return result.returncode == 0


def main() -> None:
    configure_output_encoding()
    check = "--check" in sys.argv
    args = ("--check",) if check else ()
    print("== 资产目录检查 ==" if check else "== 刷新资产目录 ==")
    ok = run("catalog.py", "check" if check else "render")
    if not ok:
        sys.exit(1)
    if check:
        print("== 发布漂移检查 ==")
    else:
        print("== 发布全局 AGENTS ==")
    ok = run("publish_global.py", *args)
    print("== 发布 skills ==" if not check else "== skill 漂移检查 ==")
    ok &= run("publish_skills.py", *args)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
