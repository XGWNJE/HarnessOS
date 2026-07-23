#!/usr/bin/env python3
"""扫描仓库当前状态，生成单文件看板 dashboard.html。

用法：
    python scripts/dashboard.py     # 重新生成 dashboard.html

数据来源全部是仓库源文件本身（skill frontmatter、笔记标注、CHANGELOG、
全局规则与发布点的一致性），看板不维护任何自己的状态——改了规则就跑一次本脚本。
"""

import html
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
OUT = ROOT / "dashboard.html"

PUBLISH_TARGETS = [
    ("home · ~/AGENTS.md",            HOME / "AGENTS.md",                    None),
    ("Codex · ~/.codex/AGENTS.md",    HOME / ".codex" / "AGENTS.md",         None),
    ("OpenCode · ~/.config/opencode/AGENTS.md", HOME / ".config" / "opencode" / "AGENTS.md", None),
    ("Claude Code · ~/.claude/CLAUDE.md", HOME / ".claude" / "CLAUDE.md",    "claude"),
]

SKILL_PUBLISH = [
    (name, HOME / ".agents" / "skills" / name)
    for name in ["grsai-image-gen", "init-project", "scope-guard", "vps-server-info"]
]
SKILL_PUBLISH.append(("vps-server-info", HOME / ".claude" / "skills" / "vps-server-info"))


def dir_same(a, b) -> bool:
    import filecmp
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(dir_same(a / s, b / s) for s in cmp.common_dirs)


def collect_skill_publish() -> dict[str, list[dict]]:
    """目录发布状态：skill 名 -> [{pool, path, sync}]。"""
    out: dict[str, list[dict]] = {}
    for name, target in SKILL_PUBLISH:
        src = ROOT / "skills" / name
        pool = "Claude 池 ~/.claude/skills" if ".claude" in str(target) else "共享池 ~/.agents/skills"
        out.setdefault(name, []).append({
            "pool": pool, "sync": src.is_dir() and dir_same(src, target)})
    return out


def collect_matrix(skills: list[dict]) -> list[dict]:
    """构建 × 发布矩阵：每个自有 skill 一行。"""
    builds = collect_builds()
    pubs = collect_skill_publish() or {}
    out = []
    for s in skills:
        built = builds.get(s["name"])
        if built == s["version"]:
            build = {"state": "ok", "text": f"v{built} 已打包（待手动导入 Kimi Code / Codex / Claude Code）"}
        elif built:
            build = {"state": "drift", "text": f"dist 里是旧版 v{built}，源已 v{s['version']}，需重新 pack"}
        else:
            build = {"state": "none", "text": "未打包"}
        out.append({**s, "build": build, "pubs": pubs.get(s["dir"], [])})
    return out


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta


def collect_skills(base: Path, own: bool) -> list[dict]:
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        f = d / "SKILL.md"
        if not d.is_dir() or not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        sources = sorted(set(re.findall(r"来源：([\w/.\-一-鿿]+\.md)", text)))
        rules = len(re.findall(r"^#{2,3} ", text, re.M))
        out.append({
            "dir": d.name,
            "name": meta.get("name", d.name),
            "version": meta.get("version", "?"),
            "desc": meta.get("description", ""),
            "rules": rules,
            "sources": sources,
            "own": own,
        })
    return out


def collect_builds() -> dict[str, str]:
    """dist/ 下已构建的 .skill 包：name -> 最新已构建版本。"""
    out = {}
    dist = ROOT / "dist"
    if dist.is_dir():
        for f in sorted(dist.glob("*.skill")):
            m = re.match(r"(.+)-([\d.]+)\.skill$", f.name)
            if m:
                out[m.group(1)] = m.group(2)
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
        out.append({
            "file": f.name,
            "title": (re.search(r"^# (.+)$", text, re.M) or [None, f.name])[1],
            "total": len(items),
            "distilled": len(distilled),
            "targets": targets,
        })
    return out


def collect_global() -> dict:
    f = ROOT / "global" / "AGENTS.md"
    text = f.read_text(encoding="utf-8")
    version = (re.search(r"版本：v?([\d.]+)", text) or [None, "?"])[1]
    sections = len(re.findall(r"^## ", text, re.M))
    overlays = sorted(p.stem for p in (ROOT / "global" / "overlays").glob("*.md"))
    targets = []
    for label, target, overlay in PUBLISH_TARGETS:
        want = text.rstrip()
        if overlay:
            want += "\n\n---\n\n" + (ROOT / "global" / "overlays" / f"{overlay}.md").read_text(encoding="utf-8")
        current = target.read_text(encoding="utf-8") if target.exists() else None
        targets.append({"label": label, "path": str(target),
                        "sync": current is not None and current.rstrip() == want.rstrip(),
                        "overlay": overlay or ""})
    return {"version": version, "sections": sections, "overlays": overlays, "targets": targets}


