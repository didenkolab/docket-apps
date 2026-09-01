---
type: test_execution
environment: staging
revision: 
started: 
finished: 
---

# What was run, where

An execution is one pass over a set of tests, on one build, in one environment.
Its runs are its children: a note per test, each with its own result.

Two notes rather than a status on the test, because a test carrying only its
last result cannot answer "did this ever pass on staging" — which is the
question a release asks.

## What was not run, and why

The part nobody writes down, and the part that matters when somebody asks
whether this build was tested.
