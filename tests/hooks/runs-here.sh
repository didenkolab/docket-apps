#!/bin/sh
# On an execution: the failures in full, the passes as a number. See runs-here.py.
set -eu
exec python3 hooks/runs-here.py
