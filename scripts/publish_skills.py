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

退役残留检测：池中存在、源中不存在的 skill 目录 = 退役时未清理的残留（如
security-review 退役后仍留在 ~/.config/opencode/skills）。--check 检出即失败；
发布模式只报告不删除（池内可能混有 SOURCES.md 登记「仅登记来源」的第三方
git 管理技能，不得误删），清理按报告清单人工执行。检测范围 = 3 个标准池 +
~/.config/opencode/skills（opencode 私有池，历史手动放置副本，发布不入但残留要查）。
"""

import filecmp
import re
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
EXTRA_RESIDUE_POOLS = [HOME / ".config" / "opencode" / "skills"]


def exempted_names() -> set[str]:
    """豁免名单 = SOURCES.md「仅登记来源（不拷贝实体）」节登记的技能（第三方 git 原地管理，非发布产物）。自动扫描，不硬编码。"""
    try:
        sources = (ROOT / "vendor" / "SOURCES.md").read_text(encoding="utf-8")
    except OSError:
        return set()
    names: set[str] = set()
    section = False
    for line in sources.splitlines():
        if line.startswith("## "):
            section = "仅登记来源" in line
            continue
        if section and line.startswith("|"):
            m = re.match(r"^\|\s*([a-z0-9][a-z0-9-]*)\s*\|", line)
            if m:
                names.add(m.group(1))
    return names


def residue_dirs() -> list[tuple[str, Path]]:
    """池中存在、源中不存在的 skill 目录 = 退役残留。"""
    tracked = {name for name, _ in publishable_skills()}
    exempt = exempted_names()
    out = []
    for pool in POOLS + EXTRA_RESIDUE_POOLS:
        if not pool.is_dir():
            continue
        for d in sorted(pool.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if d.name in tracked or d.name in exempt:
                continue
            out.append((d.name, d))
    return out


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
    residues = residue_dirs()
    for name, d in residues:
        print(f"[残留] {name:18s} {d}（源中不存在，退役未清；若是第三方 git 管理技能请登记 SOURCES.md 豁免）")
    if check_only and drift:
        sys.exit(1)
    if residues:
        if check_only:
            sys.exit(1)
        print("[注意] 存在退役残留，请按上方清单手动清理（本脚本不自动删除，防误删第三方技能）")


if __name__ == "__main__":
    main()
