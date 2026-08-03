#!/usr/bin/env python3
"""HarnessOS 装机脚本：新环境一键完成「环境变量 + 发布 + 体检」。

用法：
    python scripts/install.py

做的事（幂等，可重复运行）：
    1. 写用户级环境变量 HARNESSOS_ROOT = 本仓库根目录
       （Windows 用 setx；Linux/macOS 追加 export 到 ~/.bashrc 与 ~/.profile，查重跳过）
    2. python scripts/sync.py（打包 + 发布全局规则与 skills）
    3. git config core.hooksPath hooks（启用提交体检钩子）
    4. 体检三件套：sync.py --check、check_docs.py、check_hooks.py
    5. 打印 hook 注册指引（只打印不写入——hook 注册维持手工，check_hooks.py 只读体检）

任一步失败即停并报告。规则/skill 文本中的路径一律读 HARNESSOS_ROOT，
未设置时按 harness-observer skill 的寻址链兜底（本脚本就是「设置」的那一环）。
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_NAME = "HARNESSOS_ROOT"


def run(cmd: list[str], label: str) -> None:
    print(f"\n== {label} ==")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"[install] 失败：{label}（退出码 {r.returncode}），已停止，请修复后重跑。")
        sys.exit(1)


def set_env() -> str:
    root = str(ROOT)
    if os.environ.get(ENV_NAME) == root:
        return f"{ENV_NAME} 已设置且指向本仓库，跳过"
    if platform.system() == "Windows":
        # setx 只影响新进程，os.environ 查不到刚写入的值——先查注册表里的持久化值保证幂等
        q = subprocess.run(["reg", "query", r"HKCU\Environment", "/v", ENV_NAME],
                           capture_output=True, text=True)
        if q.returncode == 0 and root in q.stdout:
            return f"{ENV_NAME} 已设置且指向本仓库，跳过"
        # setx 写入用户级注册表，新进程生效；>1024 字符会被截断，路径短无此问题
        r = subprocess.run(["setx", ENV_NAME, root], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[install] 失败：setx {ENV_NAME}（{r.stderr.strip()}）")
            sys.exit(1)
        return f"{ENV_NAME}={root} 已写入（用户级，当前会话需重开终端生效）"
    # Linux/macOS：追加 export 到已有 shell 配置文件，查重
    line = f'export {ENV_NAME}="{root}"'
    written = []
    for rc in (Path.home() / ".bashrc", Path.home() / ".profile"):
        if rc.is_file():
            if f"{ENV_NAME}=" in rc.read_text(encoding="utf-8", errors="replace"):
                continue
            with rc.open("a", encoding="utf-8") as f:
                f.write(f"\n# HarnessOS 根目录（scripts/install.py 写入）\n{line}\n")
            written.append(str(rc))
    if written:
        return f"{ENV_NAME}={root} 已追加到 {', '.join(written)}（当前会话需 source 或重开终端生效）"
    return f"未找到 ~/.bashrc 或 ~/.profile，请手动设置：{line}"


def hook_guide() -> None:
    registry = json.loads((ROOT / "global" / "hooks" / "registry.json").read_text(encoding="utf-8"))
    own = [r for r in registry.get("registrations", []) if r.get("owner") == "HarnessOS"]
    if not own:
        return
    print("\n== hook 注册指引（手工，维持现状不自动写入）==")
    print("以下 HarnessOS 自有 hook 需注册到对应运行时（注册后跑 scripts/check_hooks.py 体检）：")
    for r in own:
        src = Path(r["source"])
        # registry 记录的是旧机器路径；按运行时根目录取相对部分拼新路径
        try:
            rel = src.relative_to(src.anchor + "ObjectCode/HarnessOS")
        except ValueError:
            rel = Path(*src.parts[-3:])  # global/hooks/xxx.py
        new_src = ROOT / rel
        matcher = f'，matcher = "{r["matcher"]}"' if r.get("matcher") else ""
        print(f"  - {r['runtime']} {r['event']}{matcher} -> {new_src}")


def main() -> None:
    print(f"[install] HarnessOS 根目录：{ROOT}")
    print(f"[install] 环境变量：{set_env()}")
    run([sys.executable, "scripts/sync.py"], "发布（打包 + 全局 + skills）")
    run(["git", "config", "core.hooksPath", "hooks"], "启用提交体检钩子")
    run([sys.executable, "scripts/sync.py", "--check"], "体检 1/3：发布漂移")
    run([sys.executable, "scripts/check_docs.py"], "体检 2/3：文档结构")
    run([sys.executable, "scripts/check_hooks.py"], "体检 3/3：hook 登记")
    hook_guide()
    print("\n[install] 完成。全部体检通过。")


if __name__ == "__main__":
    main()
