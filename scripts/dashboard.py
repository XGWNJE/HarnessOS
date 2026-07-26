#!/usr/bin/env python3
"""扫描仓库当前状态，生成单文件看板 dashboard.html。

用法：
    python scripts/dashboard.py     # 重新生成 dashboard.html

设计原则：单屏全局概览，布局对齐流水线框架——
    输入三通道（抓 observer→inbox / 喂 notes / 拿 vendor）
    → 产物三类（约束规则 global / 技能 skills / hook 机制强制）
    → 生命周期（待处理清单）。
只展示「需要关注的状态」，不堆砌历史细节——细节回仓库查 CHANGELOG 和源文件。
数据来源全部是仓库源文件与登记表本身，看板不维护任何自己的状态。
"""

import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
OUT = ROOT / "dashboard.html"

PUBLISH_TARGETS = [
    ("home",            HOME / "AGENTS.md",                    None),
    ("Codex",           HOME / ".codex" / "AGENTS.md",         None),
    ("OpenCode",        HOME / ".config" / "opencode" / "AGENTS.md", None),
    ("Claude Code",     HOME / ".claude" / "CLAUDE.md",        "claude"),
]


def own_skills() -> list[str]:
    """自有 skill = skills/ 下含 SKILL.md 的目录，自动扫描（与 publish_skills.py 同一口径）。"""
    return sorted(p.name for p in (ROOT / "skills").iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


SKILL_POOLS = [HOME / ".agents" / "skills", HOME / ".codex" / "skills", HOME / ".claude" / "skills"]

SKILL_PUBLISH = [
    (name, pool / name)
    for name in own_skills()
    for pool in SKILL_POOLS
]


SESSION_LOGS = [
    HOME / ".claude" / "projects",
    HOME / ".codex" / "sessions",
    HOME / ".kimi-code" / "sessions",
]

REGISTRY = ROOT / "global" / "hooks" / "registry.json"


def dir_same(a, b) -> bool:
    import filecmp
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dir_same(a / s, b / s) for s in cmp.common_dirs)


def collect_usage(names: list[str]) -> dict[str, dict]:
    """扫描各 Agent 会话日志，统计 skill 名的近似使用次数与最后使用时间。
    说明：日志出现 ≠ 精确调用（可能是索引注入或提及），作为热度近似值足够。"""
    usage = {n: {"count": 0, "last": 0.0} for n in names}
    for base in SESSION_LOGS:
        if not base.is_dir():
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.endswith((".jsonl", ".json")):
                    continue
                p = Path(dirpath) / fn
                try:
                    if p.stat().st_size > 20 * 1024 * 1024:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for n in names:
                    c = text.count(n)
                    if c:
                        usage[n]["count"] += c
                        usage[n]["last"] = max(usage[n]["last"], p.stat().st_mtime)
    return usage


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta


def collect_skills(base: Path) -> list[dict]:
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        f = d / "SKILL.md"
        if not d.is_dir() or not f.exists():
            continue
        meta = parse_frontmatter(f.read_text(encoding="utf-8"))
        out.append({"dir": d.name, "name": meta.get("name", d.name),
                    "version": meta.get("version", "?")})
    return out


def collect_builds() -> dict[str, str]:
    out = {}
    dist = ROOT / "dist"
    if dist.is_dir():
        for f in sorted(dist.glob("*.skill")):
            m = re.match(r"(.+)-([\d.]+)\.skill$", f.name)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def collect_skill_publish() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for name, target in SKILL_PUBLISH:
        src = ROOT / "skills" / name
        root = str(target.parent.parent)
        pool = "Claude 池" if ".claude" in root else ("Codex 池" if ".codex" in root else "共享池")
        out.setdefault(name, []).append({
            "pool": pool, "sync": src.is_dir() and dir_same(src, target)})
    return out


