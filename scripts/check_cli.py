#!/usr/bin/env python3
"""全机 CLI/环境/配置登记核验：对照 global/cli/registry.json 检查本机现状。

用法：
    python scripts/check_cli.py            # 核验，必需项缺失退出码 1

核验规则（只读不写，缺失按 registry 安装指引补装）：
    1. cli：必需项用 shutil.which 查找，缺失即失败；按需项缺失只报告；
       平台字段过滤（win-only 项在 mac 不查）；「随附于」字段跟随其依赖项存在性
    2. 环境变量：必需项按名检查 os.environ（只查名不读值，密钥零暴露）
    3. 配置文件：路径以 ~ 相对 home（win/mac 同构），必需项检查存在
    4. 快照密钥扫描：config-snapshots/ 含明文密钥（sk-/Bearer 模式）即失败
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "global" / "cli" / "registry.json"
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"


def platform_ok(platforms: list) -> bool:
    if not platforms:
        return True
    if IS_WIN:
        return "win" in platforms
    if IS_MAC:
        return "mac" in platforms
    return True


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    problems, notes = [], []

    print("== CLI ==")
    for item in reg["cli"]:
        name = item["name"]
        if not platform_ok(item.get("平台", [])):
            print(f"  [跳过] {name}（平台 {item['平台']} 不适用本机）")
            continue
        if "随附于" in item:
            dep_found = shutil.which(item["随附于"]) is not None
            found = dep_found
            print(f"  [{'存在' if found else '缺失'}] {name}（随附于 {item['随附于']}）")
        else:
            found = shutil.which(name) is not None
            print(f"  [{'存在' if found else '缺失'}] {name}（{item['分级']}）")
        if item["分级"] == "必需" and not found:
            problems.append(f"CLI {name} 缺失（安装：{item['安装']}）")
        elif item["分级"] == "按需" and not found:
            notes.append(f"CLI {name} 缺失（按需，安装：{item['安装']}）")

    print("== 环境变量 ==")
    for item in reg["环境变量"]:
        name = item["name"]
        found = name in os.environ
        print(f"  [{'已设置' if found else '未设置'}] {name}")
        if item["分级"] == "必需" and not found:
            problems.append(f"环境变量 {name} 未设置（指引：{item['设置者']}）")

    print("== 配置文件 ==")
    for item in reg["配置文件"]:
        path = item["路径"]
        if path.startswith("git "):
            try:
                r = subprocess.run(["git", "config", "--global", "--get-regexp", r"user\."],
                                   capture_output=True, text=True)
                found = r.returncode == 0 and "user.email" in r.stdout and "user.name" in r.stdout
            except FileNotFoundError:
                found = False
        else:
            found = Path(path).expanduser().is_file()
        print(f"  [{'存在' if found else '缺失'}] {item['name']}")
        if item["分级"] == "必需" and not found:
            problems.append(f"配置文件 {item['name']} 缺失（{path}）")

    print("== 快照密钥扫描 ==")
    snap_dir = ROOT / "global" / "config-snapshots"
    secret_re = re.compile(r"sk-[A-Za-z0-9]{8,}|Bearer\s+[A-Za-z0-9_-]{10,}|token\s*[=:]\s*[\"']?[A-Za-z0-9_-]{16,}",
                           re.IGNORECASE)
    leak = False
    if snap_dir.is_dir():
        for f in sorted(snap_dir.iterdir()):
            if f.is_file():
                hit = secret_re.search(f.read_text(encoding="utf-8", errors="replace"))
                if hit:
                    leak = True
                    problems.append(f"快照 {f.name} 含疑似密钥（{hit.group(0)[:20]}...）")
                    print(f"  [泄露] {f.name}")
                else:
                    print(f"  [干净] {f.name}")
    else:
        print("  [无目录] config-snapshots 不存在")

    if problems:
        print("\n[cli-check] 未通过：")
        for p in problems:
            print(f"  - {p}")
        for n in notes:
            print(f"  ~ {n}")
        return 1
    print("\n[cli-check] 通过：必需项齐全，快照无密钥残留" + (f"；按需项缺失 {len(notes)} 个（见上）" if notes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
