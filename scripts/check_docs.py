#!/usr/bin/env python3
"""文档结构体检：验证 README 守住职责边界（面向人、只留门面、不越界）。

用法：
    python scripts/check_docs.py                     # 体检当前仓库，违规退出码 1
    python scripts/check_docs.py --readme 路径       # 检查其他项目的 README（多项目复用）

检查项：
    1. README 不含操作细节禁止词——防职责越界（发布命令/hook 安装/笔记格式等应只在 AGENTS.md）
    2. README 包含文档导航（"文档地图"或 "AGENTS.md"）——防瘦身过头失去导航
    3. README 徽章计数与实际一致——易变信息防漂移（仅存在 Skills 徽章且仓库含 skills//vendor/ 时生效）

行数不设硬上限（owner 2026-08-01 决策）：冗余与否按智能判断（结构正确、无明显冗长），
机器只管结构项。被 hooks/pre-commit 调用（doc-structure skill 的机械锚点）。
只读不写。违规时提示运行 doc-structure skill 修复。
"""

import argparse
import re
import sys
from pathlib import Path

# 操作细节禁止词：只属于 AGENTS.md（面向 Agent），出现在 README 即视为职责越界。
# 新增禁止词前先在 doc-structure skill 的验收标准里登记语义，避免误伤。
FORBIDDEN = [
    "两行元信息",
    "core.hooksPath",
    "scripts/sync.py",
    "pack.py",
    "publish_global.py",
    "publish_skills.py",
    "check_hooks.py",
    "registry.json",
    "失效测试",
    "静态验证",
    "双门槛",
    "月度评审",
    "模型换代",
    "废止块",
    "refs/original",
]

NAV_MARKERS = ["文档地图", "AGENTS.md"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--readme", default="README.md", help="README 路径（默认当前目录 README.md）")
    args = ap.parse_args()

    readme = Path(args.readme)
    if not readme.is_file():
        print(f"[doc-check] 错误：未找到 README：{readme}")
        return 1

    lines = readme.read_text(encoding="utf-8").splitlines()
    problems = []

    for word in FORBIDDEN:
        for i, line in enumerate(lines, 1):
            if word in line:
                problems.append(f"README 第 {i} 行含操作细节词「{word}」——职责越界，应移至 AGENTS.md 或专题文档")
                break

    if not any(marker in "\n".join(lines) for marker in NAV_MARKERS):
        problems.append("README 缺少文档导航（应含「文档地图」段或指向 AGENTS.md）——瘦身过头")

    # 徽章计数校验（owner 2026-08-04 归属 doc-structure：易变信息对齐与漂移纠正）
    badge = re.search(r"badge/Skills-(\d+)%20active", "\n".join(lines))
    if badge:
        root = readme.resolve().parent
        bases = [b for b in (root / "skills", root / "vendor") if b.is_dir()]
        if bases:
            actual = sum(1 for b in bases for p in b.iterdir()
                         if p.is_dir() and (p / "SKILL.md").is_file())
            declared = int(badge.group(1))
            if declared != actual:
                problems.append(f"README 徽章 Skills-{declared} 与实际可发布 skill 数 {actual} 不一致"
                                "——易变信息漂移，修正徽章数字")

    if problems:
        print("[doc-check] 文档体检未通过：")
        for p in problems:
            print(f"  - {p}")
        print("[doc-check] 请运行 doc-structure skill 按模板修复后重新体检。")
        return 1

    print(f"[doc-check] 通过：{readme} 职责边界无越界")
    return 0


if __name__ == "__main__":
    sys.exit(main())
