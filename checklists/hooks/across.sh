#!/bin/sh
# Where the open work stands against its own acceptance criteria.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Acceptance across the board\n\n'
"$docket" export --format csv --open --fields checked,boxes,board "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 {
    # `board: false` in docket.yaml says a type is a record of something rather
    # than work somebody does — a test, a run, an execution. Nobody writes an
    # acceptance list for a machine-written record, so counting them made "No
    # list at all" the whole story and hid how the real work is doing.
    if ($3 == "false") next
    if ($2 == 0) { none++; next }
    if ($1 == $2) { full++; next }
    partial++
  }
  END {
    printf "| | Tasks |\n|---|---:|\n"
    printf "| Every box ticked | %d |\n", full + 0
    printf "| Some ticked | %d |\n", partial + 0
    printf "| No list at all | %d |\n", none + 0
  }'
printf '\nA task with no acceptance list is not a fault. It is a question: how\n'
printf 'would anybody else know it was finished?\n'
