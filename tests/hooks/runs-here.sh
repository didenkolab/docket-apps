#!/bin/sh
# On an execution: what failed, first and in full; what passed, as a number.
#
# A list of four hundred ticks with fourteen crosses in it is a list nobody
# reads to the end — and the fourteen are the entire reason anybody opened the
# page. So the failures come first, with the test's own title and the assertion
# that broke, and the passes are counted rather than enumerated.
set -eu
docket="${DOCKET_BIN:-docket}"
key=$(cat | sed -n 's/.*"key":"\([^"]*\)".*/\1/p')
[ -n "$key" ] || exit 0

runs=$(mktemp); tests=$(mktemp)
trap 'rm -f "$runs" "$tests"' EXIT
"$docket" export --format csv --fields key,type,parent,result,runs,evidence,title "$DOCKET_ROOT" > "$runs"
"$docket" export --format csv --fields key,title,automation_id "$DOCKET_ROOT" > "$tests"

awk -F',' -v key="$key" '
  NR == FNR {
    if (FNR > 1) { title[$1] = $2; ident[$1] = $3 }
    next
  }
  FNR == 1 { next }
  $2 == "test_run" && $3 == key {
    covers = $5
    name = (covers in title) ? title[covers] : $7
    gsub(/^"|"$/, "", name)
    id = (covers in ident) ? ident[covers] : ""
    if ($4 == "failed") {
      failed = failed sprintf("- ✗ [**%s**](/task/%s) %s\n", (id ? id : covers), covers, name)
      if ($6 != "") { why = $6; gsub(/^"|"$/, "", why); failed = failed "  - " why "\n" }
      nfail++
    } else if ($4 == "passed") npass++
    else nother++
  }
  END {
    if (nfail) printf "**%d failed**\n\n%s\n", nfail, failed
    if (npass) printf "%d passed.", npass
    if (nother) printf " %d neither.", nother
    if (npass || nother) printf "\n"
  }' "$tests" "$runs"
