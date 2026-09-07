#!/bin/sh
# Open work per person, with estimates where they exist. Columns are asked for
# by name: a title may hold a comma, and counting columns is how an app comes
# to read the wrong one.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Who is carrying what\n\n'
printf '| Person | Open | Sized | Total |\n|---|---:|---:|---:|\n'
"$docket" export --format csv --open --fields assignee,estimate,board "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 {
    # `board: false` in docket.yaml says a type is a record of something rather
    # than work somebody does — a test, a run, an execution. They are written by
    # a machine and nobody will ever be assigned one, so counting them made
    # "(nobody)" the largest row on the page and hid the imbalance between the
    # people who are actually carrying the work.
    if ($3 == "false") next
    who = ($1 == "" ? "" : $1)
    tasks[who]++
    if ($2 != "") { points[who] += $2; sized[who]++ }
  }
  END {
    for (who in tasks) {
      shown = (who == "" ? "(nobody)" : "[" who "](/person/" who ")")
      printf "%d\t| %s | %d | %d | %s |\n", tasks[who], shown, tasks[who], sized[who] + 0,
             (points[who] ? points[who] : "—")
    }
  }' | sort -rn | cut -f2-

printf '\nUnsized work is counted but not totalled: a total that quietly leaves\n'
printf 'out what nobody estimated is a total that reads as the whole. Types the\n'
printf 'vault marks `board: false` are left out entirely: nobody is going to be\n'
printf 'assigned a test run.\n'
