#!/usr/bin/env python3
"""HarnessOS 总入口：改完规则后跑这一条，完成全部发布。

用法：
    python scripts/sync.py            # 打包 + 发布，全流程
    python scripts/sync.py --check    # 只做体检：检查漂移与待重建，不写入

流程：
    1. pack.py            打包有改动的 skill 为 .skill（同版本已存在则跳过，不视为失败）
    2. publish_global.py  发布全局规则到 4 个 Agent 读取位置
    3. publish_skills.py  发布自有 skill 到各 skill 目录

hook 登记体检（check_hooks.py）两种模式都跑：对照 global/hooks/registry.json
校验全机 Agent hook 注册点与源文件，漂移即失败。只读不写，漂移按登记表手工修复。
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

# 让子脚本统一以 UTF-8 输出，避免 Windows GBK 控制台下解码崩溃
CHILD_ENV = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run(script: str, *args: str) -> bool:
    """返回是否全部顺利（pack 的「同版本已存在」退出码 1 视为跳过，不算失败）。"""
    r = subprocess.run([PY, str(ROOT / "scripts" / script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=CHILD_ENV)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.splitlines():
        if line.strip():
            print(f"  {line}")
    if r.returncode != 0:
        print(f"  [警告] {script} 退出码 {r.returncode}")
        return False
    return True


def main() -> None:
    check = "--check" in sys.argv
    if check:
        print("== 体检（不写入）==")
        ok = run("publish_global.py", "--check")
        ok &= run("publish_skills.py", "--check")
        print("== hook 登记体检 ==")
        ok &= run("check_hooks.py")
        print("== MCP 登记体检 ==")
        ok &= run("check_mcp.py")
        sys.exit(0 if ok else 1)
    print("== 1/3 打包 skill ==")
    ok = run("pack.py")
    print("== 2/3 发布全局规则 ==")
    ok &= run("publish_global.py")
    print("== 3/3 发布 skill 目录 ==")
    ok &= run("publish_skills.py")
    print("== hook 登记体检 ==")
    ok &= run("check_hooks.py")
    print("== MCP 登记体检 ==")
    ok &= run("check_mcp.py")
    print("\n[完成] 全部同步" if ok else "\n[注意] 部分步骤有警告，见上方输出")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
