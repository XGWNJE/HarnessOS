#!/usr/bin/env python3
"""全机 CLI/环境/配置登记核验：对照 global/cli/registry.json 检查本机现状。

用法：
    python scripts/check_cli.py            # 核验，必需项缺失退出码 1

核验规则（只读不写，缺失按 registry 安装指引补装）：
    1. cli：必需项用 shutil.which 查找，缺失即失败；按需项缺失只报告
    2. 环境变量：必需项按名检查 os.environ（只查名不读值，密钥零暴露）
    3. 配置文件：必需项检查路径存在
"""

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "global" / "cli" / "registry.json"


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    problems, notes = [], []

    print("== CLI ==")
    for item in reg["cli"]:
        name = item["name"]
        found = shutil.which(name) is not None or item.get("现状", "").startswith("随")
        status = "存在" if found else "缺失"
        print(f"  [{status}] {name}（{item['分级']}）")
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
            problems.append(f"环境变量 {name} 未设置（设置者：{item['设置者']}）")

    print("== 配置文件 ==")
    for item in reg["配置文件"]:
        path = item["路径"]
        found = not path.startswith("git ") and Path(path).is_file()
        if path.startswith("git "):
            import subprocess
            r = subprocess.run(["git", "config", "--global", "--get-regexp", "user\\."],
                               capture_output=True, text=True)
            found = r.returncode == 0 and "user.email" in r.stdout and "user.name" in r.stdout
        print(f"  [{'存在' if found else '缺失'}] {item['name']}")
        if item["分级"] == "必需" and not found:
            problems.append(f"配置文件 {item['name']} 缺失（{path}）")

    if problems:
        print("\n[cli-check] 未通过：")
        for p in problems:
            print(f"  - {p}")
        for n in notes:
            print(f"  ~ {n}")
        return 1
    print("\n[cli-check] 通过：必需项齐全" + (f"；按需项缺失 {len(notes)} 个（见上）" if notes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
