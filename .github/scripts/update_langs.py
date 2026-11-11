import os, json, urllib.request, math

USERNAME = os.environ.get("USERNAME", "hollali")
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "langs-script"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

# fetch repos (public, non-fork), paginate
repos = []
page = 1
while True:
    batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
    if not batch:
        break
    repos.extend([r for r in batch if not r.get("fork")])
    if len(batch) < 100:
        break
    page += 1
    if page > 10:
        break

# aggregate languages
totals = {}
for r in repos:
    try:
        langs = api(f"/repos/{USERNAME}/{r['name']}/languages")
    except Exception:
        continue
    for lang, size in langs.items():
        totals[lang] = totals.get(lang, 0) + size

# sort
items = sorted(totals.items(), key=lambda x: -x[1])
total = sum(totals.values()) or 1
# keep all with >=0.1%? keep all
rows_data = [(name, size / total * 100) for name, size in items]

# build 3-column table
cols = 3
# chunk into rows of 3
lines = []
lines.append("| | | |")
lines.append("|---|---|---|")
i = 0
n = len(rows_data)
while i < n:
    cells = []
    for c in range(cols):
        idx = i + c
        if idx < n:
            name, pct = rows_data[idx]
            cells.append(f"**{name}** — {pct:.1f}%")
        else:
            cells.append("")
    lines.append("| " + " | ".join(cells) + " |")
    i += cols

table = "\n".join(lines)

# read README
readme_path = os.environ.get("README_PATH", "README.md")
with open(readme_path) as f:
    content = f.read()

start = "<!--LANGS:START-->"
end = "<!--LANGS:END-->"
block = f"{start}\n### Most Used Languages\n\n{table}\n{end}"
if start in content and end in content:
    import re
    content = re.sub(re.escape(start) + r".*?" + re.escape(end), block, content, count=1, flags=re.S)
else:
    # append before a marker? just print
    pass

with open(readme_path, "w") as f:
    f.write(content)

print(f"Updated {len(rows_data)} languages in {math.ceil(n/cols)} rows")
