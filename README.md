# docket apps

A library of packs. Each folder is one app: a manifest, and the files it brings.

```
docket app add https://github.com/vadymdidenkolab/docket-apps.git#tests
```

Nothing here is executed on installation. A pack adds types, fields and
relations to `docket.yaml` and copies templates, saved views and documents in —
and the whole of it arrives as a diff you read before you commit it.

| app | what it is, and what it replaces |
|---|---|
| `tests` | test plans, tests and runs, and the verb that says what a test covers — Xray, Zephyr, AIO, QMetry (13 of the top 100) |
| `time` | hours as worklog notes rather than a number on a card — Tempo and the ten others |
| `risks` | a register: likelihood, impact, and what each risk threatens — Risk Register |
| `okr` | objectives, key results and what contributes to them — OKR for Jira |
| `incidents` | incidents and the postmortem that has to follow, as two tasks |
| `intake` | requests from outside the team, kept apart from the work they became |
| `time-in-status` | how long work sits in each column — Time in Status, Timepiece, Status Time Reports (4 apps) |
| `anomalies` | what is odd about how the work is connected — nothing in the marketplace does this |
| `workload` | who is carrying what and how much — the capacity reports |
| `checklists` | progress through the acceptance list, on the task and across the board (3 apps) |
| `estimation` | what has not been sized, so a planning session has an agenda — Planning Poker, Agile Poker |
| `portfolio` | containers and how much of what is under them is done — Structure, BigPicture (8 apps) |

The ones that draw something run a program, and a program is run only by a
server started with `--programs`. They ask **docket itself** for the data —
`docket export --format csv --fields …`, `docket report time-in-status`,
`docket anomalies` — so the awkward reading stays in one tested place and an app
is a few lines of formatting.

## Writing your own

Anyone can. An app is a git repository with an `docket-app.yaml` in it, and it
is installed by pasting the URL — see [WRITING-AN-APP.md](WRITING-AN-APP.md).
There is nothing to register with and nobody to ask.

## What a pack may not do

- **No statuses and no workflow.** A column is what a team agreed to. An app
  that added one would change how work moves through a project because
  somebody wanted a report.
- **Files in three folders only** — `templates/`, `boards/`, `docs/` — and only
  regular files. A symlink is a path out of the pack.
- **Nothing runs.** Automation is a separate mechanism with a separate consent:
  a program is declared in the vault and run only by a server started with
  `--reactions`.
