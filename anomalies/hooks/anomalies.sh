#!/bin/sh
# What docket finds odd in the shape of the vault, as a table with links: a key
# nobody can click is a key somebody has to copy and paste.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Worth a look\n\n'
printf 'From the graph rather than the board: what is adrift, what only one\n'
printf 'person can touch, which label has stopped meaning anything, and where two\n'
printf 'tasks disagree about their own relationship.\n\n'

"$docket" anomalies --json "$DOCKET_ROOT" | awk '
  /"Kind":/  { kind = value($0) }
  /"About":/ { about = value($0) }
  /"Says":/  { says = value($0) }
  /"Why":/   {
    why = value($0)
    if (kind != seen) { printf "\n### %s\n\n", kind; seen = kind }
    # A key looks like PROJECT-123; anything else is a label or a note name.
    if (about ~ /^[A-Za-zА-Яа-я0-9_]+-[0-9]+$/)
      printf "- [**%s**](/task/%s) — %s _(%s)_\n", about, about, says, why
    else
      printf "- **%s** — %s _(%s)_\n", about, says, why
  }
  function value(line) {
    sub(/^[^:]*: *"/, "", line); sub(/",?$/, "", line); return line
  }'

printf '\nNone of these is a fault. A task nobody links to may be the most\n'
printf 'important thing in the project — the tool can only say that it is\n'
printf 'unusual and why it noticed.\n'
