"""Bring a Cucumber JSON report in as an execution and a run per scenario.

Cucumber's JSON rather than its JUnit, and the reason is the identity: JUnit
carries a class name and a scenario name and no tags, so the case id — the one
stable thing about a scenario — is not in it. Matching on the name instead would
attach a run to the wrong test the first time somebody rewords one.
"""
import json, os, re, subprocess, sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
report = sys.argv[1]
environment = sys.argv[2] if len(sys.argv) > 2 else "unsaid"
revision = sys.argv[3] if len(sys.argv) > 3 else ""
project = sys.argv[4] if len(sys.argv) > 4 else ""

CASE_ID = re.compile(r"^@(SP|ACME)-[A-Z]+-\d+$")

def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()

by_id = {}
for t in json.loads(run("export", "--format", "json")):
    ident = (t.get("fields") or {}).get("automation_id", "").strip()
    if ident and t.get("type") == "test":
        by_id[ident] = t["key"]

outcome = {}   # case id -> (result, why)
unknown = []
for feature in json.load(open(report, encoding="utf-8")):
    for e in feature.get("elements", []):
        ident = next((t["name"][1:] for t in e.get("tags", []) if CASE_ID.match(t["name"])), "")
        steps = [s.get("result", {}) for s in e.get("steps", []) if "result" in s]
        if not steps:
            continue
        statuses = [s.get("status") for s in steps]
        if "failed" in statuses:
            broke = next(s for s in steps if s.get("status") == "failed")
            result = ("failed", (broke.get("error_message") or "").strip().splitlines()[0][:180])
        elif all(s == "passed" for s in statuses):
            result = ("passed", "")
        elif all(s in ("skipped", "undefined", "pending") for s in statuses):
            # A dry run: cucumber reports every step skipped. Not a result, and
            # recording it as one would say the suite passed when nothing ran.
            continue
        else:
            result = ("aborted", "")
        if not ident:
            unknown.append(e.get("name", "")[:70])
            continue
        outcome[ident] = result

if not outcome:
    sys.exit("nothing in that report has a result: a dry run reports every step skipped")

matched = {i: r for i, r in outcome.items() if i in by_id}
missing = sorted(i for i in outcome if i not in by_id)

title = "Cucumber on " + environment + (" at " + revision if revision else "")
# The execution belongs to a project: a board with ten projects has ten sets
# of results, and one of them being "the first project in the vault" is how
# somebody reads another team's run as their own.
execution = run("new", title, "--type", "test_execution",
                *(["--project", project] if project else [])).split()[0]
run("set", execution, "environment=" + environment,
    *(["revision=" + revision] if revision else []), "--quiet")

for ident, (result, why) in sorted(matched.items()):
    key = run("new", ident, "--type", "test_run", "--parent", execution,
              *(["--project", project] if project else [])).split()[0]
    args = [key, "result=" + result, "runs=" + by_id[ident]]
    if why:
        args.append("evidence=" + why)
    run("set", *args, "--quiet")

print(f"{execution}: {len(matched)} runs written.")
for result in ("passed", "failed", "aborted"):
    n = sum(1 for r, _ in matched.values() if r == result)
    if n:
        print(f"  {result}: {n}")
if missing:
    print(f"\n{len(missing)} case ids ran and are not in the vault: " + ", ".join(missing[:8]))
    print("Run import-features again — the automation has grown since.")
if unknown:
    print(f"\n{len(unknown)} scenarios ran carrying no case id, so nothing could hold their result.")
