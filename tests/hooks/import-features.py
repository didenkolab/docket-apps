"""Turn a Cucumber project's scenarios into tests in the vault.

One task per scenario. The case id tag is the identity — `@ACME-ADM-002` — and
nothing else is: a scenario's name is written for people and gets improved, and
a test whose identity is its name loses its history the first time somebody
rewords it.

A scenario nobody tagged still gets one, derived from the feature file and the
scenario's name (see caseid.py). Skipping them was worse: a fifth of a real
suite carries no tag, and a fifth of every run then had nothing to land on.
--write-tags puts the derived id back into the .feature, which freezes it
against a rename; it is the only thing here that touches the automation repo,
and it is off unless asked for.

Read by import-features.sh, which passes the features directory.
"""
import os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caseid

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
where = sys.argv[1]
rest = sys.argv[2:]
wanted_tag = next((a for a in rest if a.startswith("@")), "")
project = next((a.split("=", 1)[1] for a in rest if a.startswith("--project=")), "")
dry = "--dry-run" in rest
write_tags = "--write-tags" in rest
prefix = next((a.split("=", 1)[1] for a in rest if a.startswith("--prefix=")), project or "ACME")

CASE_ID = caseid.WRITTEN

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
    for number, line in enumerate(open(path, encoding="utf-8").read().splitlines()):
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
            current = {"feature": feature, "tags": tags, "file": path,
                       "line": number, "indent": line[:len(line) - len(bare)],
                       "name": bare.split(":", 1)[1].strip(), "steps": []}
            tags = []
            continue
        if current is not None and bare and not bare.startswith("#"):
            current["steps"].append(bare)
    if current:
        out.append(current)
    return out

def freeze(path, marks):
    """Put the derived tags into the .feature, above the scenarios they name."""
    lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
    for number, indent, tag in sorted(marks, reverse=True):
        lines.insert(number, indent + "@" + tag + "\n")
    open(path, "w", encoding="utf-8").write("".join(lines))


made = skipped = guessed = frozen = 0
for base, _, files in os.walk(where):
    for name in sorted(files):
        if not name.endswith(".feature"):
            continue
        marks = []
        for s in scenarios(os.path.join(base, name)):
            ident, told = caseid.identity(s["tags"], name, s["name"], prefix)
            if not told:
                guessed += 1
                if write_tags and not dry:
                    marks.append((s["line"], s["indent"], ident))
                    frozen += 1
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
            body += ["```", "", "From `" + s["feature"] + "` in the automation repository."]
            body += ["Identity is the case id, not this title: a title gets improved."] if told else [
                "**No case id in the automation**, so this one was derived from the feature "
                "file and the scenario name. Rename the scenario and it becomes a different "
                "test; tag the scenario `@" + ident + "` to settle it."]
            with open(os.path.join(root, at.strip()), "a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(body) + "\n")

            # One call, not three: eight hundred scenarios is eight hundred
            # processes per property otherwise.
            args = [key, "automation_id=" + ident, "automated=true"]
            if not told:
                # Recorded, because a derived id is a guess about identity and
                # anything reading this later deserves to know which ids the
                # automation says and which the tool worked out.
                args.append("generated=true")
            tags = [t[1:] for t in s["tags"] if not CASE_ID.match(t) and t != "@acme"]
            if tags:
                args.append("tags=" + ",".join(tags[:6]))
            run("set", *args, "--quiet")
            made += 1
        if marks:
            freeze(os.path.join(base, name), marks)

print(f"{made} tests written, {skipped} already here")
if guessed:
    print(f"{guessed} scenarios carry no case id, so one was derived from the "
          "feature and the scenario name.")
    if frozen:
        print(f"{frozen} of those tags were written back into the .feature files — "
              "commit that repo and the ids survive a rename.")
    else:
        print("Rename one of those scenarios and its id changes with it. "
              "--write-tags puts the derived tag in the .feature and settles it.")
if dry:
    print("Nothing was written: --dry-run.")
