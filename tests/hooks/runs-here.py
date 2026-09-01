"""On an execution: what failed, first and in full; what passed, as a number.

A list of four hundred ticks with fourteen crosses in it is a list nobody reads
to the end — and the fourteen are the entire reason anybody opened the page. So
the failures come first, with the scenario's own name and the assertion that
broke, and the passes are counted rather than enumerated.

JSON rather than CSV, because a scenario name and an assertion both contain
commas and a page showing half a sentence is worse than no page.
"""
import json
import os
import subprocess
import sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")

told = json.loads(sys.stdin.read() or "{}")
key = told.get("key", "")
if not key:
    sys.exit(0)

out = subprocess.run([docket, "export", "--format", "json"],
                     capture_output=True, text=True, cwd=root)
if out.returncode != 0:
    sys.exit(0)
tasks = json.loads(out.stdout)

runs = [t for t in tasks if t.get("type") == "test_run" and t.get("parent") == key]
if not runs:
    sys.exit(0)

failed = [t for t in runs if (t.get("fields") or {}).get("result") == "failed"]
passed = sum(1 for t in runs if (t.get("fields") or {}).get("result") == "passed")
other = len(runs) - len(failed) - passed

if failed:
    print("**%d failed**" % len(failed))
    print()
    for run in sorted(failed, key=lambda t: t.get("title", "")):
        fields = run.get("fields") or {}
        print("- [%s](/task/%s)" % (run.get("title") or run["key"], run["key"]))
        why = fields.get("evidence", "").strip()
        if why:
            print("  - `%s`" % why.replace("`", "'"))
        ran = fields.get("runs", "") or ""
        if ran:
            print("  - the test: %s" % ran)
    print()

tail = []
if passed:
    tail.append("%d passed" % passed)
if other:
    tail.append("%d neither" % other)
if tail:
    print(", ".join(tail) + ".")
