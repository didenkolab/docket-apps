"""What failed, grouped by the execution it failed in.

Reads the JSON export rather than the CSV one, and the reason is a comma. A
scenario is called "a refused payout announces a balance, unchanged" and an
assertion says "expected 3, got 4" — split those on commas and the page shows
half a sentence. CSV is right for a column of keys and wrong for prose.
"""
import json
import os
import subprocess
import sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")

out = subprocess.run([docket, "export", "--format", "json"],
                     capture_output=True, text=True, cwd=root)
if out.returncode != 0:
    sys.exit(0)
tasks = json.loads(out.stdout)

titles = {t["key"]: t.get("title", "") for t in tasks}
kinds = {t["key"]: t.get("type", "") for t in tasks}
# What each test covers, so a failure can be reported as work rather than as a
# scenario. "Fourteen scenarios failed" is a number; "the payout story and the
# allowlist story have failing tests" is a decision about shipping.
covers = {t["key"]: (t.get("relations") or {}).get("tests", [])
          for t in tasks if t.get("type") == "test"}
failed = {}
for t in tasks:
    if t.get("type") != "test_run":
        continue
    if (t.get("fields") or {}).get("result") != "failed":
        continue
    failed.setdefault(t.get("parent", ""), []).append(t)

if not failed:
    print("Nothing has failed in any recorded execution.")
    sys.exit(0)

# The work behind the failures, before the failures themselves: it is the
# shorter list and the one somebody acts on.
hurt = {}
for runs in failed.values():
    for run in runs:
        for test in (run.get("relations") or {}).get("runs", []):
            for key in covers.get(test, []):
                hurt.setdefault(key, set()).add(test)
if hurt:
    print("### Work with a failing test")
    print()
    for key in sorted(hurt, key=lambda k: (-len(hurt[k]), k)):
        print("- [%s](/task/%s) %s — %d failing %s" % (
            key, key, titles.get(key, ""), len(hurt[key]),
            "test" if len(hurt[key]) == 1 else "tests"))
    print()
    print("Derived from what each test says it covers, which was itself derived "
          "from the automation's history. Wrong links are fixed on the test.")
    print()

# Worst execution first: the one with most failures is the one somebody is
# about to be asked about.
for execution in sorted(failed, key=lambda k: -len(failed[k])):
    where = titles.get(execution, execution) or "no execution"
    print("### [%s](/task/%s) — %s" % (execution, execution, where))
    print()
    print("%d failed." % len(failed[execution]))
    print()
    for run in sorted(failed[execution], key=lambda t: t.get("title", "")):
        why = (run.get("fields") or {}).get("evidence", "").strip()
        print("- [%s](/task/%s)" % (run.get("title") or run["key"], run["key"]))
        if why:
            print("  - `%s`" % why.replace("`", "'"))
    print()
