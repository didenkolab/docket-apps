#!/bin/sh
# Containers and what is under them, with how much of it is finished.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Where each container stands\n\n'
printf '| Container | Done | Of | Left |\n|---|---:|---:|---:|\n'
"$docket" export --format csv --fields parent,category "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 && $1 != "" {
    under[$1]++
    if ($2 == "done") closed[$1]++
  }
  END {
    for (p in under)
      printf "| %s | %d | %d | %d |\n", p, closed[p] + 0, under[p], under[p] - closed[p]
  }' | sort

printf '\nCounted by tasks rather than by estimate: a container is finished when\n'
printf 'the work under it is, and half the work is usually unsized.\n'
