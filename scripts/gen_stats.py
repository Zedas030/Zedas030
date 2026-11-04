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
    totalIssueContributions totalPullRequestReviewContributions contributionCalendar{ totalContributions } }
  pullRequests(states:MERGED){ totalCount }
  allPrs: pullRequests{ totalCount }
  issues{ totalCount }
  followers{ totalCount }
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
    ("⭐", "Stars earned", stars),
    ("📦", "Public projects", len(repos)),
    ("🔨", "Commits (last year)", cc["totalCommitContributions"]),
    ("🔀", "Merged pull requests", u["pullRequests"]["totalCount"]),
    ("📅", "Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
]

# --- Rang wie bei github-readme-stats (calculateRank) ----------------------
def exp_cdf(x):
    return 1 - 2 ** -x


def lognorm_cdf(x):
    return x / (1 + x)


parts = [
    (2, exp_cdf(cc["totalCommitContributions"] / 250)),
    (3, exp_cdf(u["allPrs"]["totalCount"] / 50)),
    (1, exp_cdf(u["issues"]["totalCount"] / 25)),
    (1, exp_cdf(cc["totalPullRequestReviewContributions"] / 2)),
    (4, lognorm_cdf(stars / 50)),
    (1, lognorm_cdf(u["followers"]["totalCount"] / 10)),
]
percentile = (1 - sum(w * v for w, v in parts) / sum(w for w, _ in parts)) * 100
LEVELS = [(1, "S"), (12.5, "A+"), (25, "A"), (37.5, "A-"), (50, "B+"), (62.5, "B"), (75, "B-"), (87.5, "C+"), (100, "C")]
level = next(lv for t, lv in LEVELS if percentile <= t)

# --- stats.svg -----------------------------------------------------------
W, H = 420, 200
RX, RY, RR = 352, 118, 40
circ = 2 * 3.14159 * RR
done = circ * (1 - percentile / 100)
ring = (f'<circle cx="{RX}" cy="{RY}" r="{RR}" fill="none" stroke="#30363d" stroke-width="6"/>'
        f'<circle cx="{RX}" cy="{RY}" r="{RR}" fill="none" stroke="{CYAN}" stroke-width="6" stroke-linecap="round" '
        f'stroke-dasharray="{done:.1f} {circ:.1f}" transform="rotate(-90 {RX} {RY})">'
        f'<animate attributeName="stroke-dasharray" from="0 {circ:.1f}" to="{done:.1f} {circ:.1f}" dur="1.2s" fill="freeze"/></circle>'
        f'<text x="{RX}" y="{RY + 9}" text-anchor="middle" fill="{FG}" style="{FONT};font-size:26px;font-weight:700">{level}</text>')
lines = []
for i, (ico, label, val) in enumerate(rows):
    y = 72 + i * 26
    lines.append(f'<text x="28" y="{y}" fill="{FG}" style="{FONT};font-size:14px">{ico}  {escape(label)}</text>'
                 f'<text x="270" y="{y}" text-anchor="end" fill="{CYAN}" style="{FONT};font-size:15px;font-weight:700">{f"{val:,}"}</text>')
stats = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#30363d"/>
<text x="28" y="38" fill="{CYAN}" style="{FONT};font-size:18px;font-weight:600">{escape(USER)}'s GitHub stats</text>
{"".join(lines)}
{ring}
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
                  f'<tspan fill="{DIM}">{100 * v / total:.1f}%</tspan></text>')
langs_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Most used languages">
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#30363d"/>
<text x="28" y="38" fill="{CYAN}" style="{FONT};font-size:18px;font-weight:600">Most used languages</text>
<defs><clipPath id="b"><rect x="28" y="56" width="{W - 56}" height="10" rx="5"/></clipPath></defs>
<g clip-path="url(#b)">{"".join(bar)}</g>
{"".join(legend)}
</svg>'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "stats.svg").write_text(stats, encoding="utf-8")
(OUT / "langs.svg").write_text(langs_svg, encoding="utf-8")
print(rows, top, level, round(percentile, 1))
