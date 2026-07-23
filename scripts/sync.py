#!/usr/bin/env python3
"""HarnessOS 总入口：改完规则后跑这一条，完成全部发布与看板刷新。

用法：
    python scripts/sync.py            # 打包 + 发布 + 看板，全流程
    python scripts/sync.py --check    # 只做体检：检查漂移与待重建，不写入

流程：
    1. pack.py            打包有改动的 skill 为 .skill（同版本已存在则跳过，不视为失败）
    2. publish_global.py  发布全局规则到 4 个 Agent 读取位置
    3. publish_skills.py  发布自有 skill 到各 skill 目录
    4. dashboard.py       重新生成看板（--check 模式下跳过）
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(script: str, *args: str) -> bool:
    """返回是否全部顺利（pack 的「同版本已存在」退出码 1 视为跳过，不算失败）。"""
    r = subprocess.run([PY, str(ROOT / "scripts" / script), *args],
                       capture_output=True, text=True, encoding="utf-8")
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
        sys.exit(0 if ok else 1)
    print("== 1/4 打包 skill ==")
    ok = run("pack.py")
    print("== 2/4 发布全局规则 ==")
    ok &= run("publish_global.py")
    print("== 3/4 发布 skill 目录 ==")
    ok &= run("publish_skills.py")
    print("== 4/4 刷新看板 ==")
    ok &= run("dashboard.py")
    print("\n[完成] 全部同步" if ok else "\n[注意] 部分步骤有警告，见上方输出")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
