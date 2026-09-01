#!/bin/sh
# Draws what docket finds odd in the shape of the vault.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Worth a look\n\n'
printf 'From the graph rather than the board: what is adrift, what only one\n'
printf 'person can touch, which label has stopped meaning anything, and where two\n'
printf 'tasks disagree about their own relationship.\n\n'
printf '```\n'
"$docket" anomalies "$DOCKET_ROOT" 2>&1
printf '```\n\n'
printf 'None of these is a fault. A task nobody links to may be the most\n'
printf 'important thing in the project — the tool can only say that it is\n'
printf 'unusual and why it noticed.\n'
