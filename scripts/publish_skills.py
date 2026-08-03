#!/usr/bin/env python3
"""把 skills/ 与 vendor/ 下的 skill 发布到各 Agent 实际读取的 skill 目录。

用法：
    python scripts/publish_skills.py            # 发布全部映射
    python scripts/publish_skills.py --check    # 只检查同步状态，不写入

发布映射（源 = skills/<name>/ 自有 + vendor/<name>/ 第三方原样中转，× 3 个读取池）：
    ~/.agents/skills/<name>/   跨 Agent 共享池（agentskills.io 标准位置，OpenCode 等）
    ~/.codex/skills/<name>/    Codex 池
    ~/.claude/skills/<name>/   Claude Code 池
Kimi Code CLI 无独立 skills 目录（config 有 merge_all_available_skills，推测读取共享池），不单独发布。

发布以目录为单位做整目录镜像（源多余文件全拷、目标多余文件删除）。
目标被视为发布产物：写入前若不一致，先备份到 backups/ 再覆盖。
"""

import filecmp
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
BACKUPS = ROOT / "backups"

def publishable_skills() -> list[tuple[str, Path]]:
    """可发布 skill = skills/（自有）与 vendor/（第三方，原样中转）下含 SKILL.md 的目录，自动扫描，不硬编码。"""
    out = []
    for base in (ROOT / "skills", ROOT / "vendor"):
        out += [(p.name, p) for p in base.iterdir()
                if p.is_dir() and (p / "SKILL.md").is_file()]
    return sorted(out)


POOLS = [HOME / ".agents" / "skills", HOME / ".codex" / "skills", HOME / ".claude" / "skills"]


def dir_same(a: Path, b: Path) -> bool:
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dir_same(a / s, b / s) for s in cmp.common_dirs)


def mirror(src: Path, dst: Path) -> None:
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    elif dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))


def main() -> None:
    check_only = "--check" in sys.argv
    drift = False
    for name, src in publishable_skills():
        for pool in POOLS:
            target = pool / name
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
                pool_name = target.parent.parent.name  # .agents / .claude
                shutil.copytree(target, BACKUPS / f"skill-{pool_name}-{name}-{ts}")
            mirror(src, target)
            print(f"[发布] {name:18s} {target}")
    if check_only and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
