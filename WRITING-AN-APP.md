# Writing an app

An app is a git repository with a file called `docket-app.yaml` in it. That is
the whole of the contract. There is no SDK, no registration, and nothing to
publish: somebody installs yours by pasting its URL.

```
docket app add https://git.example.com/you/your-app.git
docket app add https://github.com/vadymdidenkolab/docket-apps.git#risks   # one of many
```

## The manifest

```yaml
name: coverage            # letters, digits, underscores — how the vault records it
version: "1"              # yours to number; shown when installed
description: One line saying what somebody gets

vocabulary:               # everything here is merged into docket.yaml
  types:
    - name: test
    - name: test_plan
      level: 1            # a container: above the level below it
  fields:
    - name: steps
      label: Steps
      kind: text          # text | number | date | datetime | choice | flag | link
      types: [test]       # which kinds of work carry it; omit for all
      choices: [a, b]     # for kind: choice
      required: true
      help: Shown beside the field
  relations:
    - name: tests         # a verb between two tasks
      inverse: tested_by  # written once; the other direction is made for you

surfaces:                 # optional, and the part that brings code
  pages:
    - name: coverage      # /app/coverage
      title: Coverage
      run: hooks/coverage.sh
  panels:
    - name: covered       # a block on every task page
      title: Covered by
      run: hooks/covered.sh
```

## Files it may carry

`templates/`, `boards/`, `docs/`, `hooks/`. Nothing else, and only regular
files — a symlink is a path out of the pack, and `templates/x -> ../../.git/hooks/pre-commit`
would turn installing an app into running one.

A file that already exists and differs is a conflict: the install is refused
and says which file. Installing the same app twice writes nothing.

## Writing a program

A program is an executable file in `hooks/`. It is run directly, with no shell,
so nothing a person typed into a task can become part of a command line. It is
told what happened on **stdin as JSON**, and prints **Markdown** on stdout.

```sh
#!/bin/sh
set -eu
docket="${DOCKET_BIN:-docket}"      # the tool itself, so you do not parse the vault

printf '## Coverage\n\n'
"$docket" export --format csv --open --fields key,title "$DOCKET_ROOT" | ...
```

Two environment variables are set: `DOCKET_ROOT` (the vault on disk) and
`DOCKET_BIN` (the tool). Ask docket for data rather than reading the files
yourself — it follows renames through the history, it knows the vault's
vocabulary, and it is the part that is tested:

| command | what it gives |
|---|---|
| `docket export --format json` | every task, with its fields |
| `docket export --format csv --fields key,assignee,estimate` | the columns you name, in order |
| `docket report time-in-status --json` | how long work sat in each column |
| `docket anomalies --json` | what is odd about how the work is connected |
| `docket graph` | clusters, hubs, islands |

And one that writes:

```
docket set TEST-5 result=failed runs=TEST-3 evidence="gateway timeout"
```

Everything it sets is held to what the vault declared — a choice must be on the
list, a relation must be a key that exists, a status move must be allowed by the
workflow. That is the reason it exists: a script reaching for `sed` on
frontmatter gets none of that, and breaks the file on the first title with a
colon in it.

Ask for columns **by name**. A task title may hold a comma, and counting
columns from the left is exactly how an app comes to read the wrong one.

Markdown, not HTML: a program that could return HTML could put anything on a
page people trust. Links work — `[IGL-12](/task/IGL-12)` and `[[wikilinks]]`
both resolve. A key that is not a link is a key somebody has to copy out.

## What an app may not do

- **Add a status or a workflow.** A column is what a team agreed to. An app
  that added one would change how work moves because somebody wanted a report.
- **Run on installation.** Installing writes files. Running them is a separate
  decision, made on the machine that would run them: a server executes nothing
  unless it was started with `--programs`.
- **Redefine what a vault already means.** A field the vault has as a number, a
  relation with a different inverse, a page that is already drawn by something
  else — each is refused by name, and nothing is written.

## Reactions

An app can also ask to be run when something happens, by declaring it in the
vault (this is not in the manifest yet — write it into `docket.yaml`):

```yaml
reactions:
  - on: task.moved       # task.moved | task.created | task.edited
    status: Done         # optional: only this destination
    run: hooks/on-done.sh
    name: the-release-note
```

The program is told the event on stdin, writes files, and what it wrote is
committed as its own commit. Files that were already uncommitted are left
alone — they are somebody's unfinished edit.

## Testing yours

```
docket app add ../your-app --dry-run     # says exactly what it would change
docket app add ../your-app               # installs; look at the diff
docket check                             # the vault must still be valid
docket serve --programs                  # and then open the page
```
