"""Turn a Cucumber project's scenarios into tests in the vault.

One task per scenario. The case id tag is the identity — `@ACME-ADM-002` — and
nothing else is: a scenario's name is written for people and gets improved, and
a test whose identity is its name loses its history the first time somebody
rewords it.

Read by import-features.sh, which passes the features directory.
"""
import os, re, subprocess, sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
where = sys.argv[1]
rest = sys.argv[2:]
wanted_tag = next((a for a in rest if a.startswith("@")), "")
project = next((a.split("=", 1)[1] for a in rest if a.startswith("--project=")), "")
dry = "--dry-run" in rest

CASE_ID = re.compile(r"^@(SP|ACME)-[A-Z]+-\d+$")

def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()

# What is already here, by case id, so running this twice does not double.
import json
known = {}
for t in json.loads(run("export", "--format", "json")):
    ident = (t.get("fields") or {}).get("automation_id", "").strip()
    if ident:
        known[ident] = t["key"]

def scenarios(path):
    """Every scenario in one .feature: its tags, name, and the steps under it."""
    feature, tags, out = "", [], []
    current = None
    for line in open(path, encoding="utf-8").read().splitlines():
        bare = line.strip()
        if bare.startswith("Feature:"):
            feature = bare[len("Feature:"):].strip()
            tags = []
            continue
        if bare.startswith("@"):
            tags = bare.split()
            continue
        if re.match(r"^(Scenario|Scenario Outline|Example):", bare):
            if current:
                out.append(current)
            current = {"feature": feature, "tags": tags,
                       "name": bare.split(":", 1)[1].strip(), "steps": []}
            tags = []
            continue
        if current is not None and bare and not bare.startswith("#"):
            current["steps"].append(bare)
    if current:
        out.append(current)
    return out

made = skipped = without = 0
for base, _, files in os.walk(where):
    for name in sorted(files):
        if not name.endswith(".feature"):
            continue
        for s in scenarios(os.path.join(base, name)):
            ident = next((t[1:] for t in s["tags"] if CASE_ID.match(t)), "")
            if not ident:
                without += 1
                continue
            if wanted_tag and wanted_tag not in s["tags"]:
                continue
            if ident in known:
                skipped += 1
                continue
            if dry:
                made += 1
                continue

            # `docket new` prints the key and the path it wrote, which is why
            # this does not ask for the path again: an export per scenario is
            # a 3 MB read eight hundred times over.
            made_line = run("new", s["name"][:120], "--type", "test",
                            *(["--project", project] if project else []))
            key, at = made_line.split(None, 1)
            body = ["## Scenario", "", "```gherkin"]
            body += ["  " + step for step in s["steps"]]
            body += ["```", "", "From `" + s["feature"] + "` in the automation repository.",
                     "Identity is the case id, not this title: a title gets improved."]
            with open(os.path.join(root, at.strip()), "a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(body) + "\n")

            # One call, not three: eight hundred scenarios is eight hundred
            # processes per property otherwise.
            args = [key, "automation_id=" + ident, "automated=true"]
            tags = [t[1:] for t in s["tags"] if not CASE_ID.match(t) and t != "@acme"]
            if tags:
                args.append("tags=" + ",".join(tags[:6]))
            run("set", *args, "--quiet")
            made += 1

print(f"{made} tests written, {skipped} already here, {without} scenarios carry no case id")
if dry:
    print("Nothing was written: --dry-run.")
