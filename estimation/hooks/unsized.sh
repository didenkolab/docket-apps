#!/bin/sh
# The agenda for a planning session: open work nobody has put a number on.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Not sized\n\n'
printf 'Open work nobody has put a number on — the agenda for a planning session.\n\n'
"$docket" export --format csv --open --fields estimate,key,title "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 && $1 == "" {
    key = $2
    title = substr($0, index($0, $2) + length($2) + 1)
    gsub(/^"|"$/, "", title)
    printf "- **%s** %s\n", key, title
    left++
  }
  END { if (!left) printf "Everything open has a number on it.\n" }'
