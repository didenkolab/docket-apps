#!/bin/sh
# Draws the report docket already computes. Four apps on the Atlassian
# marketplace sell this one table; here the numbers come out of git log.
set -eu
docket="${DOCKET_BIN:-docket}"

printf '## Where the work sits\n\n'
printf 'Read out of this repository history: every move was a commit.\n\n'
printf '```\n'
"$docket" report time-in-status "$DOCKET_ROOT" 2>&1
printf '```\n\n'
printf 'The median rather than the average — one task abandoned for a year moves\n'
printf 'an average and says nothing true about the column. "Entered" counts\n'
printf 'arrivals rather than tasks, because work comes back.\n'
