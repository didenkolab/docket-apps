"""What a machine-written task says, in place of the template's instructions.

A vault's templates are written for a person filling one in by hand: `test.md`
carries a worked example about a merchant with a verified account and an essay
on why Gherkin. That is right for a person and wrong for an importer — sixty
imported tests all opened with somebody else's scenario, and seven hundred runs
would each carry a copy of a note to a reader who does not exist.

So an importer replaces the body rather than appending to it. The frontmatter is
untouched (it is the task's identity and every property `docket set` wrote), and
a `## Comments` section survives, because the conversation is the one half of a
body a person wrote and an importer runs again every time the suite grows.
"""

# Where a person's words live in a task file.
COMMENTS = "## Comments"


def replace(path, lines):
    """Write `lines` as the task's body, keeping its frontmatter and comments.

    Falls back to appending when the file has no frontmatter to keep: there is
    then no safe boundary between what the tool owns and what it does not.
    """
    whole = open(path, encoding="utf-8").read()
    head = whole.split("---", 2)
    said = "\n".join(lines).rstrip("\n") + "\n"
    if len(head) < 3:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + said)
        return False
    kept = ""
    at = head[2].find(COMMENTS)
    if at >= 0:
        kept = "\n" + head[2][at:].strip() + "\n"
    open(path, "w", encoding="utf-8").write("---" + head[1] + "---\n\n" + said + kept)
    return True
