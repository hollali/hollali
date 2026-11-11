import os, json, urllib.request, math

USERNAME = os.environ.get("USERNAME", "hollali")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT", "top-langs.svg")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "langs-svg"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

repos = []
page = 1
while True:
    if TOKEN:
        batch = api(f"/user/repos?per_page=100&page={page}&affiliation=owner")
    else:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
    if not batch:
        break
    for r in batch:
        if TOKEN and r.get("owner", {}).get("login") != USERNAME:
            continue
        repos.append(r)
    if len(batch) < 100:
        break
    page += 1
    if page > 10:
        break

totals = {}
for r in repos:
    try:
        langs = api(f"/repos/{USERNAME}/{r['name']}/languages")
    except Exception:
        continue
    for lang, size in langs.items():
        totals[lang] = totals.get(lang, 0) + size

items = sorted(totals.items(), key=lambda x: -x[1])
total = sum(totals.values()) or 1
data = [(name, size / total * 100) for name, size in items]

# GitHub linguist colors (subset)
COLORS = {
 "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
 "PHP": "#4F5D95", "Rust": "#dea584", "Java": "#b07219", "Kotlin": "#A97BFF",
 "C++": "#f34b7d", "C": "#555555", "C#": "#178600", "Go": "#00ADD8",
 "Ruby": "#701516", "Swift": "#F05138", "Dart": "#00B4AB", "Shell": "#89e051",
 "HTML": "#e34c26", "CSS": "#563d7c", "SCSS": "#c6538c", "Vue": "#41b883",
 "PowerShell": "#012456", "Blade": "#f7523f", "PLpgSQL": "#336790",
 "CMake": "#DA3434", "Dockerfile": "#384d54", "Hack": "#878787",
 "Objective-C": "#438eff", "Batchfile": "#C1F12E", "Swift": "#F05138",
}
def color(n): return COLORS.get(n, "#858585")

COLS = 3
W = 720
PAD = 25
bar_w = W - 2*PAD
n = len(data)
rows = math.ceil(n / COLS)
H = 60 + 12 + rows*22 + 20

# build svg
parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
parts.append('<style>.t{font:600 16px Segoe UI,Ubuntu,sans-serif;fill:#61dafb}.l{font:400 12px Segoe UI,Ubuntu,sans-serif;fill:#c9d1d9}.p{font:400 11px Segoe UI,Ubuntu,sans-serif;fill:#8b949e}</style>')
parts.append(f'<text x="{PAD}" y="28" class="t">Most Used Languages</text>')

# stacked bar
x = PAD
y = 42
parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="8" rx="4" fill="#21262d"/>')
off = 0
for name, pct in data:
    w = pct/100*bar_w
    parts.append(f'<rect x="{x+off}" y="{y}" width="{w}" height="8" fill="{color(name)}"/>')
    off += w

# legend
start_y = 72
col_w = bar_w // COLS
for i,(name,pct) in enumerate(data):
    r = i // COLS
    c = i % COLS
    lx = PAD + c*col_w
    ly = start_y + r*22
    parts.append(f'<circle cx="{lx+5}" cy="{ly-4}" r="4" fill="{color(name)}"/>')
    parts.append(f'<text x="{lx+14}" y="{ly}" class="l">{name}</text>')
    parts.append(f'<text x="{lx+col_w-4}" y="{ly}" class="p" text-anchor="end">{pct:.1f}%</text>')

parts.append('</svg>')

svg = "\n".join(parts)
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print(f"Wrote {OUT} with {n} languages")
