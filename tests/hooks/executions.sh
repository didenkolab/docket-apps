#!/bin/sh
# What each execution came to: how many passed, failed, and never ran.
set -eu
docket="${DOCKET_BIN:-docket}"
runs=$(mktemp); heads=$(mktemp)
trap 'rm -f "$runs" "$heads"' EXIT

"$docket" export --format csv --fields type,parent,result "$DOCKET_ROOT" > "$runs"
"$docket" export --format csv --fields key,type,environment,revision,title "$DOCKET_ROOT" > "$heads"

printf '## Executions\n\n'

# The picture first, because the shape of the last dozen runs is the thing
# anybody looks at before reading a table. It is a file in the vault, so it is
# committed, diffed, and there in Obsidian too.
python3 hooks/charts.py attachments/test-results.svg >/dev/null 2>&1 || true
if [ -f attachments/test-results.svg ]; then
  # DOCKET_PREFIX is where this vault sits in the space — empty for a repository
  # opened on its own, "acme/" inside a workspace. Given rather than guessed.
  printf '![Results of the last executions](/file/%sattachments/test-results.svg)\n\n' "${DOCKET_PREFIX:-}"
fi

awk -F',' '
  NR == FNR {
    if (FNR == 1 || $1 != "test_run") next
    total[$2]++
    if ($3 == "passed") passed[$2]++
    else if ($3 == "failed") failed[$2]++
    else if ($3 == "aborted") aborted[$2]++
    else waiting[$2]++
    next
  }
  FNR == 1 { next }
  $2 == "test_execution" {
    key = $1
    title = substr($0, index($0, $5)); gsub(/^"|"$/, "", title)
    seen++
    printf "| [%s](/task/%s) %s | %s | %s | %d | %d | %d | %d |\n",
      key, key, title, ($3 == "" ? "—" : $3), ($4 == "" ? "—" : $4),
      passed[key] + 0, failed[key] + 0, aborted[key] + 0, waiting[key] + 0
  }
  END {
    if (!seen) print "no-executions"
  }' "$runs" "$heads" > /tmp/docket-exec.$$ || true

if grep -q '^no-executions$' /tmp/docket-exec.$$ 2>/dev/null; then
  printf 'Nothing has been executed yet. An execution is a task of type\n'
  printf '`test_execution` — the template that came with this app has the shape —\n'
  printf 'and its runs are its children.\n'
else
  printf '| Execution | Environment | Revision | Passed | Failed | Aborted | Waiting |\n'
  printf '|---|---|---|---:|---:|---:|---:|\n'
  cat /tmp/docket-exec.$$
  printf '\nA run is a note under its execution, pointing at the test with `runs:`.\n\n'

  # What failed, across every execution. The table says how many; this says
  # which — and which is the only part anybody acts on.
  printf '## What failed\n\n'
  python3 hooks/failures.py || true
fi
rm -f /tmp/docket-exec.$$
