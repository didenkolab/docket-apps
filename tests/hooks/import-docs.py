"""Bring the automation repository's documentation into the vault as pages.

The test plan, the coverage map, the attack matrix, the handover — three
thousand lines that explain why the suite is shaped the way it is. They sit in
a repository most of the team never opens, so they are read the day somebody
is already lost.

Copying them is the small part. What makes them worth having here is that they
join the graph:

  a key a page names — "carried across in ACME-410" — becomes a link, so the
  task shows the document in its backlinks and the document shows in the graph
  beside the work it is about;

  a link between two of these documents keeps working, rewritten from
  `docs/coverage-map.md` to `[[coverage-map]]`, because a relative path out of
  another repository resolves to nothing here.

Nothing is invented: only keys the board actually has become links, and every
page says at the top which repository and which commit it came from. Run it
again after the docs change and it overwrites what it wrote — these are copies,
and a copy that has to be merged by hand is a copy nobody refreshes.

  hooks/import-docs.sh <repo> [--into=docs/automation] [--project=KEY] [--dry-run]
"""
import json
import os
import re
import subprocess
import sys

docket = os.environ.get("DOCKET_BIN", "docket")
root = os.environ.get("DOCKET_ROOT", ".")

repo = sys.argv[1]
rest = sys.argv[2:]
into = next((a.split("=", 1)[1] for a in rest if a.startswith("--into=")), "docs/automation")
project = next((a.split("=", 1)[1] for a in rest if a.startswith("--project=")), "")
dry = "--dry-run" in rest

KEY = re.compile(r"(?<![\w\[-])([A-Z][A-Z0-9]+-\d{1,6})\b(?![\w\]-])")
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)(#[^)]*)?\)")
FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]*`")


def run(*args):
    out = subprocess.run([docket, *args], capture_output=True, text=True, cwd=root)
    if out.returncode != 0:
        sys.exit((out.stderr or out.stdout).strip())
    return out.stdout.strip()


def git(*args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


# What the board has, so a key can become a link to something real. A wikilink
# to a task that does not exist is a dead link, and on a page of four hundred
# mentions it is four hundred of them.
titles = {}
for t in json.loads(run("export", "--format", "json")):
    if project and t.get("project") != project:
        continue
    titles[t["key"]] = t.get("title", "")


def note(path):
    """What a copied document is called in the vault: its file name, no folder.

    Obsidian resolves a wikilink by note name, so two documents with the same
    base name in different folders would collide. None do here, and the check
    below says so rather than assuming it.
    """
    return os.path.splitext(os.path.basename(path))[0]


def sources():
    """Every markdown file the repository tracks, outside the features."""
    out = []
    for line in git("ls-files", "*.md").splitlines():
        if line.startswith("features/") or "/node_modules/" in line:
            continue
        out.append(line)
    return sorted(out)


def linkify(text, mine):
    """Turn keys into wikilinks and cross-document links into wikilinks.

    Code is left alone. A fenced block is usually a request or a payload, and
    an id inside one is a value rather than a reference — linking it would
    rewrite the example into something that no longer runs.
    """
    keep = []

    def hide(m):
        keep.append(m.group(0))
        return "\x00%d\x00" % (len(keep) - 1)

    text = FENCE.sub(hide, text)
    text = INLINE.sub(hide, text)

    def wiki(m):
        label, target = m.group(1), m.group(2)
        name = note(target)
        if name not in mine:
            return m.group(0)  # a document that did not come across
        return "[[%s|%s]]" % (name, label) if label and label != name else "[[%s]]" % name

    text = MD_LINK.sub(wiki, text)

    def task(m):
        key = m.group(1)
        if key not in titles:
            return key
        return "[[%s %s]]" % (key, titles[key]) if titles[key] else "[[%s]]" % key

    text = KEY.sub(task, text)
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], text)


def heading(text, fallback):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").replace("_", " ").capitalize()


found = sources()
if not found:
    sys.exit("no markdown in that repository outside its features")

clashes = {}
for path in found:
    clashes.setdefault(note(path), []).append(path)
for name, paths in clashes.items():
    if len(paths) > 1:
        sys.exit("two documents would be called %s: %s. Obsidian resolves a link "
                 "by note name, so one would shadow the other." % (name, ", ".join(paths)))

mine = set(clashes)
where = git("config", "--get", "remote.origin.url") or os.path.basename(os.path.abspath(repo))
at = git("rev-parse", "--short", "HEAD")
when = git("log", "-1", "--format=%cs")

wrote = 0
for path in found:
    body = open(os.path.join(repo, path), encoding="utf-8").read()
    title = heading(body, note(path))
    page = "---\ntitle: " + title.replace('"', "'") + "\ntype: page\n"
    if when:
        page += "updated: " + when + "\n"
    page += "---\n\n"
    page += ("> Copied from `" + path + "` in " + where +
             (" at `" + at + "`" if at else "") + ". Edit it there: this file is "
             "overwritten the next time the documentation is imported.\n\n")
    page += linkify(body, mine)

    to = os.path.join(root, into, os.path.basename(path))
    if not dry:
        os.makedirs(os.path.dirname(to), exist_ok=True)
        open(to, "w", encoding="utf-8").write(page)
    wrote += 1

print(f"{wrote} documents copied into {into}/ from {where}" +
      (f" at {at}" if at else "") + ".")
print("Keys they name are links now, so each task shows the document in its "
      "backlinks and the graph draws them together.")
if dry:
    print("Nothing was written: --dry-run.")
