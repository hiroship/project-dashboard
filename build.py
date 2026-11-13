#!/usr/bin/env python3
"""Regenerate the static project dashboard from PROJECTS.md and (optionally) publish.

Usage:
  python3 build.py            # regenerate index.html only
  python3 build.py --publish  # regenerate + commit + push to GitHub Pages repo
"""
import html, re, subprocess, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE.parent / "PROJECTS.md"

# Rows whose next step belongs to the user get the attention stamp.
ATTENTION_HINTS = ("要対応", "QC待ち", "入力待ち", "ユーザー操作", "承認待ち")

def parse_ledger(text):
    updated = ""
    m = re.search(r"最終更新:\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        updated = m.group(1)
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4 or cells[0] in ("プロジェクト",) or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return updated, rows

def is_attention(row):
    name, status, nxt, block = row
    return any(h in (status + block + nxt) for h in ATTENTION_HINTS)

def card(row, attention):
    name, status, nxt, block = [html.escape(c) for c in row]
    stamp = '<span class="stamp">要対応</span>' if attention else ""
    cls = "card attention" if attention else "card"
    return f'''<article class="{cls}">
  <div class="card-head"><h3>{name}</h3>{stamp}</div>
  <p class="status"><span class="label">状態</span>{status}</p>
  <p><span class="label">次の一手</span>{nxt}</p>
  <p><span class="label">期限・ブロック</span>{block}</p>
</article>'''

def render(updated, rows):
    att = [r for r in rows if is_attention(r)]
    rest = [r for r in rows if not is_attention(r)]
    att_html = "\n".join(card(r, True) for r in att)
    all_html = "\n".join(card(r, is_attention(r)) for r in rows)
    gen = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>プロジェクト管理</title>
<style>
  :root {{ --ink:#1f2937; --sub:#6b7280; --line:#e5e7eb; --accent:#b91c1c; --bg:#f7f5f0; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Noto Sans JP",sans-serif;
         background:var(--bg); color:var(--ink); -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:24px 16px 48px; }}
  header h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:.02em; }}
  header p {{ margin:0; color:var(--sub); font-size:13px; }}
  h2 {{ font-size:15px; margin:28px 0 12px; padding-bottom:6px; border-bottom:2px solid var(--ink); letter-spacing:.05em; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
  .card.attention {{ border-color:var(--accent); border-width:1.5px; }}
  .card-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }}
  .card h3 {{ font-size:15px; margin:0 0 8px; line-height:1.4; }}
  .stamp {{ flex:none; color:var(--accent); border:1.5px solid var(--accent); border-radius:4px;
           font-size:11px; font-weight:700; padding:1px 6px; transform:rotate(3deg); }}
  .card p {{ margin:4px 0; font-size:13px; line-height:1.55; }}
  .label {{ display:inline-block; min-width:76px; color:var(--sub); font-size:11px; font-weight:700; }}
  footer {{ margin-top:32px; color:var(--sub); font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>プロジェクト管理</h1>
  <p>台帳の最終更新: {html.escape(updated)} ／ このページの生成: {gen}（読み取り専用スナップショット）</p>
</header>
<h2>あなたの手が必要なもの（{len(att)}件）</h2>
<div class="grid">
{att_html}
</div>
<h2>全プロジェクト（{len(rows)}件）</h2>
<div class="grid">
{all_html}
</div>
<footer>編集は Muse のダッシュボード（Space「プロジェクト管理」）で。台帳: workspace/projects/PROJECTS.md</footer>
</div>
</body>
</html>'''

def main():
    text = LEDGER.read_text(encoding="utf-8")
    updated, rows = parse_ledger(text)
    out = HERE / "index.html"
    out.write_text(render(updated, rows), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} projects)")
    if "--publish" in sys.argv:
        def run(*args):
            subprocess.run(args, cwd=HERE, check=True)
        run("git", "add", "index.html", "build.py")
        r = subprocess.run(["git", "status", "--porcelain"], cwd=HERE,
                           capture_output=True, text=True)
        if r.stdout.strip():
            run("git", "commit", "-m", f"Update dashboard snapshot {datetime.now():%Y-%m-%d %H:%M}")
            run("git", "push", "origin", "main")
            print("pushed")
        else:
            print("no changes")

if __name__ == "__main__":
    main()
