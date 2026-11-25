#!/usr/bin/env python3
"""Генерирует dist/releases-{dark,light}.svg — последние релизы репозиториев пользователя."""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from html import escape

USER = os.environ.get("GH_USER", "distillium")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
LIMIT = int(os.environ.get("LIMIT", "5"))
OUT = os.environ.get("OUT_DIR", "dist")

def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "releases-card",
                 **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

def collect():
    if os.environ.get("MOCK"):
        return json.load(open(os.environ["MOCK"]))
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner") or []
    items = []
    for r in repos:
        if r.get("fork") or r.get("archived") or r["name"] == USER: continue
        rel = api(f"/repos/{USER}/{r['name']}/releases/latest")
        if not rel or not rel.get("published_at"): continue
        items.append({"repo": r["name"], "tag": rel["tag_name"], "url": rel["html_url"],
                      "date": rel["published_at"]})
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:LIMIT]

def ago(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = (datetime.now(timezone.utc) - d).total_seconds()
    days = int(s // 86400)
    if days < 1:
        h = int(s // 3600); return "just now" if h < 1 else f"{h} hour{'s'*(h!=1)} ago"
    if days < 30: return f"{days} day{'s'*(days!=1)} ago"
    m = days // 30
    if m < 12: return f"{m} month{'s'*(m!=1)} ago"
    y = days // 365; return f"{y} year{'s'*(y!=1)} ago"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

def render(items, dark):
    W, top, row = 880, 62, 52
    H = top + row * max(len(items), 1) + 14
    gold = "#c9a66b"
    acc = "#e2c48e" if dark else "#8c6630"
    tc = "#e6edf3" if dark else "#1f2328"
    dc = "#9198a1" if dark else "#59636e"
    sep = "#c9a66b"
    rows = []
    for i, it in enumerate(items):
        y = top + i * row
        tag = escape(it["tag"]); tw = 9.2 * len(it["tag"]) + 22
        rows.append(f'''
  <g transform="translate(0 {y})">
    {'' if i == 0 else f'<line x1="28" x2="{W-28}" y1="0" y2="0" stroke="{sep}" stroke-opacity=".14"/>'}
    <g transform="translate(30 15)" fill="none" stroke="{acc}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 3.5v6.2l9.3 9.3a1.6 1.6 0 0 0 2.3 0l5.4-5.4a1.6 1.6 0 0 0 0-2.3L9.7 2H3.5A1.5 1.5 0 0 0 2 3.5z"/><circle cx="6.6" cy="6.6" r="1.4"/>
    </g>
    <text x="64" y="32" font-family="{SANS}" font-size="16" font-weight="600" fill="{tc}">{escape(it["repo"])}</text>
    <rect x="{W-28-150-tw}" y="13" width="{tw}" height="26" rx="13" fill="{gold}" fill-opacity="{.12 if dark else .14}" stroke="{gold}" stroke-opacity=".35"/>
    <text x="{W-28-150-tw/2}" y="31" text-anchor="middle" font-family="{MONO}" font-size="13.5" font-weight="600" fill="{acc}">{tag}</text>
    <text x="{W-28}" y="31" text-anchor="end" font-family="{SANS}" font-size="14" fill="{dc}">{ago(it["date"])}</text>
  </g>''')
    if not items:
        rows.append(f'<text x="30" y="{top+30}" font-family="{SANS}" font-size="14" fill="{dc}">No releases yet</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{gold}" fill-opacity="{.05 if dark else .07}" stroke="{gold}" stroke-opacity="{.28 if dark else .4}"/>
  <text x="30" y="38" font-family="{MONO}" font-size="12.5" font-weight="600" letter-spacing="2.2" fill="{acc}">LATEST RELEASES</text>
  <circle cx="{W-34}" cy="34" r="4" fill="{acc}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>
  {''.join(rows)}
</svg>'''

def main():
    items = collect()
    os.makedirs(OUT, exist_ok=True)
    for t in ("dark", "light"):
        open(f"{OUT}/releases-{t}.svg", "w").write(render(items, t == "dark"))
    print(f"releases: {len(items)}", *[f"{i['repo']} {i['tag']}" for i in items], sep="\n  ")

if __name__ == "__main__":
    main()
