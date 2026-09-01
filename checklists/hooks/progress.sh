#!/bin/sh
# What is ticked on this one task. Silent when there is no list.
set -eu
docket="${DOCKET_BIN:-docket}"
key=$(cat | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
[ -n "$key" ] || exit 0

"$docket" export --format csv --fields key,checked,boxes "$DOCKET_ROOT" |
  awk -F',' -v key="$key" 'NR > 1 && $1 == key {
    if ($3 == 0) exit
    printf "**%d of %d** ticked.\n\n", $2, $3
    if ($2 < $3) printf "%d left before this can be called done.\n", $3 - $2
    else printf "Everything on the list is ticked.\n"
  }'