def collect_changelog(limit: int = 8) -> list[dict]:
    f = ROOT / "CHANGELOG.md"
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        title, body = m.group(1), m.group(2)
        items = re.findall(r"^- (.+)", body, re.M)
        entries.append({"title": title, "items": items})
    return entries[:limit]


def badge(ok: bool) -> str:
    return ('<span class="badge ok">同步</span>' if ok
            else '<span class="badge drift">漂移</span>')


def render() -> str:
    skills = collect_skills(ROOT / "skills", own=True)
    vendor = collect_skills(ROOT / "vendor", own=False)
    notes = collect_notes()
    g = collect_global()
    log = collect_changelog()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_rules = sum(s["rules"] for s in skills)
    total_items = sum(n["total"] for n in notes)
    total_distilled = sum(n["distilled"] for n in notes)

    skill_cards = "".join(f"""
      <div class="card">
        <div class="card-head"><span class="name">{esc(s['name'])}</span>
          <span class="ver">v{esc(s['version'])}</span></div>
        <div class="meta">{s['rules']} 个章节 · 来源：{esc('、'.join(s['sources'])) or '—'}</div>
        <p>{esc(s['desc'])}</p>
      </div>""" for s in skills)

    vendor_rows = "".join(
        f"<tr><td>{esc(s['name'])}</td><td>v{esc(s['version'])}</td><td>引入 · 原样不改</td></tr>"
        for s in vendor)

    note_rows = "".join(f"""
      <tr><td class="mono">{esc(n['file'])}</td>
        <td><div class="bar"><div class="fill" style="width:{(n['distilled']/n['total']*100 if n['total'] else 0):.0f}%"></div></div>
            {n['distilled']}/{n['total']} 条已加工</td>
        <td>{esc('、'.join(n['targets'])) or '<span class="dim">待提炼</span>'}</td></tr>"""
        for n in notes)

    target_rows = "".join(f"""
      <tr><td>{esc(t['label'])}{' <span class="tag">+overlay</span>' if t['overlay'] else ''}</td>
          <td>{badge(t['sync'])}</td></tr>""" for t in g["targets"])

    matrix = collect_matrix(skills)

    def build_cell(b: dict) -> str:
        if b["state"] == "ok":
            return f'<span class="badge ok">已构建</span> <span class="dim">{esc(b["text"])}</span>'
        if b["state"] == "drift":
            return f'<span class="badge drift">待重建</span> <span class="dim">{esc(b["text"])}</span>'
        return f'<span class="badge none">未构建</span>'

    matrix_rows = "".join(
        "<tr><td class=\"mono\">{name}</td><td>v{ver}</td><td>{build}</td><td>{pubs}</td></tr>".format(
            name=esc(m["name"]), ver=esc(m["version"]), build=build_cell(m["build"]),
            pubs="<br>".join(
                f'{esc(p["pool"])} {badge(p["sync"])}' for p in m["pubs"]
            ) or '<span class="dim">无目录发布（仅 .skill 包）</span>')
        for m in matrix)

    log_html = "".join(f"""
      <div class="log-entry"><div class="log-title">{esc(e['title'])}</div>
        <ul>{''.join(f'<li>{esc(i)}</li>' for i in e['items'])}</ul></div>""" for e in log)

    pct = f"{total_distilled/total_items*100:.0f}%" if total_items else "—"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarnessOS 看板</title>
