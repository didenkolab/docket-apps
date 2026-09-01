#!/bin/sh
# Every scenario in the vault, as one feature file a runner can take.
#
# Needs python3, which is on every machine this runs on and is the only
# dependency in this app. The script is written to a file rather than piped in:
# a heredoc on stdin and the JSON on stdin are the same stdin.
set -eu
docket="${DOCKET_BIN:-docket}"
script=$(mktemp)
trap 'rm -f "$script"' EXIT

cat > "$script" <<'PY'
import json, re, sys

tasks = json.load(sys.stdin)
out, found = [], 0
for t in sorted(tasks, key=lambda t: t["key"]):
    if t.get("type") not in ("test", "test_run"):
        continue
    for block in re.findall(r"```gherkin\n(.*?)```", t.get("body", ""), re.S):
        covers = " ".join(t.get("relations", {}).get("tests", []))
        head = "# " + t["key"] + " " + t["title"]
        if covers:
            head += " - covers " + covers
        out.append(head)
        out.append("Scenario: " + t["title"])
        out += ["  " + line.strip() for line in block.strip().splitlines()]
        out.append("")
        found += 1

if found:
    print("```gherkin")
    print("\n".join(out).rstrip())
    print("```")
    print()
    print(str(found) + " scenarios, collected from the tests themselves.")
else:
    print("No scenario yet. A test carries one in a gherkin block; the template")
    print("that came with this app has the shape.")
PY

printf '## The feature file\n\n'
printf 'Every gherkin block in every test, collected. Copy it into a runner, or keep\n'
printf 'this page open beside the work — it is the same text either way.\n\n'
"$docket" export --format json --body "$DOCKET_ROOT" | python3 "$script"
