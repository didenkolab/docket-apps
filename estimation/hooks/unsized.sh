#!/bin/sh
# The agenda for a planning session: open work nobody has put a number on.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Not sized\n\n'
printf 'Open work nobody has put a number on — the agenda for a planning session.\n\n'
"$docket" export --format csv --open --fields estimate,board,key,title "$DOCKET_ROOT" |
  awk -F',' 'NR > 1 && $1 == "" {
    # `board: false` in docket.yaml says a type is a record of something rather
    # than work somebody does — a test, a run, an execution. A machine writes
    # them and nobody sizes them, so counting them would bury the planning
    # agenda under thousands of rows no planning session is ever about.
    if ($2 == "false") next
    key = $3
    title = substr($0, index($0, $3) + length($3) + 1)
    gsub(/^"|"$/, "", title)
    # A key that is not a link is a key somebody has to copy and paste.
    printf "- [**%s**](/task/%s) %s\n", key, key, title
    left++
  }
  END { if (!left) printf "Everything open has a number on it.\n" }'
