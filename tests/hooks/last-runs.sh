#!/bin/sh
# Every run of this test, newest first — or, on a piece of work, the runs of
# the tests that cover it.
set -eu
docket="${DOCKET_BIN:-docket}"
key=$(cat | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
[ -n "$key" ] || exit 0

"$docket" export --format csv --fields key,type,runs,result,ran_at,parent "$DOCKET_ROOT" |
  awk -F',' -v key="$key" '
    NR == 1 { next }
    $2 == "test_run" {
      split($3, of, " ")
      for (i in of) if (of[i] == key) {
        printf "- **%s** in [%s](/task/%s)%s\n", ($4 == "" ? "todo" : $4),
          ($6 == "" ? "no execution" : $6), $6, ($5 == "" ? "" : " — " $5)
        found++
      }
    }
    END { if (!found) printf "" }'
