"""What an importer writes over, and what it leaves alone."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body

TEMPLATE = """---
key: ACME-7
title: Berth booking
type: test
automated: false
---

## Preconditions

What has to be true before this can be run. One line each.

## Scenario

```gherkin
Given a merchant with a verified account
When they request a withdrawal of 40.00 EUR
Then the withdrawal is created with status pending
```

Written as Gherkin because it is the one format both a person and a runner can
read.

## What it covers

Link the work with `tests:`.
"""

SAID = ["## Scenario", "", "```gherkin", "  Given a berth", "```", "",
        "From `Berth booking` in `booking.feature`."]


def written(text):
    with tempfile.TemporaryDirectory() as where:
        path = os.path.join(where, "task.md")
        open(path, "w", encoding="utf-8").write(text)
        kept = body.replace(path, SAID)
        return open(path, encoding="utf-8").read(), kept


class WhatTheImporterWritesOver(unittest.TestCase):
    def test_the_templates_instructions_do_not_survive(self):
        """The template's example is for a person, and it is not this test.

        Sixty imported tests opened with a worked example about a payment
        merchant that had nothing to do with the product under test, because
        the importer appended after the template instead of replacing it.
        """
        out, kept = written(TEMPLATE)
        self.assertTrue(kept)
        self.assertNotIn("merchant", out)
        self.assertNotIn("What it covers", out)
        self.assertNotIn("Preconditions", out)

    def test_the_frontmatter_is_untouched(self):
        """It is the task's identity and every property `docket set` wrote."""
        out, _ = written(TEMPLATE)
        self.assertTrue(out.startswith("---\nkey: ACME-7\n"))
        for line in ("title: Berth booking", "type: test", "automated: false"):
            self.assertIn(line, out.split("---")[1])

    def test_the_scenario_is_what_is_left(self):
        out, _ = written(TEMPLATE)
        self.assertIn("Given a berth", out)
        self.assertIn("From `Berth booking` in `booking.feature`.", out)
        self.assertEqual(out.count("## Scenario"), 1)

    def test_a_conversation_survives(self):
        """The one half of a body a person wrote, and this runs again."""
        out, _ = written(TEMPLATE + "\n## Comments\n\n**mateo · 2026-07-03 11:20** — flaky.\n")
        self.assertIn("## Comments", out)
        self.assertIn("**mateo · 2026-07-03 11:20** — flaky.", out)
        self.assertNotIn("merchant", out)
        self.assertLess(out.index("Given a berth"), out.index("## Comments"))

    def test_running_it_twice_says_the_same_thing(self):
        once, _ = written(TEMPLATE)
        twice, _ = written(once)
        self.assertEqual(once, twice)

    def test_a_file_with_no_frontmatter_is_appended_to(self):
        """No frontmatter is no boundary between what the tool owns and what
        it does not, so nothing is thrown away."""
        out, kept = written("Somebody's notes.\n")
        self.assertFalse(kept)
        self.assertIn("Somebody's notes.", out)
        self.assertIn("Given a berth", out)


if __name__ == "__main__":
    unittest.main()
