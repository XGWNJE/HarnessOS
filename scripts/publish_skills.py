#!/usr/bin/env python3
"""把 skills/ 下的自有 skill 发布到各 Agent 实际读取的 skill 目录。

用法：
    python scripts/publish_skills.py            # 发布全部映射
    python scripts/publish_skills.py --check    # 只检查同步状态，不写入

发布映射（源 = skills/<name>/）：
    ~/.agents/skills/<name>/          跨 Agent 共享 skill 池（agentskills.io 标准位置）
    ~/.claude/skills/vps-server-info/ 仅 vps-server-info（Claude 池的同名副本，以仓库为准）

发布以目录为单位做整目录镜像（源多余文件全拷、目标多余文件删除）。
目标被视为发布产物：写入前若不一致，先备份到 backups/ 再覆盖。
.ai-stack-harness / ai-coding-workflow 走 pack.py 打包 .skill，不经本脚本发布。
"""

import filecmp
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
BACKUPS = ROOT / "backups"

SHARED = ["grsai-image-gen", "init-project", "scope-guard", "vps-server-info"]
TARGETS = [(name, HOME / ".agents" / "skills" / name) for name in SHARED]
TARGETS.append(("vps-server-info", HOME / ".claude" / "skills" / "vps-server-info"))


def dir_same(a: Path, b: Path) -> bool:
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dir_same(a / s, b / s) for s in cmp.common_dirs)


def mirror(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))


def main() -> None:
    check_only = "--check" in sys.argv
    drift = False
    for name, target in TARGETS:
        src = ROOT / "skills" / name
        if dir_same(src, target):
            print(f"[同步] {name:18s} {target}")
            continue
        drift = True
        if check_only:
            print(f"[漂移] {name:18s} {target}")
            continue
        if target.exists():
            BACKUPS.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            pool = target.parent.parent.name  # .agents / .claude
            shutil.copytree(target, BACKUPS / f"skill-{pool}-{name}-{ts}")
        mirror(src, target)
        print(f"[发布] {name:18s} {target}")
    if check_only and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
