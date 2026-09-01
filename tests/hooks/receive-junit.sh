#!/bin/sh
# Results arriving from outside: a CI job posts its JUnit and the board has an
# execution before the pipeline finishes.
#
#   curl -X POST --data-binary @junit.xml \
#        -H "X-Docket-Secret: $DOCKET_JUNIT_SECRET" \
#        -H "X-Docket-Environment: staging" \
#        -H "X-Docket-Revision: $(git rev-parse --short HEAD)" \
#        https://board.example.com/in/junit
#
# This is the second way in, and the fussier one. The first is a commit: CI has
# a clone, the notes are files, and `hooks/import-junit.sh results.xml --commit`
# followed by a push delivers the whole thing with no endpoint and no secret to
# rotate. Use this when CI must not have push rights to the board.
#
# The body arrives on stdin. Nothing about it is trusted beyond being XML: it is
# written to a file and handed to the same importer a person runs by hand, so
# there is one way results become runs rather than two that drift apart.
set -eu
root="${DOCKET_ROOT:-$(pwd)}"
cd "$root"

file=$(mktemp); trap 'rm -f "$file"' EXIT
cat > "$file"

if [ ! -s "$file" ]; then
  echo "nothing was posted" >&2
  exit 1
fi

hooks/import-junit.sh "$file" \
  --environment "${DOCKET_ENVIRONMENT:-posted}" \
  --revision "${DOCKET_REVISION:-unsaid}"
