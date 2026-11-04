"""Erzeugt dist/stats.svg und dist/langs.svg aus der GitHub-API.

Laeuft in der Action mit GITHUB_TOKEN, ohne fremden Stats-Dienst.
Aufruf: python3 scripts/gen_stats.py <user> <ausgabeordner>
"""
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

USER, OUT = sys.argv[1], Path(sys.argv[2])
SKIP = {"achievements-playground", USER.lower()}
TOKEN = os.environ["GITHUB_TOKEN"]

BG, CARD, CYAN, FG, DIM = "#0d1117", "#161b22", "#00d8ff", "#e6edf3", "#8b949e"
COLORS = {"Python": "#3572A5", "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399",
          "Shell": "#89e051", "PowerShell": "#012456", "C#": "#178600", "Batchfile": "#C1F12E",
          "VBScript": "#15dcdc", "TypeScript": "#3178c6"}
FONT = "font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"

Q = """query($login:String!){ user(login:$login){
  name createdAt
  contributionsCollection{ totalCommitContributions totalPullRequestContributions
    totalIssueContributions contributionCalendar{ totalContributions } }
  pullRequests(states:MERGED){ totalCount }
  repositories(ownerAffiliations:OWNER, isFork:false, first:100, privacy:PUBLIC){
    totalCount nodes{ name stargazerCount
      languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } } } } }"""


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


u = gql(Q, login=USER)["user"]
cc = u["contributionsCollection"]
repos = [r for r in u["repositories"]["nodes"] if r["name"].lower() not in SKIP]
stars = sum(r["stargazerCount"] for r in repos)
langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]

rows = [
    ("⭐", "Sterne", stars),
    ("📦", "Öffentliche Projekte", len(repos)),
    ("🔨", "Commits (12 Monate)", cc["totalCommitContributions"]),
    ("🔀", "Gemergte Pull Requests", u["pullRequests"]["totalCount"]),
    ("📅", "Beiträge (12 Monate)", cc["contributionCalendar"]["totalContributions"]),
]

# --- stats.svg -----------------------------------------------------------
W, H = 420, 200
lines = []
for i, (ico, label, val) in enumerate(rows):
    y = 72 + i * 26
    lines.append(f'<text x="28" y="{y}" fill="{FG}" style="{FONT};font-size:14px">{ico}  {escape(label)}</text>'
                 f'<text x="{W - 28}" y="{y}" text-anchor="end" fill="{CYAN}" style="{FONT};font-size:15px;font-weight:700">{f"{val:,}".replace(",", ".")}</text>')
stats = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub-Statistik">
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#30363d"/>
<text x="28" y="38" fill="{CYAN}" style="{FONT};font-size:18px;font-weight:600">Statistik von {escape(USER)}</text>
{"".join(lines)}
</svg>'''

# --- langs.svg -----------------------------------------------------------
top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
total = sum(v for _, v in top) or 1
bar, x = [], 28.0
for name, v in top:
    w = (W - 56) * v / total
    bar.append(f'<rect x="{x:.1f}" y="56" width="{w:.1f}" height="10" fill="{COLORS.get(name, DIM)}"/>')
    x += w
legend = []
for i, (name, v) in enumerate(top):
    cx = 28 + (i % 2) * 190
    cy = 98 + (i // 2) * 28
    legend.append(f'<circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{COLORS.get(name, DIM)}"/>'
                  f'<text x="{cx + 16}" y="{cy}" fill="{FG}" style="{FONT};font-size:13px">{escape(name)} '
                  f'<tspan fill="{DIM}">{100 * v / total:.1f} %</tspan></text>')
langs_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Meistgenutzte Sprachen">
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#30363d"/>
<text x="28" y="38" fill="{CYAN}" style="{FONT};font-size:18px;font-weight:600">Meistgenutzte Sprachen</text>
<defs><clipPath id="b"><rect x="28" y="56" width="{W - 56}" height="10" rx="5"/></clipPath></defs>
<g clip-path="url(#b)">{"".join(bar)}</g>
{"".join(legend)}
</svg>'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "stats.svg").write_text(stats, encoding="utf-8")
(OUT / "langs.svg").write_text(langs_svg, encoding="utf-8")
print(rows, top)
