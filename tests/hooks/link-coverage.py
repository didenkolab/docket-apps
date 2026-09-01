"""Point each imported test at the work it was written for.

A test that hangs off nothing answers "did it pass". A test linked to the story
it covers answers the question anybody actually asks when a run goes red: what
broke, for whom, and is it shippable. It is also the only way the graph is worth
drawing — story, test, run is a chain, and Obsidian will draw it because every
step of it is a wikilink.

Nobody wrote that link down, so it is derived, from two things the automation
repository already knows:

  the blame — the commit that introduced the scenario's own lines. A suite whose
  subjects read "test(chain): count the settle budget twice (ACME-961)" is a
  suite that recorded, at the time and by hand, which ticket each scenario was
  written for. This is the strong signal.

  the text — a key the scenario or its comments name, "since ACME-1000". Weaker:
  it says the ticket changed the behaviour, not that this scenario covers it.

Both are guesses, so both are written down on the test, and a key the board does
not have is dropped rather than invented. Correct one by editing the test: this
runs again without undoing anything a person did, because it only adds.

  hooks/link-coverage.sh <features-dir> --repo <automation repo> [--project KEY]
                         [--limit N] [--dry-run]
"""
import json
import os
import re
import subprocess
import sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caseid

where = sys.argv[1]
rest = sys.argv[2:]
repo = next((a.split("=", 1)[1] for a in rest if a.startswith("--repo=")), where)
project = next((a.split("=", 1)[1] for a in rest if a.startswith("--project=")), "")
most = int(next((a.split("=", 1)[1] for a in rest if a.startswith("--limit=")), "5"))
dry = "--dry-run" in rest

KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d{1,6})\b")


def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()


def git(*args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


# The board as it is: what exists to be linked to, and which tests are here.
# Only real work gets linked — a key the automation names that the board never
# had is a key somebody deleted or mistyped, and a wikilink to it would be a
# dead link on eight hundred pages.
work, tests = {}, {}
for t in json.loads(run("export", "--format", "json")):
    if t.get("type") in ("test", "test_run", "test_execution", "test_set", "test_plan"):
        ident = (t.get("fields") or {}).get("automation_id", "").strip()
        if t.get("type") == "test" and ident:
            tests[ident] = t
        continue
    work[t["key"]] = t


def spans(path):
    """Every scenario in one .feature: its tags, its name, and the lines it holds."""
    lines = open(path, encoding="utf-8").read().splitlines()
    out, current, pending = [], None, []
    for number, line in enumerate(lines, start=1):
        bare = line.strip()
        if bare.startswith("@"):
            if current:
                current["to"] = number - 1
                current = None
            pending = bare.split()
            continue
        if re.match(r"^(Scenario|Scenario Outline|Example):", bare):
            if current:
                current["to"] = number - 1
            current = {"name": bare.split(":", 1)[1].strip(), "tags": pending,
                       "from": number, "to": len(lines)}
            out.append(current)
            pending = []
    return out, lines


def blamed(path):
    """Line number -> the subject of the commit that last touched that line."""
    said = git("blame", "-w", "--line-porcelain", "--", os.path.relpath(path, repo))
    out, line, summary = {}, 0, ""
    for row in said.splitlines():
        head = row.split(" ", 3)
        if len(head) >= 3 and re.fullmatch(r"[0-9a-f]{40}", head[0]):
            line = int(head[2])
        elif row.startswith("summary "):
            summary = row[len("summary "):]
        elif row.startswith("\t"):
            out[line] = summary
    return out


linked = touched = 0
for base, _, files in os.walk(where):
    for name in sorted(files):
        if not name.endswith(".feature"):
            continue
        path = os.path.join(base, name)
        found, lines = spans(path)
        if not found:
            continue
        by_line = blamed(path)

        for s in found:
            ident, _ = caseid.identity(s["tags"], name, s["name"],
                                       project or "ACME")
            test = tests.get(ident)
            if not test:
                continue

            from_history, from_text = [], []
            for number in range(s["from"], s["to"] + 1):
                for key in KEY.findall(by_line.get(number, "")):
                    if key in work and key not in from_history:
                        from_history.append(key)
                if number - 1 < len(lines):
                    for key in KEY.findall(lines[number - 1]):
                        if key in work and key not in from_text:
                            from_text.append(key)

            # History first, then mentions, because the commit that wrote the
            # scenario knew what it was for and a comment only knows what
            # changed. Capped: a file an epic rewrote names twenty tickets, and
            # a test that covers twenty things covers nothing.
            keys, why = [], []
            for key in from_history + [k for k in from_text if k not in from_history]:
                if len(keys) >= most:
                    break
                keys.append(key)
                why.append("the commit that wrote it" if key in from_history
                           else "named in the scenario")
            if not keys:
                continue

            already = (test.get("relations") or {}).get("tests", [])
            fresh = [k for k in keys if k not in already]
            if not fresh:
                continue
            touched += 1
            linked += len(fresh)
            if dry:
                continue
            run("set", test["key"], "tests=" + ",".join(already + fresh), "--quiet")

            with open(os.path.join(root, test["path"]), "a", encoding="utf-8") as f:
                f.write("\n## What this covers\n\n")
                f.write("Derived, not declared — correct it by editing the "
                        "`tests:` links above.\n\n")
                # The keys are plain here on purpose: the links live in
                # `tests:` above, and a second set of them in the body would
                # be two things to keep true instead of one.
                for key, said in zip(keys, why):
                    if key in fresh:
                        f.write("- %s — %s\n" % (key, said))

print(f"{touched} tests now point at work, with {linked} links between them.")
if dry:
    print("Nothing was written: --dry-run.")