def collect_notes() -> list[dict]:
    out = []
    notes_dir = ROOT / "notes"
    if not notes_dir.is_dir():
        return out
    for f in sorted(notes_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        items = re.findall(r"^- .+", text, re.M)
        distilled = [i for i in items if "已提炼进" in i or "已废止" in i]
        targets = sorted(set(re.findall(r"已提炼进 ([\w\-]+)", text)))
        out.append({"file": f.name, "total": len(items),
                    "distilled": len(distilled), "targets": targets})
    return out


def collect_inbox() -> dict:
    """① 抓：observer 静默写入的原料区（notes/inbox/）统计。"""
    inbox = ROOT / "notes" / "inbox"
    files = sorted(inbox.glob("*.md")) if inbox.is_dir() else []
    entries = 0
    types: dict[str, int] = {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        entries += len(re.findall(r"^## .+", text, re.M))
        for t in re.findall(r"> 类型：(\S+)", text):
            types[t] = types.get(t, 0) + 1
    return {"files": len(files), "entries": entries, "types": types,
            "latest": files[-1].stem if files else "—"}


def collect_global() -> dict:
    f = ROOT / "global" / "AGENTS.md"
    text = f.read_text(encoding="utf-8")
    version = (re.search(r"版本：v?([\d.]+)", text) or [None, "?"])[1]
    targets = []
    for label, target, overlay in PUBLISH_TARGETS:
        want = text.rstrip()
        if overlay:
            want += "\n\n---\n\n" + (ROOT / "global" / "overlays" / f"{overlay}.md").read_text(encoding="utf-8")
        current = target.read_text(encoding="utf-8") if target.exists() else None
        targets.append({"label": label, "overlay": overlay or "",
                        "sync": current is not None and current.rstrip() == want.rstrip()})
    return {"version": version, "targets": targets}


def collect_hooks() -> dict:
    """hook 产物：对照 registry.json 逐条体检（复用 check_hooks 的注册点读取）。"""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries: dict[str, list[dict]] = {}
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import check_hooks
        entries = {"kimi-code": check_hooks.kimi_entries(),
                   "codex": check_hooks.codex_entries()}
    except Exception:
        pass  # 注册点不可读时只体检源文件存在性
    rows = []
    n_ok = 0
    for r in reg["registrations"]:
        src = Path(r["source"])
        ok = src.exists()
        if ok and r["runtime"] in entries:
            base = src.name
            hit = next((e for e in entries[r["runtime"]]
                        if e.get("event") == r["event"] and base in e.get("command", "")), None)
            ok = hit is not None and (r.get("matcher") is None or hit.get("matcher") == r["matcher"])
        n_ok += ok
        rows.append({"runtime": r["runtime"], "event": r["event"],
                     "matcher": r.get("matcher") or "—", "source": src.name,
                     "owner": r.get("owner", "?"), "sync": ok})
    return {"rows": rows, "ok": n_ok, "total": len(rows)}


def collect_githook() -> bool:
    """本仓库 pre-commit 体检钩子是否已安装（core.hooksPath = hooks）。"""
    try:
        out = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                             cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() == "hooks"
    except Exception:
        return False


def collect_freeze() -> dict | None:
    """框架冷冻期（项目 AGENTS.md 工作规则）：解析「至 YYYY-MM-DD」。"""
    f = ROOT / "AGENTS.md"
    if not f.exists():
        return None
    m = re.search(r"冷冻期[^\n]*?至 (\d{4}-\d{2}-\d{2})", f.read_text(encoding="utf-8"))
    if not m:
        return None
    end = date.fromisoformat(m.group(1))
    return {"end": m.group(1), "days": (end - date.today()).days}


def collect_changelog() -> dict:
    f = ROOT / "CHANGELOG.md"
    if not f.exists():
        return {"latest": "—", "count": 0}
    text = f.read_text(encoding="utf-8")
    entries = re.findall(r"^## (.+)$", text, re.M)
    return {"latest": entries[0] if entries else "—", "count": len(entries)}


def badge(ok: bool) -> str:
    return ('<span class="b ok">同步</span>' if ok else '<span class="b bad">漂移</span>')


def render() -> str:
    skills = collect_skills(ROOT / "skills")
    vendor = collect_skills(ROOT / "vendor")
    notes = collect_notes()
    inbox = collect_inbox()
    g = collect_global()
    hooks = collect_hooks()
    githook = collect_githook()
    freeze = collect_freeze()
    log = collect_changelog()
    builds = collect_builds()
    pubs = collect_skill_publish()
    usage = collect_usage([s["name"] for s in skills])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    now_ts = time.time()

    alerts = []

    # ---- ① 输入：inbox（抓） ----
    types_txt = " · ".join(f"{esc(k)} {v}" for k, v in inbox["types"].items()) or "无类型标注"
    inbox_html = (f'{inbox["files"]} 个文件 / {inbox["entries"]} 条原料（{types_txt}）'
                  f' · 最新 {esc(inbox["latest"])} · 归并提炼由 owner 主动发起评审')

    # ---- ① 输入：notes（喂） ----
    note_rows = "".join(
        f'<tr><td class="mono">{esc(n["file"])}</td>'
        f'<td><span class="bar"><span style="width:{(n["distilled"]/n["total"]*100 if n["total"] else 0):.0f}%"></span></span>'
        f'{n["distilled"]}/{n["total"]}</td>'
        f'<td class="dim">{esc("、".join(n["targets"])) or "待提炼"}</td></tr>'
        for n in notes)

    # ---- ① 输入：vendor（拿） ----
    vendor_txt = "、".join(f'{v["name"]} v{v["version"]}' for v in vendor)

    # ---- ② 产物：技能矩阵 ----
    matrix_rows = ""
    for s in skills:
        built = builds.get(s["name"])
        if built == s["version"]:
            build_html = f'<span class="b ok">v{built}</span>'
        elif built:
            build_html = f'<span class="b warn">旧 v{built}</span>'
            alerts.append(f"{s['name']} 需重新打包（源 v{s['version']}）")
        else:
            build_html = '<span class="b off">无包</span>'
        pub_html = " ".join(f'{p["pool"]}{badge(p["sync"])}' for p in pubs.get(s["dir"], []))
        if not pub_html:
            pub_html = '<span class="dim">仅 .skill 包</span>'
        for p in pubs.get(s["dir"], []):
            if not p["sync"]:
                alerts.append(f"{s['name']} {p['pool']}漂移，需 publish_skills")
        u = usage.get(s["name"], {"count": 0, "last": 0.0})
        if u["last"]:
            days = int((now_ts - u["last"]) / 86400)
            ago = "今天" if days == 0 else f"{days} 天前"
            usage_html = f'{u["count"]} 次 · {ago}'
            if days > 90:
                alerts.append(f"{s['name']} 已 {days} 天无使用记录，下次月度评审考虑退役")
        else:
            usage_html = '<span class="dim">0 次</span>'
        matrix_rows += (f'<tr><td class="mono">{esc(s["name"])}</td><td>v{esc(s["version"])}</td>'
                        f'<td>{build_html}</td><td>{pub_html}</td><td class="dim">{usage_html}</td></tr>')

    # ---- ② 产物：全局规则 ----
    g_badges = " ".join(f'{t["label"]}{"*" if t["overlay"] else ""}{badge(t["sync"])}' for t in g["targets"])
    for t in g["targets"]:
        if not t["sync"]:
            alerts.append(f"全局规则 {t['label']} 漂移，需 publish_global")

    # ---- ② 产物：hook ----
    hook_rows = "".join(
        f'<tr><td class="mono">{esc(r["runtime"])}</td><td>{esc(r["event"])}</td>'
        f'<td class="mono">{esc(r["source"])}</td><td class="dim">{esc(r["owner"])}</td>'
        f'<td class="dim mono">{esc(r["matcher"][:24])}</td><td>{badge(r["sync"])}</td></tr>'
        for r in hooks["rows"])
    for r in hooks["rows"]:
        if not r["sync"]:
            alerts.append(f"hook {r['runtime']} {r['event']} {r['source']} 漂移，按 registry.json 修复")
    if not githook:
        alerts.append("本仓库 pre-commit 体检钩子未安装：git config core.hooksPath hooks")
    githook_html = ('<span class="b ok">已安装</span>' if githook else '<span class="b bad">未安装</span>')

    # ---- KPI ----
    n_sync = sum(t["sync"] for t in g["targets"]) + sum(p["sync"] for ps in pubs.values() for p in ps)
    n_total = len(g["targets"]) + sum(len(ps) for ps in pubs.values())

    alerts_html = "".join(f"<li>{esc(a)}</li>" for a in alerts)
    alerts_block = (f'<div class="alerts"><b>待处理（{len(alerts)}）</b><ul>{alerts_html}</ul></div>'
                    if alerts else '<div class="allok">✓ 所有发布点与源文件一致，无待处理事项</div>')

    freeze_txt = ""
    if freeze:
        freeze_txt = (f' · 框架冷冻期至 {freeze["end"]}（剩 {freeze["days"]} 天）' if freeze["days"] > 0
                      else f' · 框架冷冻期已于 {freeze["end"]} 期满')

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarnessOS 看板</title>
<style>
  :root {{ --ink:#20242a; --dim:#828a94; --line:#e6e4de; --accent:#b3541e; --ok:#1a7f4b; --bad:#b91c1c; --warn:#a16207; --bg:#fafaf7; }}
  * {{ margin:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); font-size:13px; line-height:1.55; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:28px 20px 40px; }}
  header {{ display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:4px; }}
  h1 {{ font-size:20px; }}
  header .sub {{ color:var(--dim); font-size:11px; }}
  .kpis {{ display:flex; gap:10px; margin:16px 0 18px; flex-wrap:wrap; }}
  .kpi {{ flex:1; min-width:110px; border:1px solid var(--line); border-radius:8px; padding:10px 12px; background:#fff; }}
  .kpi .n {{ font-size:20px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .kpi .l {{ font-size:11px; color:var(--dim); }}
  h2 {{ font-size:12px; color:var(--dim); font-weight:600; letter-spacing:.08em; margin:18px 0 6px; text-transform:uppercase; }}
  h2 .tag {{ color:var(--accent); }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
  td,th {{ padding:6px 10px; border-bottom:1px solid var(--line); text-align:left; font-size:12px; }}
  th {{ color:var(--dim); font-weight:600; background:#f5f4f0; }}
  tr:last-child td {{ border-bottom:none; }}
  .mono {{ font-family:ui-monospace,Consolas,monospace; font-size:11.5px; }}
  .dim {{ color:var(--dim); }}
  .b {{ font-size:10.5px; padding:1px 7px; border-radius:99px; font-weight:600; margin-left:4px; white-space:nowrap; }}
  .b.ok {{ background:#e4f4ec; color:var(--ok); }}
  .b.bad {{ background:#fbe7e7; color:var(--bad); }}
  .b.warn {{ background:#fdf3e0; color:var(--warn); }}
  .b.off {{ background:#f0eee9; color:var(--dim); }}
  .bar {{ display:inline-block; width:64px; height:5px; background:#eceae4; border-radius:3px; margin-right:6px; vertical-align:middle; overflow:hidden; }}
  .bar span {{ display:block; height:100%; background:var(--accent); }}
  .alerts {{ border:1px solid #f0d9b5; background:#fffaf2; border-radius:8px; padding:8px 12px; margin-top:18px; }}
  .alerts b {{ color:var(--warn); font-size:12px; }}
  .alerts ul {{ margin:4px 0 0 18px; font-size:12px; }}
  .allok {{ border:1px solid #cde8da; background:#f2faf6; color:var(--ok); border-radius:8px; padding:8px 12px; margin-top:18px; font-size:12px; }}
  .row {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:8px 12px; margin-bottom:6px; }}
  .row .chan {{ font-weight:600; }}
  footer {{ margin-top:20px; font-size:11px; color:var(--dim); }}
  code {{ background:#f0eee9; padding:0 4px; border-radius:3px; font-size:11px; }}
</style></head><body><div class="wrap">
<header>
  <h1>HarnessOS 看板</h1>
  <div class="sub">scripts/dashboard.py 生成 · {now}{freeze_txt} · 细节查仓库 CHANGELOG 与源文件</div>
</header>

<div class="kpis">
  <div class="kpi"><div class="n">{n_sync}/{n_total}</div><div class="l">发布点同步</div></div>
  <div class="kpi"><div class="n">v{esc(g['version'])}</div><div class="l">全局规则</div></div>
  <div class="kpi"><div class="n">{len(skills)}</div><div class="l">自有 Skill</div></div>
  <div class="kpi"><div class="n">{hooks['ok']}/{hooks['total']}</div><div class="l">hook 注册同步</div></div>
  <div class="kpi"><div class="n">{inbox['entries']}</div><div class="l">inbox 原料（{inbox['types'].get('待确认', 0)} 待确认）</div></div>
  <div class="kpi"><div class="n">{len(alerts)}</div><div class="l">待处理</div></div>
</div>

<h2>① 输入 · 三通道</h2>
<div class="row"><span class="chan">抓 · observer → inbox</span> <span class="dim">{inbox_html}</span></div>
<table><tr><th>喂 · 笔记（notes/）</th><th>加工进度</th><th>去向</th></tr>{note_rows or '<tr><td class="dim">暂无</td></tr>'}</table>
<div class="row" style="margin-top:6px"><span class="chan">拿 · vendor 引入</span> <span class="dim">{esc(vendor_txt)}；另有 skill-creator（Anthropic 官方，仅登记）</span></div>

<h2>② 产物 · 约束规则（global）</h2>
<div class="row">v{esc(g['version'])} · {g_badges} <span class="dim">· * = 含 Claude overlay · Kimi Code 无全局注入，不发布</span></div>

<h2>② 产物 · 技能（skills）</h2>
<table><tr><th>Skill</th><th>源版本</th><th>.skill 包</th><th>目录发布</th><th>使用热度（近似）</th></tr>{matrix_rows}</table>

<h2>② 产物 · hook（机制强制）</h2>
<table><tr><th>运行时</th><th>事件</th><th>源</th><th>属主</th><th>matcher</th><th>状态</th></tr>{hook_rows}</table>
<div class="row dim" style="margin-top:6px">本仓库 git hook：pre-commit 体检硬卡点 {githook_html} <span class="dim">· 登记事实源 global/hooks/registry.json，体检 scripts/check_hooks.py（已并入 sync.py）</span></div>

<h2>最近动态</h2>
<div class="row dim">{esc(log['latest'])}（共 {log['count']} 条，见 CHANGELOG.md）</div>

{alerts_block}

<footer>生成产物，不手改。数据变化后运行 <code>python scripts/sync.py</code>（或单独 <code>dashboard.py</code>）重新生成；修复漂移运行对应 publish 脚本。</footer>
</div></body></html>"""


def main() -> None:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[完成] {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
