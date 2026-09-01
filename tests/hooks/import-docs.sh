#!/bin/sh
# Bring the automation repository's documentation in as pages. See import-docs.py.
set -eu
exec python3 hooks/import-docs.py "$@"
