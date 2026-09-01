#!/bin/sh
# What has a test and what does not — read from the tests' own side, because
# the test is what declares coverage: `tests:` points at the work.
set -eu
docket="${DOCKET_BIN:-docket}"
work=$(mktemp); covers=$(mktemp)
trap 'rm -f "$work" "$covers"' EXIT

"$docket" export --format csv --fields key,type,category,title "$DOCKET_ROOT" > "$work"
"$docket" export --format csv --fields type,tests "$DOCKET_ROOT" > "$covers"

printf '## Coverage\n\n'
awk -F',' '
  # The first file is what the tests say they cover; the second is the work.
  # NR == FNR is true only while the first is being read, which is the idiom —
  # matching on FILENAME let every non-test row of the first file fall through
  # into the second block and be counted as work.
  NR == FNR {
    if (FNR == 1) next
    if ($1 != "test" && $1 != "test_run") next
    split($2, keys, " ")
    for (i in keys) if (keys[i] != "") covered[keys[i]] = 1
    tests++
    if ($2 == "") loose++
    next
  }
  FNR == 1 { next }
  {
    type = $2
    if (type == "test" || type == "test_run" || type == "test_plan") next
    if ($3 == "done") next
    open++
    if ($1 in covered) { has++; next }
    title = substr($0, index($0, $4)); gsub(/^"|"$/, "", title)
    if (bare < 25) { list = list "\n- [**" $1 "**](/task/" $1 ") " title; bare++ }
    else rest++
  }
  END {
    printf "| | Tasks |\n|---|---:|\n"
    printf "| Open work with a test | %d |\n", has + 0
    printf "| Open work with none | %d |\n", open - has
    printf "| Tests and runs | %d |\n", tests + 0
    if (loose) printf "| Tests covering nothing | %d |\n", loose
    printf "\n"
    if (open == 0) printf "No open work to cover.\n"
    else if (open == has) printf "Everything open is covered.\n"
    else {
      printf "### Not covered%s\n", list
      if (rest) printf "\nand %d more.\n", rest
    }
  }' "$covers" "$work"

printf '\nCoverage means a link: a test says what it covers with `tests:`, and the\n'
printf 'work shows it in its backlinks. A number without that link is a number\n'
printf 'nobody can follow to the test.\n'
