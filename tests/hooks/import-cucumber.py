"""Bring a Cucumber JSON report in as an execution and a run per scenario.

Cucumber's JSON rather than its JUnit, and the reason is the identity: JUnit
carries a class name and a scenario name and no tags, so the case id — the one
stable thing about a scenario — is not in it. Matching on the name instead would
attach a run to the wrong test the first time somebody rewords one.

A scenario the automation never tagged is identified the way import-features
identified it — derived from the feature file and the scenario name, by the same
function — so a result lands on the test even when nobody wrote an id. Both
sides derive it; neither invents it.
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caseid

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")
report = sys.argv[1]
environment = sys.argv[2] if len(sys.argv) > 2 else "unsaid"
revision = sys.argv[3] if len(sys.argv) > 3 else ""
project = sys.argv[4] if len(sys.argv) > 4 else ""
prefix = (sys.argv[5] if len(sys.argv) > 5 else "") or caseid.project_key(root, project)

def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()

by_id = {}
for t in json.loads(run("export", "--format", "json")):
    ident = (t.get("fields") or {}).get("automation_id", "").strip()
    if ident and t.get("type") == "test":
        by_id[ident] = (t["key"], t.get("title", ""))

outcome = {}   # case id -> (result, one line, the whole message)
names = {}     # case id -> what the scenario is called
derived = set()
for feature in json.load(open(report, encoding="utf-8")):
    uri = feature.get("uri") or feature.get("name") or ""
    for e in feature.get("elements", []):
        if e.get("type") == "background":
            continue
        # Every case this scenario settles, not just the first: a scenario
        # tagged with two case ids is a result for both, and reading only the
        # first left half the suite's coverage with no result at all.
        idents = caseid.all_written(caseid.tags_of(e))
        if not idents:
            idents = [caseid.derived(uri, e.get("name", ""), prefix)]
            derived.add(idents[0])
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
        # A Scenario Outline is one test and several rows in the report. The
        # test failed if any row did — reporting the last row's result would
        # make a suite green because its final example happened to pass.

        # The whole message, not the summary line: the summary is what a table
        # can hold, and the stack is what somebody fixing it reads. Both, in
        # different places, so neither has to be looked up elsewhere.
        whole = ""
        if result[0] == "failed":
            whole = (broke.get("error_message") or "").strip()
        for ident in idents:
            # A Scenario Outline is one case and several rows in the report, and
            # a case settled by two scenarios is one case and two results. The
            # case failed if any of them did — taking the last would make a
            # suite green because its final example happened to pass.
            if outcome.get(ident, ("", "", ""))[0] == "failed":
                continue
            outcome[ident] = (result[0], result[1], whole)
            names[ident] = e.get("name", "")

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

for ident, (result, why, whole) in sorted(matched.items()):
    test, test_title = by_id[ident]
    # Named after the scenario, not after the case id. A page of seven hundred
    # runs called ACME-RPT-005 is a page nobody can read; the id is a field, and
    # it is a field precisely so that the title can be language.
    made = run("new", (names.get(ident) or test_title or ident)[:120],
               "--type", "test_run", "--parent", execution,
               *(["--project", project] if project else []))
    key, at = made.split(None, 1)
    args = [key, "result=" + result, "runs=" + test, "automation_id=" + ident]
    if why:
        args.append("evidence=" + why)
    run("set", *args, "--quiet")

    # What happened, in place of the template's instructions on how to write it.
    # Those are for a person filling one in by hand; on a machine-written run
    # they are seven hundred copies of a note to somebody who will never read it.
    said = ["## What happened", ""]
    if result == "failed":
        said += ["**Failed** on " + environment +
                 (" at `" + revision + "`" if revision else "") + ".", ""]
        said += ["```", (whole or why)[:1500], "```", ""]
    elif result == "passed":
        said += ["**Passed** on " + environment +
                 (" at `" + revision + "`" if revision else "") + ".", ""]
    else:
        said += ["**" + result.title() + "** on " + environment + ".", ""]
    said += ["Case `" + ident + "`, from the Cucumber report — "
             "nothing here was typed by hand."]
    body = open(os.path.join(root, at.strip()), encoding="utf-8").read()
    head = body.split("---", 2)
    if len(head) >= 3:
        body = "---" + head[1] + "---\n\n" + "\n".join(said) + "\n"
        open(os.path.join(root, at.strip()), "w", encoding="utf-8").write(body)

print(f"{execution}: {len(matched)} runs written.")
for result in ("passed", "failed", "aborted"):
    n = sum(1 for r, _, _ in matched.values() if r == result)
    if n:
        print(f"  {result}: {n}")
if missing:
    print(f"\n{len(missing)} case ids ran and are not in the vault: " + ", ".join(missing[:8]))
    print("Run import-features again — the automation has grown since.")
ran_derived = sorted(i for i in matched if i in derived)
if ran_derived:
    print(f"\n{len(ran_derived)} of those carry no case id in the automation; "
          "their identity was derived from the feature and the scenario name.")
