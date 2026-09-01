#!/bin/sh
# Bring a Cucumber JSON report in: one execution, one run per scenario.
#
#   hooks/import-cucumber.sh reports/cucumber-123.json --environment staging \
#       --revision "$(git -C ../acme-aqa rev-parse --short HEAD)" --commit
set -eu
docket="${DOCKET_BIN:-docket}"
root="${DOCKET_ROOT:-$(pwd)}"

file=""; environment="unsaid"; revision=""; commit=""; project=""
while [ $# -gt 0 ]; do
  case "$1" in
    --environment) environment="$2"; shift 2 ;;
    --revision)    revision="$2";    shift 2 ;;
    --commit)      commit=1;         shift 1 ;;
    --project)     project="$2";     shift 2 ;;
    *)             file="$1";        shift 1 ;;
  esac
done
[ -n "$file" ] && [ -f "$file" ] || { echo "say which report" >&2; exit 2; }

python3 "$(dirname "$0")/import-cucumber.py" "$file" "$environment" "$revision" "$project"
python3 "$(dirname "$0")/charts.py" attachments/test-results.svg || true

if [ -n "$commit" ]; then
  cd "$root"
  git add -A
  git -c user.name="${DOCKET_AUTHOR_NAME:-CI}" -c user.email="${DOCKET_AUTHOR_EMAIL:-ci@example.com}" \
      commit -q -m "Cucumber results from ${environment}${revision:+ at $revision}" || true
  echo "committed."
fi
