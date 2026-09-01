#!/bin/sh
# Bring a Cucumber project's scenarios in as tests.
#
#   hooks/import-features.sh ../acme-aqa/features [@smoke] [--project=ACME] [--dry-run]
#
# The project matters: an execution and its runs belong to one project, and a
# board with ten of them has ten sets of tests. One automation repository is
# normally one project, so it is said here rather than guessed.
#
# One task per scenario, identified by its case id tag. Run it again after the
# automation grows and only the new scenarios arrive.
set -eu
docket="${DOCKET_BIN:-docket}"
[ $# -ge 1 ] || { echo "say where the features are" >&2; exit 2; }
python3 "$(dirname "$0")/import-features.py" "$@"
