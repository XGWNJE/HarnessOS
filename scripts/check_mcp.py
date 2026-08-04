#!/usr/bin/env python3
"""全机 MCP 登记体检：对照 global/mcp/registry.json 校验各工具实际 MCP 配置。

用法：
    python scripts/check_mcp.py            # 体检，漂移退出码 1

校验规则（只读不写，漂移按登记表手工修复）：
    1. registry 登记的 (工具, server) 必须存在于该工具实际配置
    2. 实际配置里出现的 server 必须已登记（工具自带名单除外）
    3. 与 hook 体检（check_hooks.py）同构，已并入 sync.py 两种模式
"""

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "global" / "mcp" / "registry.json"


def load_config(spec: dict):
    p = Path(spec["path"])
    if not p.is_file():
        return None
    if spec.get("格式") == "toml":
        with open(p, "rb") as f:
            return tomllib.load(f)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    tools = reg["工具配置"]
    servers = reg["servers"]
    problems = []
    for tname, spec in tools.items():
        cfg = load_config(spec)
        key = spec.get("键")
        actual = set()
        if cfg is not None and key and key in cfg:
            actual = set(cfg[key].keys())
        builtin = set(spec.get("工具自带", []))
        expected = {s["name"] for s in servers if tname in s.get("工具", [])}
        missing = expected - actual
        if missing:
            problems.append(f"{tname}: 配置缺失登记过的 MCP {sorted(missing)}")
        extra = actual - expected - builtin
        if extra:
            problems.append(f"{tname}: 配置存在未登记的 MCP {sorted(extra)}（登记进 registry 或列入工具自带）")
    if problems:
        print("[mcp-check] 未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[mcp-check] 通过：各工具 MCP 配置与 registry 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