<style>
  :root {{ --ink:#1a1d21; --dim:#6b7280; --line:#e5e7eb; --accent:#b3541e; --ok:#1a7f4b; --drift:#b91c1c; --bg:#fafaf7; }}
  * {{ margin:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); line-height:1.6; }}
  .wrap {{ max-width:960px; margin:0 auto; padding:48px 24px 80px; }}
  header h1 {{ font-size:28px; letter-spacing:.02em; }}
  header .sub {{ color:var(--dim); font-size:13px; margin-top:4px; }}
  .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:28px 0 40px; }}
  .stat {{ border:1px solid var(--line); border-radius:10px; padding:16px; background:#fff; }}
  .stat .num {{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .stat .lbl {{ font-size:12px; color:var(--dim); margin-top:2px; }}
  h2 {{ font-size:16px; margin:36px 0 14px; padding-left:10px; border-left:3px solid var(--accent); }}
  .card {{ border:1px solid var(--line); border-radius:10px; padding:16px 18px; background:#fff; margin-bottom:10px; }}
  .card-head {{ display:flex; justify-content:space-between; align-items:baseline; }}
  .name {{ font-weight:700; font-family:ui-monospace,Consolas,monospace; }}
  .ver {{ color:var(--accent); font-size:13px; font-weight:600; }}
  .meta {{ font-size:12px; color:var(--dim); margin:2px 0 8px; }}
  .card p {{ font-size:13px; color:#3f454d; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--line); border-radius:10px; overflow:hidden; font-size:13px; }}
  td,th {{ padding:10px 14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; }}
  tr:last-child td {{ border-bottom:none; }}
  .mono {{ font-family:ui-monospace,Consolas,monospace; font-size:12px; }}
  .dim {{ color:var(--dim); }}
  .bar {{ display:inline-block; width:90px; height:6px; background:#eceae4; border-radius:3px; margin-right:8px; vertical-align:middle; overflow:hidden; }}
  .fill {{ height:100%; background:var(--accent); }}
  .badge {{ font-size:11px; padding:2px 8px; border-radius:99px; font-weight:600; }}
  .badge.ok {{ background:#e4f4ec; color:var(--ok); }}
  .badge.drift {{ background:#fbe7e7; color:var(--drift); }}
  .badge.none {{ background:#f0eee9; color:var(--dim); }}
  .tag {{ font-size:11px; color:var(--dim); border:1px solid var(--line); border-radius:99px; padding:1px 7px; }}
  .log-entry {{ border-left:2px solid var(--line); padding:2px 0 14px 16px; position:relative; }}
  .log-entry::before {{ content:""; position:absolute; left:-5px; top:8px; width:8px; height:8px; border-radius:50%; background:var(--accent); }}
  .log-title {{ font-weight:600; font-size:14px; }}
  .log-entry ul {{ margin:4px 0 0 18px; font-size:13px; color:#3f454d; }}
  footer {{ margin-top:48px; font-size:12px; color:var(--dim); }}
  code {{ background:#f0eee9; padding:1px 5px; border-radius:4px; font-size:12px; }}
</style></head><body><div class="wrap">
<header>
  <h1>HarnessOS 看板</h1>
  <div class="sub">个人 AI 编程 Harness 规则资产总览 · 由 <code>scripts/dashboard.py</code> 扫描仓库自动生成 · {now}</div>
</header>
<div class="stats">
  <div class="stat"><div class="num">{len(skills)}</div><div class="lbl">自有 Skill</div></div>
  <div class="stat"><div class="num">{total_rules}</div><div class="lbl">规则章节</div></div>
  <div class="stat"><div class="num">v{esc(g['version'])}</div><div class="lbl">全局规则版本</div></div>
  <div class="stat"><div class="num">{pct}</div><div class="lbl">原料加工率</div></div>
</div>

<h2>生产线 · 经验 → Skill</h2>
{skill_cards or '<p class="dim">暂无</p>'}

<h2>构建 × 发布矩阵（每个 skill 构建了什么、发到了哪些 Agent）</h2>
<table><tr><th>Skill</th><th>版本</th><th>.skill 构建（dist/）</th><th>目录发布（同步状态）</th></tr>{matrix_rows}</table>
<p class="dim" style="font-size:12px;margin-top:6px">目录发布以仓库源为准：~/.agents/skills 为共享池（Codex / OpenCode 等读取），~/.claude/skills 为 Claude 池。.skill 包需手动导入 Kimi Code / Codex / Claude Code。Kimi Code 另有托管技能体系，不在此矩阵。</p>

<h2>全局规则 · 经验 → 用户规则</h2>
<div class="card">
  <div class="card-head"><span class="name">global/AGENTS.md</span><span class="ver">v{esc(g['version'])}</span></div>
  <div class="meta">{g['sections']} 个章节 · 发布到 4 个 Agent 读取位置 · Kimi Code 无全局注入机制，不发布</div>
  <table><tr><th>发布目标</th><th>状态</th></tr>{target_rows}</table>
</div>

<h2>原料区 · 笔记加工进度</h2>
<table><tr><th>笔记</th><th>加工进度</th><th>去向</th></tr>{note_rows or '<tr><td class="dim">暂无笔记</td></tr>'}</table>

<h2>引入区 · vendor（原样不改）</h2>
<table><tr><th>Skill</th><th>版本</th><th>来源</th></tr>{vendor_rows}</table>

<h2>加工历史</h2>
{log_html}

<footer>本文件为生成产物，不手改。数据变化后运行 <code>python scripts/dashboard.py</code> 重新生成。
漂移状态的修复：运行 <code>python scripts/publish_global.py</code>。</footer>
</div></body></html>"""


def main() -> None:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[完成] {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
