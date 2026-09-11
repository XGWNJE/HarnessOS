#!/usr/bin/env python3
"""Batch-check the upstream channel version registered for each managed asset.

Only queries the channel recorded in the asset's ``[upstream]`` table, at most
one request per asset.  ``official-page`` assets still need a human look,
``launcher`` assets are anchored to the local launcher, and ``unavailable``
assets have no checkable channel.  The report is read-only: no record, catalog
or installed software is modified by this script.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import Catalog, _configure_output_encoding  # noqa: E402

REQUEST_TIMEOUT = 30


def _http_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "HarnessOS-versions/1.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.load(response)


def _run(command: list[str]) -> str:
    executable = shutil.which(command[0]) or command[0]
    result = subprocess.run(
        [executable, *command[1:]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=REQUEST_TIMEOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "命令失败").strip().splitlines()[-1])
    return result.stdout


def latest_winget(identifier: str) -> str:
    output = _run([
        "winget", "show", "--id", identifier, "--exact",
        "--source", "winget", "--accept-source-agreements",
    ])
    match = re.search(r"^(?:Version|版本):\s*(\S+)", output, re.M)
    if not match:
        raise RuntimeError("winget 输出中未找到版本")
    return match.group(1)


def latest_npm(identifier: str) -> str:
    return _run(["npm", "view", identifier, "version"]).strip().splitlines()[-1].strip()


def latest_pypi(identifier: str) -> str:
    return str(_http_json(f"https://pypi.org/pypi/{identifier}/json")["info"]["version"])


def latest_github_releases(identifier: str) -> str:
    data = _http_json(f"https://api.github.com/repos/{identifier}/releases/latest")
    return str(data["tag_name"]).removeprefix("v")


def latest_store(identifier: str) -> str:
    data = _http_json(
        "https://displaycatalog.mp.microsoft.com/v7.0/products"
        f"?bigIds={identifier}&market=US&languages=en-us,neutral"
    )
    products = data.get("Products") or []
    if not products:
        raise RuntimeError("displaycatalog 未返回产品")
    versions: set[str] = set()
    for sku in products[0].get("DisplaySkuAvailabilities", []):
        for properties in (
            sku.get("Properties", {}),
            sku.get("Sku", {}).get("Properties", {}),
        ):
            for package in properties.get("Packages", []):
                parts = str(package.get("PackageFullName", "")).split("_")
                if len(parts) > 2 and re.fullmatch(r"[0-9.]+", parts[1]):
                    versions.add(parts[1])
    if not versions:
        raise RuntimeError("displaycatalog 未返回包版本")
    return max(versions, key=lambda value: tuple(int(part) for part in value.split(".")))


def latest_nodejs_lts() -> str:
    entries = _http_json("https://nodejs.org/dist/index.json")
    for entry in entries:
        if entry.get("lts"):
            return str(entry["version"]).removeprefix("v")
    raise RuntimeError("dist index 中未找到 LTS 版本")


def latest_official_api(identifier: str) -> str:
    if "nodejs.org/dist/index.json" in identifier:
        return latest_nodejs_lts()
    raise RuntimeError("未实现的官方接口，请在 versions.py 中补充解析器")


CHECKERS: dict[str, Callable[[str], str]] = {
    "winget": latest_winget,
    "npm": latest_npm,
    "pypi": latest_pypi,
    "github-releases": latest_github_releases,
    "store": latest_store,
    "official-api": latest_official_api,
}
SKIP_STATUS = {
    "official-page": "需人工查看官方页面",
    "launcher": "以本机启动器为准",
    "unavailable": "无渠道",
}


def main() -> int:
    _configure_output_encoding()
    catalog = Catalog(Path(__file__).resolve().parent.parent).load()
    if catalog.problems:
        for problem in catalog.problems:
            print(f"ERROR: {problem.display(catalog.root)}", file=sys.stderr)
        return 1
    rows: list[tuple[str, str, str, str, str]] = []
    for asset in sorted(catalog.assets.values(), key=lambda item: item.id):
        data = asset.data or {}
        if not asset.upstream_updates:
            continue
        channel = str(data.get("upstream_channel", ""))
        identifier = str(data.get("upstream_identifier", ""))
        registered = str(data.get("upstream_latest_stable", ""))
        if not channel:
            continue
        if channel in SKIP_STATUS:
            rows.append((asset.id, channel, registered or "—", "—", SKIP_STATUS[channel]))
            continue
        checker = CHECKERS.get(channel)
        if checker is None:
            rows.append((asset.id, channel, registered or "—", "—", "未知渠道"))
            continue
        try:
            current = checker(identifier)
        except Exception as exc:  # noqa: BLE001 - 报告层需要吞掉单资产失败
            rows.append((asset.id, channel, registered or "—", "—", f"查询失败: {exc}"))
            continue
        if not registered:
            status = "首查"
        elif current == registered:
            status = "一致"
        else:
            status = "可更新"
        rows.append((asset.id, channel, registered or "—", current, status))
    width_id = max((len(row[0]) for row in rows), default=10) + 2
    print(f"{'资产':<{width_id}}{'渠道':<16}{'登记':<18}{'渠道当前':<18}状态")
    for asset_id, channel, registered, current, status in rows:
        print(f"{asset_id:<{width_id}}{channel:<16}{registered:<18}{current:<18}{status}")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[4]] = counts.get(row[4], 0) + 1
    print(f"\n共 {len(rows)} 条跟踪上游的资产：" + "，".join(f"{key} {value}" for key, value in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
