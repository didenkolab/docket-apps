---
title: How incidents are kept
type: page
---

An incident is a task. It says how bad it was and when it was detected and
resolved; a postmortem is a separate task pointing at it with `explains:`.

## Two tasks, not one

Because they close at different times and for different reasons. The incident
is over when the system is well; the postmortem is done when the changes are
decided. Kept as one, the second half is always closed early — the pressure is
off, and nobody reopens a Done card.

## Severity is not a feeling

sev1 is money or data moving wrongly. sev2 is a promise broken to a customer who
can tell. sev3 is somebody inconvenienced. If two people disagree about which
one it is, that disagreement is worth more than the label.
