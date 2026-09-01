"""Turn a Cucumber project's cases into tests in the vault.

One task per **case**, not per scenario. That distinction cost a rewrite and is
the whole design:

  a case is a thing that must be true — `ACME-INV-055`, and the tag is its name;
  a scenario is one way of making it true.

One scenario can settle two cases at once (`@ACME-INV-049 @ACME-INV-048` on the
paid-invoice walk), and two scenarios can settle one case from different
directions. Reading a scenario as a test made both of those look like duplicate
ids in a suite that had none, and a real board lost 151 tests to a cleanup that
was fixing nothing.

A scenario nobody tagged has no case, so one is derived for it from the feature
file and the scenario's name (caseid.py). Skipping them was worse: a fifth of a
real suite carries no tag, and a fifth of every run then had nothing to land on.
--write-tags puts the derived id back into the .feature, which freezes it
against a rename; it is the only thing here that touches the automation repo,
and it is off unless asked for.

Read by import-features.sh, which passes the features directory.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caseid

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
where = sys.argv[1]
rest = sys.argv[2:]
wanted_tag = next((a for a in rest if a.startswith("@")), "")
project = next((a.split("=", 1)[1] for a in rest if a.startswith("--project=")), "")
prefix = next((a.split("=", 1)[1] for a in rest if a.startswith("--prefix=")), project or "ACME")
dry = "--dry-run" in rest
write_tags = "--write-tags" in rest

SCENARIO = re.compile(r"^(Scenario|Scenario Outline|Example):")


def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()


# What is already here, by case id, so running this twice does not double.
known = {}
for t in json.loads(run("export", "--format", "json")):
    ident = (t.get("fields") or {}).get("automation_id", "").strip()
    if ident:
        known[ident] = t["key"]


def scenarios(path, name):
    """Every scenario in one .feature: its tags, name, steps, and where it is.

    Tags accumulate across lines, because Gherkin says they do — a tag line,
    a comment, another tag line, then the scenario, and all of them apply.
    """
    feature, tags, out, current = "", [], [], None
    for number, line in enumerate(open(path, encoding="utf-8").read().splitlines()):
        bare = line.strip()
        if bare.startswith("Feature:"):
            feature, tags = bare[len("Feature:"):].strip(), []
            continue
        if bare.startswith("@"):
            tags = tags + bare.split()
            continue
        if SCENARIO.match(bare):
            current = {"feature": feature, "tags": tags, "file": name,
                       "line": number, "indent": line[:len(line) - len(bare)],
                       "name": bare.split(":", 1)[1].strip(), "steps": []}
            out.append(current)
            tags = []
            continue
        if current is not None and bare and not bare.startswith("#"):
            current["steps"].append(bare)
    return out


def freeze(path, marks):
    """Put the derived tags into the .feature, above the scenarios they name."""
    lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
    for number, indent, tag in sorted(marks, reverse=True):
        lines.insert(number, indent + "@" + tag + "\n")
    open(path, "w", encoding="utf-8").write("".join(lines))


# Every scenario first, then the cases they settle. Two passes, because a case
# is only whole once every file has been read: the two scenarios that cover
# ACME-INV-055 sit in different folders.
found = []
for base, _, files in os.walk(where):
    for name in sorted(files):
        if name.endswith(".feature"):
            found.append((os.path.join(base, name), name))
found.sort()

cases, order, guessed, frozen = {}, [], 0, 0
for path, name in found:
    marks = []
    for s in scenarios(path, name):
        if wanted_tag and wanted_tag not in s["tags"]:
            continue
        ids = caseid.all_written(s["tags"])
        if not ids:
            derived = caseid.derived(name, s["name"], prefix)
            ids = [derived]
            s["derived"] = True
            guessed += 1
            if write_tags and not dry:
                marks.append((s["line"], s["indent"], derived))
                frozen += 1
        for ident in ids:
            if ident not in cases:
                cases[ident] = []
                order.append(ident)
            cases[ident].append(s)
    if marks:
        freeze(path, marks)

made = skipped = 0
for ident in order:
    if ident in known:
        skipped += 1
        continue
    covered = cases[ident]
    told = not covered[0].get("derived")
    if dry:
        made += 1
        continue

    # `docket new` prints the key and the path it wrote, which is why this does
    # not ask for the path again: an export per case is a 3 MB read seven
    # hundred times over.
    made_line = run("new", covered[0]["name"][:120], "--type", "test",
                    *(["--project", project] if project else []))
    key, at = made_line.split(None, 1)

    body = []
    for s in covered:
        if len(covered) > 1:
            body += ["## " + s["name"], ""]
        else:
            body += ["## Scenario", ""]
        body += ["```gherkin"] + ["  " + step for step in s["steps"]] + ["```", ""]
        body += ["From `" + s["feature"] + "` in `" + s["file"] + "`.", ""]
    if len(covered) > 1:
        body += ["This case is settled by " + str(len(covered)) + " scenarios. "
                 "A case is a thing that must be true; a scenario is one way of "
                 "making it true, and a result from any of them is a result for "
                 "this case.", ""]
    if told:
        body += ["Identity is the case id, not this title: a title gets improved."]
    else:
        body += ["**No case id in the automation**, so this one was derived from the "
                 "feature file and the scenario name. Rename the scenario and it "
                 "becomes a different test; tag the scenario `@" + ident + "` to "
                 "settle it."]
    with open(os.path.join(root, at.strip()), "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(body) + "\n")

    # One call, not three: seven hundred cases is seven hundred processes per
    # property otherwise.
    args = [key, "automation_id=" + ident, "automated=true"]
    if not told:
        args.append("generated=true")
    tags = []
    for s in covered:
        for tag in s["tags"]:
            bare = tag.lstrip("@")
            if not caseid.WRITTEN.match(tag) and bare != "acme" and bare not in tags:
                tags.append(bare)
    if tags:
        args.append("tags=" + ",".join(tags[:6]))
    run("set", *args, "--quiet")
    known[ident] = key
    made += 1

shared = sum(1 for ident in cases if len(cases[ident]) > 1)
print(f"{made} tests written, {skipped} already here — one per case, "
      f"from {sum(len(v) for v in cases.values())} scenario tags.")
if shared:
    print(f"{shared} cases are settled by more than one scenario, which is not a "
          "duplicate: each test carries every scenario that covers it.")
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
