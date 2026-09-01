# docket apps

A library of packs. Each folder is one app: a manifest, and the files it brings.

```
docket app add https://github.com/vadymdidenkolab/docket-apps.git#tests
```

Nothing here is executed on installation. A pack adds types, fields and
relations to `docket.yaml` and copies templates, saved views and documents in —
and the whole of it arrives as a diff you read before you commit it.

| app | what it adds |
|---|---|
| `tests` | test plans, tests and runs, and the verb that says what a test covers |
| `time` | time logged against work, as notes rather than as a number nobody can audit |
| `risks` | a risk register: likelihood, impact, and what each risk threatens |
| `okr` | objectives and key results, and what contributes to them |
| `incidents` | incidents, severity, and the postmortem that has to follow |
| `intake` | requests from outside the team, and what they became |

## What a pack may not do

- **No statuses and no workflow.** A column is what a team agreed to. An app
  that added one would change how work moves through a project because
  somebody wanted a report.
- **Files in three folders only** — `templates/`, `boards/`, `docs/` — and only
  regular files. A symlink is a path out of the pack.
- **Nothing runs.** Automation is a separate mechanism with a separate consent:
  a program is declared in the vault and run only by a server started with
  `--reactions`.
