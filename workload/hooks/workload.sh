#!/bin/sh
# Open work per person, with estimates where they exist. Columns are asked for
# by name: a title may hold a comma, and counting columns is how an app comes
# to read the wrong one.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Who is carrying what\n\n'
printf '| Person | Open | Sized | Total |\n|---|---:|---:|---:|\n'
"$docket" export --format csv --open --fields assignee,estimate "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 {
    who = ($1 == "" ? "(nobody)" : $1)
    tasks[who]++
    if ($2 != "") { points[who] += $2; sized[who]++ }
  }
  END {
    for (who in tasks)
      printf "%d\t| %s | %d | %d | %s |\n", tasks[who], who, tasks[who], sized[who] + 0,
             (points[who] ? points[who] : "—")
  }' | sort -rn | cut -f2-

printf '\nUnsized work is counted but not totalled: a total that quietly leaves\n'
printf 'out what nobody estimated is a total that reads as the whole.\n'
