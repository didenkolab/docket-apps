---
type: test
automated: false
---

## Preconditions

What has to be true before this can be run. One line each.

## Scenario

```gherkin
Given a merchant with a verified account
  And a balance of 100.00 EUR
When they request a withdrawal of 40.00 EUR
Then the withdrawal is created with status pending
  And the available balance is 60.00 EUR
```

Written as Gherkin because it is the one format both a person and a runner can
read: Cucumber, Behave and SpecFlow all take it, and `docket` collects every
block like this into one feature file. Keep one scenario per test — a test that
checks two things fails for two reasons and tells you neither.

## What it covers

Link the work with `tests:` — the requirement then shows this test in its
backlinks, and the coverage page counts it.
