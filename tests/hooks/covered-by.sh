#!/bin/sh
# The tests that name this task, with what state each is in.
set -eu
docket="${DOCKET_BIN:-docket}"
key=$(cat | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
[ -n "$key" ] || exit 0

"$docket" export --format csv --fields key,type,status,tests,title "$DOCKET_ROOT" |
  awk -F',' -v key="$key" '
    NR == 1 { next }
    $2 == "test" || $2 == "test_run" {
      split($4, covers, " ")
      for (i in covers) if (covers[i] == key) {
        title = substr($0, index($0, $5)); gsub(/^"|"$/, "", title)
        printf "- [**%s**](/task/%s) %s — %s\n", $1, $1, title, $3
        found++
      }
    }
    END { if (!found) printf "" }'
