#!/bin/sh
# Point each imported test at the work it was written for. See link-coverage.py.
set -eu
exec python3 hooks/link-coverage.py "$@"
