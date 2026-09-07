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
    # Only a test declares coverage: `tests:` on a test points at the work.
    # A run carries `runs:` and no coverage at all, and counting one as a test
    # reported every run in the vault as "a test covering nothing" — 265 of
    # them in a showcase with 60 tests.
    if ($1 != "test") next
    split($2, keys, " ")
    for (i in keys) if (keys[i] != "") covered[keys[i]] = 1
    tests++
    if ($2 == "") loose++
    next
  }
  FNR == 1 { next }
  {
    type = $2
    # Nothing the tests app writes is work waiting to be covered, and each is
    # skipped for its own reason:
    #   test           is the coverage — it is what covers, not what is covered
    #   test_run       is one result of one test, written per scenario per run
    #   test_plan      names the areas to cover; it holds sets, not requirements
    #   test_set       is a grouping of tests, not work somebody asked for
    #   test_execution is one pass of the suite on one build, not a deliverable
    if (type == "test" || type == "test_run" || type == "test_plan" ||
        type == "test_set" || type == "test_execution") next
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
    printf "| Tests | %d |\n", tests + 0
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
