#!/bin/sh
# Run every scenario in the vault and bring the results back in.
#
# This app does not contain a test runner and will not pretend to be one: what
# runs your Gherkin is behave, cucumber, pytest-bdd or whatever your project
# already uses. This collects the scenarios, hands them to a script in the
# repository called `run-tests`, and imports the JUnit it leaves behind.
#
#   ./run-tests <feature-file> <junit-out>
#
# Three lines, usually. Written by you, because only you know which runner and
# which environment — and because a button that ran something the team did not
# choose would be a button nobody presses twice.
set -eu
docket="${DOCKET_BIN:-docket}"
root="${DOCKET_ROOT:-$(pwd)}"
cd "$root"

if [ ! -x ./run-tests ]; then
  cat <<'SAID'
There is no ./run-tests in this repository, so nothing ran.

Write one — it takes a feature file and the path to write JUnit XML to:

  #!/bin/sh
  behave "$1" --junit --junit-directory "$(dirname "$2")"

Then this button collects every gherkin block in the vault, hands the file to
it, and imports the results as an execution with a run per test.
SAID
  exit 1
fi

features=$(mktemp -d)/scenarios.feature
results=$(mktemp -d)/junit.xml
mkdir -p "$(dirname "$features")" "$(dirname "$results")"

# The same collection the Feature file page shows, without the prose around it.
"$docket" export --format json --body . | python3 -c '
import json, re, sys
tasks = json.load(sys.stdin)
print("Feature: every scenario in the vault")
print()
for t in sorted(tasks, key=lambda t: t["key"]):
    if t.get("type") not in ("test", "test_run"):
        continue
    for block in re.findall(r"```gherkin\n(.*?)```", t.get("body", ""), re.S):
        ident = (t.get("fields") or {}).get("automation_id") or t["key"]
        print("  @" + ident.replace(" ", "_"))
        print("  Scenario: " + t["title"])
        for line in block.strip().splitlines():
            print("    " + line.strip())
        print()
' > "$features"

printf 'Collected %s scenarios.\n' "$(grep -c '^  Scenario:' "$features" || echo 0)"

set +e
./run-tests "$features" "$results"
code=$?
set -e
printf 'The runner exited %s.\n\n' "$code"

if [ -s "$results" ]; then
  hooks/import-junit.sh "$results" --environment "${DOCKET_ENVIRONMENT:-local}" \
    --revision "$(git rev-parse --short HEAD 2>/dev/null || echo unsaid)"
else
  printf 'It wrote no JUnit at %s, so there is nothing to import.\n' "$results"
  exit 1
fi
