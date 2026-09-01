#!/bin/sh
# Bring a runner's results in: JUnit XML becomes an execution and a run per test.
#
# Run by a person or by CI, not by the server — it writes tasks, and what writes
# tasks should be something somebody started on purpose:
#
#   hooks/import-junit.sh results.xml --environment staging --revision "$(git rev-parse --short HEAD)"
#
# A testcase is matched to a test by `automation_id`. Nothing is guessed from
# titles: a title is written for people and changes when somebody improves the
# wording, and a run attached to the wrong test is worse than one attached to
# none.
set -eu
docket="${DOCKET_BIN:-docket}"
root="${DOCKET_ROOT:-$(pwd)}"

file=""; environment=""; revision=""; execution=""; commit=""
while [ $# -gt 0 ]; do
  case "$1" in
    --commit)      commit=1;        shift 1 ;;
    --environment) environment="$2"; shift 2 ;;
    --revision)    revision="$2";    shift 2 ;;
    --execution)   execution="$2";   shift 2 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) file="$1"; shift ;;
  esac
done

command -v "$docket" >/dev/null 2>&1 || {
  echo "docket is not on the PATH. Put it there, or say DOCKET_BIN=/path/to/docket." >&2
  exit 2
}
[ -n "$file" ] || { echo "say which file: hooks/import-junit.sh results.xml" >&2; exit 2; }
[ -f "$file" ] || { echo "$file is not a file" >&2; exit 2; }
[ -n "$environment" ] || environment="unsaid"

script=$(mktemp); trap 'rm -f "$script"' EXIT
cat > "$script" <<'PY'
import json, subprocess, sys, os, xml.etree.ElementTree as ET

path, docket, root, environment, revision, execution = sys.argv[1:7]

def run(*args):
    # Run in the vault rather than naming it: the commands take a directory as
    # their last argument and a title as their first, and a title followed by a
    # path is a second positional nobody accepts.
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        print(out.stderr.strip() or out.stdout.strip(), file=sys.stderr)
        sys.exit(1)
    return out.stdout.strip()

# Who the runner's names belong to. Matched on automation_id and nothing else.
tasks = json.loads(run("export", "--format", "json"))
by_id = {}
for t in tasks:
    ident = (t.get("fields") or {}).get("automation_id", "").strip()
    if ident and t.get("type") == "test":
        by_id[ident] = t["key"]

cases = []
for suite in ET.parse(path).getroot().iter("testsuite"):
    for case in suite.iter("testcase"):
        name = ".".join(p for p in (case.get("classname"), case.get("name")) if p)
        result, why = "passed", ""
        for kind, said in (("failure", "failed"), ("error", "failed"), ("skipped", "aborted")):
            found = case.find(kind)
            if found is not None:
                result, why = said, (found.get("message") or "").strip()
                break
        cases.append((name, result, why))

if not cases:
    print("No testcase in that file.")
    sys.exit(0)

matched = [(n, r, w) for n, r, w in cases if n in by_id]
missing = [n for n, _, _ in cases if n not in by_id]

if not execution:
    title = "Run on " + environment + (" at " + revision if revision else "")
    line = run("new", title, "--type", "test_execution")
    execution = line.split()[0]
    run("set", execution, "environment=" + environment,
        *(["revision=" + revision] if revision else []), "--quiet")

for name, result, why in matched:
    key = by_id[name]
    line = run("new", name, "--type", "test_run", "--parent", execution)
    made = line.split()[0]
    args = [made, "result=" + result, "runs=" + key]
    if why:
        args.append("evidence=" + why[:200])
    run("set", *args, "--quiet")

print(f"{execution}: {len(matched)} runs written.")
for result in ("passed", "failed", "aborted"):
    n = sum(1 for _, r, _ in matched if r == result)
    if n:
        print(f"  {result}: {n}")
if missing:
    print()
    print(f"{len(missing)} testcases matched no test in the vault:")
    for name in missing[:10]:
        print("  " + name)
    print()
    print("Give the test an automation_id, or leave it — a runner running tests")
    print("the vault has never heard of is worth knowing about either way.")
PY

python3 "$script" "$file" "$docket" "$root" "$environment" "$revision" "$execution"

# The simplest way results reach a board: commit them. CI has a clone, the
# notes are files, and a push is the whole of the delivery — no endpoint, no
# secret to rotate, and the audit trail is the commit. Use the inbox instead
# only when CI must not have push rights.
if [ -n "$commit" ]; then
  cd "$root"
  git add -A
  git -c user.name="${DOCKET_AUTHOR_NAME:-CI}" \
      -c user.email="${DOCKET_AUTHOR_EMAIL:-ci@example.com}" \
      commit -q -m "Test results from ${environment}${revision:+ at $revision}" || true
  echo "committed. push when you are ready."
fi
