#!/bin/sh
# Containers and what is under them, with how much of it is finished.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Where each container stands\n\n'
printf '| Container | Done | Of | Left |\n|---|---:|---:|---:|\n'
"$docket" export --format csv --fields parent,category,board "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 && $1 != "" {
    # `board: false` in docket.yaml says a type is a record of something rather
    # than work somebody does — a test, a run, an execution. Rolling them up
    # counts the test runs under a container as work left to do, and a
    # container nobody has touched can read as the busiest one on the page.
    if ($3 == "false") next
    under[$1]++
    if ($2 == "done") closed[$1]++
  }
  END {
    for (p in under)
      printf "| [%s](/task/%s) | %d | %d | %d |\n", p, p, closed[p] + 0, under[p],
             under[p] - closed[p]
  }' | sort

printf '\nCounted by tasks rather than by estimate: a container is finished when\n'
printf 'the work under it is, and half the work is usually unsized.\n'
