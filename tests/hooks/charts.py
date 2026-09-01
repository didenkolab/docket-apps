"""Draw the results as an SVG the vault keeps.

A picture in a repository rather than a canvas in a browser: it is committed,
it is diffed, it opens in Obsidian, and it is still there when the server is
not. Nothing here is a chart library — a bar is a rectangle, and the whole of
it is arithmetic somebody can check.
"""
import json, subprocess, sys, os

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
out = sys.argv[1] if len(sys.argv) > 1 else "attachments/test-results.svg"

tasks = json.loads(subprocess.run([docket, "export", "--format", "json"],
                                  capture_output=True, text=True, cwd=root).stdout or "[]")

runs, executions = [], {}
for t in tasks:
    fields = t.get("fields") or {}
    if t.get("type") == "test_execution":
        executions[t["key"]] = {
            "key": t["key"], "title": t.get("title", ""),
            "environment": fields.get("environment", ""),
            "when": t.get("created", ""), "passed": 0, "failed": 0, "other": 0,
        }
for t in tasks:
    if t.get("type") != "test_run":
        continue
    into = executions.get(t.get("parent", ""))
    if not into:
        continue
    result = (t.get("fields") or {}).get("result", "todo")
    into["passed" if result == "passed" else "failed" if result == "failed" else "other"] += 1

shown = [e for e in executions.values() if e["passed"] + e["failed"] + e["other"] > 0]
shown.sort(key=lambda e: e["when"])
shown = shown[-12:]

if not shown:
    print("no executions with runs yet, so no chart")
    sys.exit(0)

# Geometry. Everything is a number here on purpose: a chart nobody can recompute
# is a chart nobody can disbelieve.
width, height = 720, 260
pad_left, pad_bottom, pad_top = 44, 56, 16
plot_h = height - pad_bottom - pad_top
plot_w = width - pad_left - 16
tallest = max(e["passed"] + e["failed"] + e["other"] for e in shown)
step = plot_w / len(shown)
bar = min(46, step * 0.62)

def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
    f'width="{width}" height="{height}" font-family="ui-sans-serif, system-ui, sans-serif">',
    f'<rect width="{width}" height="{height}" fill="none"/>',
]

# Two gridlines and their numbers: none is unreadable, five is a cage.
for share in (0.5, 1.0):
    y = pad_top + plot_h - plot_h * share
    value = round(tallest * share)
    parts.append(f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - 16}" y2="{y:.1f}" '
                 f'stroke="#d8d8d8" stroke-width="1"/>')
    parts.append(f'<text x="{pad_left - 8}" y="{y + 4:.1f}" font-size="11" fill="#777" '
                 f'text-anchor="end">{value}</text>')

for i, e in enumerate(shown):
    total = e["passed"] + e["failed"] + e["other"]
    x = pad_left + step * i + (step - bar) / 2
    y = pad_top + plot_h
    for count, colour in ((e["passed"], "#2f9e5e"), (e["failed"], "#d1453b"), (e["other"], "#9a9a9a")):
        if not count:
            continue
        h = plot_h * count / tallest
        y -= h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h:.1f}" '
                     f'fill="{colour}"><title>{esc(e["key"])}: {count}</title></rect>')
    label = e["key"]
    parts.append(f'<text x="{x + bar / 2:.1f}" y="{pad_top + plot_h + 16}" font-size="11" '
                 f'fill="#555" text-anchor="middle">{esc(label)}</text>')
    if e["environment"]:
        parts.append(f'<text x="{x + bar / 2:.1f}" y="{pad_top + plot_h + 30}" font-size="10" '
                     f'fill="#999" text-anchor="middle">{esc(e["environment"][:12])}</text>')
    parts.append(f'<text x="{x + bar / 2:.1f}" y="{pad_top + plot_h - plot_h * total / tallest - 5:.1f}" '
                 f'font-size="10" fill="#555" text-anchor="middle">{total}</text>')

legend = [("passed", "#2f9e5e"), ("failed", "#d1453b"), ("other", "#9a9a9a")]
for i, (name, colour) in enumerate(legend):
    lx = pad_left + i * 92
    parts.append(f'<rect x="{lx}" y="{height - 16}" width="10" height="10" fill="{colour}"/>')
    parts.append(f'<text x="{lx + 15}" y="{height - 7}" font-size="11" fill="#555">{name}</text>')

parts.append("</svg>")

at = os.path.join(root, out)
os.makedirs(os.path.dirname(at), exist_ok=True)
with open(at, "w", encoding="utf-8") as f:
    f.write("\n".join(parts) + "\n")
print(f"drew {out}: {len(shown)} executions")
