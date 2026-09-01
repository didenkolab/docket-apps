---
title: How testing works here
type: page
---

A test is a task of type `test`. It says what it covers with `tests:`, which is
a link — so the thing being tested shows the test in its backlinks, and the
graph draws the two together.

A run is a task of type `test_run` with a `result`. It links to the test with
`tests:` as well, so a test's page shows every time it was run.

What this app does not do: decide what "done" means, or add a column. Whether a
release waits for a failing test is a decision, and a decision belongs to the
team rather than to an installer.
