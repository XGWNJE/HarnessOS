#!/usr/bin/env python3
"""把 skills/（自有）或 vendor/（引入）下的 skill 目录打包为 .skill 文件。

用法：
    python scripts/pack.py                # 打包全部（skills/ + vendor/）
    python scripts/pack.py ai-stack-harness keel   # 只打包指定 skill

产物输出到 dist/<name>-<version>.skill（zip 格式）。
若同名同版本产物已存在则报错，提醒先升版本号——配合「改动即 +1」的纪律。
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIRS = [ROOT / "skills", ROOT / "vendor"]
DIST = ROOT / "dist"


def read_meta(skill_dir: Path) -> tuple[str, str] | None:
    """frontmatter 缺 name/version 时返回 None（vendor 引入 skill 可不规范，跳过）。"""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    name = re.search(r"^name:\s*(.+)$", text, re.M)
    version = re.search(r"^version:\s*(.+)$", text, re.M)
    if not (name and version):
        return None
    return name.group(1).strip(), version.group(1).strip()


def pack(skill_dir: Path) -> Path | None:
    """已存在同版本包或 frontmatter 不规范时返回 None（跳过），不中断其余 skill。"""
    meta = read_meta(skill_dir)
    if meta is None:
        print(f"[跳过] {skill_dir.name}（frontmatter 无 name/version，通常为 vendor 引入）")
        return None
    name, version = meta
    out = DIST / f"{name}-{version}.skill"
    if out.exists():
        print(f"[跳过] {out.name} 已存在（无版本变更）")
        return None
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(skill_dir))
    return out


def main() -> None:
    wanted = set(sys.argv[1:])
    dirs = [d for base in SRC_DIRS if base.is_dir() for d in sorted(base.iterdir()) if d.is_dir()]
    if wanted:
        dirs = [d for d in dirs if d.name in wanted]
        missing = wanted - {d.name for d in dirs}
        if missing:
            sys.exit(f"[错误] 未找到 skill：{', '.join(sorted(missing))}")
    if not dirs:
        sys.exit("[错误] 没有可打包的 skill")
    DIST.mkdir(exist_ok=True)
    for d in dirs:
        out = pack(d)
        if out:
            print(f"[完成] {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
