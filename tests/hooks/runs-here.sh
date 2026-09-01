#!/bin/sh
# On an execution: every run in it, with what happened. On anything else:
# nothing, because a panel that says "not applicable" on every task is a panel
# people stop seeing.
set -eu
docket="${DOCKET_BIN:-docket}"
key=$(cat | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
[ -n "$key" ] || exit 0

"$docket" export --format csv --fields key,type,parent,result,runs,evidence,title "$DOCKET_ROOT" |
  awk -F',' -v key="$key" '
    NR == 1 { next }
    $2 == "test_run" && $3 == key {
      mark = ($4 == "passed" ? "✓" : $4 == "failed" ? "✗" : "·")
      title = substr($0, index($0, $7)); gsub(/^"|"$/, "", title)
      printf "- %s **%s** [%s](/task/%s) %s\n", mark, $4, $1, $1, title
      if ($4 == "failed" && $6 != "") printf "  - %s\n", $6
      seen++
    }
    END { if (!seen) printf "" }'
