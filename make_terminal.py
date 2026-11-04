"""Erzeugt assets/terminal.svg: animiertes Terminal fuer das Profil-README.

Jede Zeile bekommt eine feste Breite (textLength), damit das Tippen
unabhaengig von der Schrift des Betrachters sauber aussieht.
"""
from pathlib import Path
from html import escape

CW = 9.0          # Breite pro Zeichen in px
FS = 15           # Schriftgroesse
X0 = 24           # linker Rand
Y0 = 76           # erste Zeile
LH = 25           # Zeilenabstand
W, H = 820, 0     # H wird berechnet

BG = "#0d1117"
CYAN = "#00d8ff"
GREEN = "#3fb950"
DIM = "#8b949e"
FG = "#e6edf3"
GOLD = "#f0b429"

PROMPT = "zedas@homelab:~$ "

# (art, inhalt) – "cmd": getippter Befehl, "out": Ausgabe [(text, farbe), ...]
script = [
    ("cmd", "whoami"),
    ("out", [("Zedas030", CYAN), (" · Hobby-Entwickler · Smart-Home-Bastler · Homelab-Nerd", FG)]),
    ("cmd", "cat projekte.txt"),
    ("out", [("▸ ", CYAN), ("JARVIS  ", CYAN), ("Sprachassistent mit Gedächtnis, steuert die Wohnung", FG)]),
    ("out", [("▸ ", CYAN), ("ORBIT   ", CYAN), ("Heimnetz-Monitoring & Sicherheitszentrale", FG)]),
    ("out", [("▸ ", CYAN), ("SOLARIS ", CYAN), ("Energie-Dashboard für PV + Akku", FG)]),
    ("out", [("▸ ", CYAN), ("CS2     ", CYAN), ("KI-Agent baut Städte in Cities: Skylines II", FG)]),
    ("cmd", "uptime"),
    ("out", [("läuft seit dem ersten Raspberry Pi · ", DIM), ("Kaffee: ∞", GOLD)]),
    ("cmd", "sudo make coffee"),
    ("out", [("[sudo] ", DIM), ("Zugriff gewährt. Jarvis kocht schon.", GREEN)]),
]


def width(s: str) -> float:
    return len(s) * CW


parts = []
t = 0.4
y = Y0
for kind, content in script:
    if kind == "cmd":
        n = len(content)
        dur = max(0.35, n * 0.07)
        px = width(PROMPT)
        parts.append(
            f'<g class="l" style="animation-delay:{t:.2f}s">'
            f'<text x="{X0}" y="{y}" textLength="{px:.0f}" fill="{GREEN}">{escape(PROMPT)}</text>'
            f'<text x="{X0 + px:.0f}" y="{y}" textLength="{n * CW:.0f}" fill="{FG}">{escape(content)}</text>'
            f'<rect class="c" x="{X0 + px - 1:.0f}" y="{y - FS}" width="{n * CW + 12:.0f}" height="{LH}" fill="{BG}" '
            f'style="--w:{n * CW + 12:.0f}px;animation:type {dur:.2f}s steps({n}) {t + 0.25:.2f}s forwards"/>'
            f'</g>'
        )
        t += 0.25 + dur + 0.3
    else:
        spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in content)
        total = sum(width(s) for s, _ in content)
        parts.append(
            f'<text class="l" x="{X0}" y="{y}" textLength="{total:.0f}" lengthAdjust="spacing" '
            f'style="animation-delay:{t:.2f}s">{spans}</text>'
        )
        t += 0.22
    y += LH

# letzter Prompt mit blinkendem Cursor
px = width(PROMPT)
parts.append(
    f'<g class="l" style="animation-delay:{t + 0.2:.2f}s">'
    f'<text x="{X0}" y="{y}" textLength="{px:.0f}" fill="{GREEN}">{escape(PROMPT)}</text>'
    f'<rect class="cur" x="{X0 + px + 2:.0f}" y="{y - FS + 2}" width="9" height="17" fill="{CYAN}"/>'
    f'</g>'
)
H = y + 30

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal: whoami, Projekte, uptime">
<style>
text{{font-family:'JetBrains Mono','Cascadia Code','Fira Code',Consolas,'DejaVu Sans Mono',monospace;font-size:{FS}px;white-space:pre}}
.l{{opacity:0;animation:show .01s forwards}}
@keyframes show{{to{{opacity:1}}}}
@keyframes type{{to{{transform:translateX(var(--w))}}}}
.cur{{animation:blink 1s step-end infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>
<defs><clipPath id="win"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/></clipPath>
<linearGradient id="glow" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".9"/><stop offset="1" stop-color="#7c3aed" stop-opacity=".9"/></linearGradient></defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="{BG}" stroke="url(#glow)" stroke-width="2"/>
<g clip-path="url(#win)">
<rect x="1" y="1" width="{W - 2}" height="36" fill="#161b22"/>
<circle cx="24" cy="19" r="6" fill="#ff5f56"/><circle cx="44" cy="19" r="6" fill="#ffbd2e"/><circle cx="64" cy="19" r="6" fill="#27c93f"/>
<text x="{W / 2}" y="24" text-anchor="middle" fill="{DIM}" style="font-size:13px">zedas@homelab: ~</text>
{chr(10).join(parts)}
</g>
</svg>
'''

out = Path(__file__).parent / "assets" / "terminal.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg, encoding="utf-8")
print(out, H, f"{t:.1f}s")
