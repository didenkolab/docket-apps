# docket apps

A library of packs for a [docket](https://github.com/vadymdidenkolab/docket) vault: vocabulary
and files a vault takes on, arriving as a diff you read before you commit it.

Each folder here is one app — a manifest, and the files it brings. Twelve of them cover most of
what the Jira marketplace sells for a tracker: test management, worklogs, a risk register, OKRs,
time in status. Installing one is a URL and a `git diff`; there is nothing to register with and
nobody to ask.

## Quick start

From inside a vault:

```bash
docket app add https://github.com/vadymdidenkolab/docket-apps.git#tests
git status                                    # everything it wrote, unstaged
docket check
git add -A && git commit -m "Installed the app tests"
```

`docket.yaml` has grown the app's types, fields and relations, and `templates/`, `boards/`,
`docs/` and `hooks/` have its files. Nothing ran, and nothing was committed for you: read the
diff, then keep it or throw it away with `git checkout`.

## Requirements

| | |
|---|---|
| `docket` on the `PATH` | The tool does the installing. See [docket](https://github.com/vadymdidenkolab/docket) |
| git | Required. An app is a git repository, and what it wrote is reviewed and reverted as a diff |
| Python 3.11 or newer, and `sh` | Only for the apps that bring programs, and for the hooks below |
| Obsidian | Optional. A pack's boards and templates are files either way |
| Docker | Not needed for anything here |

## Install

One app out of this library, named after a `#`:

```bash
docket app add https://github.com/vadymdidenkolab/docket-apps.git#tests
docket app add https://github.com/vadymdidenkolab/docket-apps.git#time
```

A library of them is one repository, because six apps in six repositories is six things to
clone, six histories to follow and six places for the same fix.

The same form takes a path instead of a URL, which is how you install one you are editing:

```bash
git clone https://github.com/vadymdidenkolab/docket-apps.git
docket app add ./docket-apps#risks
```

`docket app list` says what a vault has taken on. The whole string is what it records, so
installing again from the same place finds the same app.

A conflict is refused rather than merged: a field the vault already has as another kind, a
relation with a different inverse, a file somebody has edited — all of them are named, and
nothing is written. Installing the same app twice writes nothing.

## Usage

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

### What `--programs` means

The ones that draw something run a program, and a program is run only by a server started with
`--programs`. They ask **docket itself** for the data — `docket export --format csv --fields …`,
`docket report time-in-status`, `docket anomalies` — so the awkward reading stays in one tested
place and an app is a few lines of formatting.

`--programs` is a flag on `docket serve`, off unless it is said. A repository can declare a
program, and only whoever starts the server can agree to execute it on this machine — cloning a
vault should never be the same act as running its code. Without the flag the vocabulary, the
templates and the boards still work; the pages and panels an app draws are simply not there.

| app | what a server with `--programs` draws |
|---|---|
| `tests` | pages Test coverage, Executions and Feature file; panels Runs in this execution, Tested by and Last runs; the action Run the scenarios; and a `junit` inbox a CI job can post to |
| `checklists` | the panel Acceptance on a task, and the page Acceptance across the board |
| `anomalies` | the page Anomalies |
| `estimation` | the page Not sized |
| `portfolio` | the page Portfolio |
| `time-in-status` | the page Time in status |
| `workload` | the page Workload |

`incidents`, `intake`, `okr`, `risks` and `time` bring no program at all.

### The hooks a person runs by hand

The `tests` app also brings importers, which are run by you or by CI and never by the server —
they write tasks, and what writes tasks should be something somebody started on purpose. Run
them from the vault root, after the app is installed:

| Hook | What it does, and how it is called |
|---|---|
| `hooks/import-features.sh` | Brings a Cucumber project's scenarios in as tests — one task per case id.<br>`hooks/import-features.sh ../acme-aqa/features [@smoke] [--project=ACME] [--dry-run] [--ignore-tags=a,b] [--write-tags]` |
| `hooks/import-junit.sh` | Brings a runner's results in: JUnit XML becomes an execution and a run per test, matched by `automation_id`.<br>`hooks/import-junit.sh results.xml --environment staging --revision "$(git rev-parse --short HEAD)"` |
| `hooks/import-cucumber.sh` | Brings a Cucumber JSON report in: one execution, one run per scenario.<br>`hooks/import-cucumber.sh reports/cucumber-123.json --environment staging --revision "$(git -C ../acme-aqa rev-parse --short HEAD)" --commit` |
| `hooks/link-coverage.sh` | Points each imported test at the work it was written for, from the blame and from the text.<br>`hooks/link-coverage.sh <features-dir> --repo <automation repo> [--project KEY] [--limit N] [--dry-run]` |
| `hooks/import-docs.sh` | Brings the automation repository's documentation in as pages, with the keys it names turned into links.<br>`hooks/import-docs.sh <repo> [--into=docs/automation] [--project=KEY] [--dry-run]` |

`hooks/import-junit.sh --help` prints its own header; the others carry theirs at the top of the
file, and the Python beside each — `import-features.py`, `import-cucumber.py`,
`link-coverage.py`, `import-docs.py` — opens with the long answer. Use `--dry-run` first where
it is offered.

## Configuration

An app is configured by its manifest and by the vault it lands in; there is no state of its own.

| File | Where | What it says |
|---|---|---|
| `docket-app.yaml` | An app's root | Its name, version and description, the vocabulary it merges into `docket.yaml`, and the surfaces it draws |
| `docket.yaml` | The vault's root | What the vault ended up with. Edit it here, not in the app |

docket sets three environment variables for a program it runs: `DOCKET_ROOT` (the vault on disk),
`DOCKET_BIN` (the tool, so a hook asks for data rather than parsing the vault) and `DOCKET_PREFIX`
(where the vault sits in the server's URL space — empty for a repository, set in a workspace —
so a link a hook writes resolves). The hooks here read four of their own:

| Variable | Read by | What |
|---|---|---|
| `DOCKET_JUNIT_SECRET` | `hooks/receive-junit.sh` | The shared secret the `junit` inbox checks, sent as `X-Docket-Secret` |
| `DOCKET_AUTHOR_NAME`, `DOCKET_AUTHOR_EMAIL` | the importers, with `--commit` | Who the hook's own commit is attributed to. Defaults to `CI <ci@example.com>` |
| `DOCKET_ENVIRONMENT`, `DOCKET_REVISION` | `hooks/receive-junit.sh`, `hooks/run-tests.sh` | What a posted result says it came from |

## How it works

Nothing here is executed on installation. A pack adds types, fields and relations to
`docket.yaml` and copies templates, saved views and documents in — and the whole of it arrives as
a diff you read before you commit it.

### What a pack may not do

- **No statuses and no workflow.** A column is what a team agreed to. An app
  that added one would change how work moves through a project because
  somebody wanted a report.
- **Files in four folders only** — `templates/`, `boards/`, `docs/`, `hooks/` — and only
  regular files. A symlink is a path out of the pack.
- **Nothing runs.** Automation is a separate mechanism with a separate consent:
  a program is declared in the vault and run only by a server started with
  `--programs`.

### Writing your own

Anyone can. An app is a git repository with a `docket-app.yaml` in it, and it
is installed by pasting the URL — see [WRITING-AN-APP.md](WRITING-AN-APP.md).
There is nothing to register with and nobody to ask.

## Where things are

Each app is a folder: `docket-app.yaml`, and `templates/`, `boards/`, `docs/`, `hooks/` as it
needs them. [WRITING-AN-APP.md](WRITING-AN-APP.md) is the whole contract, and `tests/hooks/` is
the worked example — the largest app, with its own unit tests.

| Repository | What |
|---|---|
| [`docket`](https://github.com/vadymdidenkolab/docket) | The tool: the CLI, the server and the MCP endpoint, as one Go binary |
| [`docket-apps`](https://github.com/vadymdidenkolab/docket-apps) | This one |
| [`docket-board`](https://github.com/vadymdidenkolab/docket-board) | The format's specification, the decisions and the roadmap — and the project's own board |
| [`docket-template`](https://github.com/vadymdidenkolab/docket-template) | What a new vault starts as. `docket init` clones it |
| [`docket-demo`](https://github.com/vadymdidenkolab/docket-demo) | A small vault to open and look at: two projects, seven tasks and a page |
| `docket-showcase` | An invented company's vault: three products, six people, twelve weeks, and every app here installed — built by a generator |
| [`northlight`](https://github.com/vadymdidenkolab/northlight) | That invented company's code, beside its vault |

Only `docket-template` is public today; the rest need access.

## Contributing

The Python that the `tests` hooks share has unit tests:

```bash
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
```

Beyond that, an app is checked by installing it: `docket app add ./docket-apps#yours` into a
scratch vault, then `docket check` and read the diff. A pack that installs cleanly and leaves a
vault `docket check` is happy with is a pack that works.

Bugs and requests go on the board in `docket-board`, where a task is a Markdown file — so a
change to the plan is a pull request, like a change to the code.

## License

MIT — see [LICENSE](LICENSE).
