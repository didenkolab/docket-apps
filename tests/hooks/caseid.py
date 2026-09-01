"""The identity of a scenario, whether or not anybody gave it one.

A case id tag — `@ACME-ADM-002` — is the right identity: it survives rewording,
and rewording is what happens to a scenario's name. But most suites have
scenarios nobody tagged, and until now those simply did not arrive: they were
counted and skipped, so a fifth of the automation was invisible on the board and
a fifth of every run had nowhere to land.

They do not need a person to name them. An id can be derived from the scenario
itself, as long as both sides derive the same one — the importer that creates
the test and the importer that attaches the result. That is all an identity is:
agreement.

Derived from the feature file's name and the scenario's, and from nothing else.
Not the path, because directories get restructured; not the steps, because a
step gets fixed. What is left is the pair a person would use to point at it.

The honest limit: **rename the scenario and the derived id changes**, so the run
history stays with the old test and a new one starts. A tag in the file has no
such problem, which is why `--write-tags` exists and why what it writes is
sequential and readable rather than this hash. Derivation is the floor, not the
goal.
"""
import hashlib
import os
import re

# A case id somebody wrote. Deliberately strict — a suite has tags like @smoke
# and @wip, and a loose pattern would promote one of those to an identity.
WRITTEN = re.compile(r"^@?(SP|ACME)-[A-Z]+-\d+$")

# One this file derived. A distinct shape on purpose: reading a board, you can
# see at a glance which tests the automation names and which the tool guessed.
DERIVED = re.compile(r"^@?[A-Z]+-GEN-[0-9A-F]{6}$")


def written(tags):
    """The first case id in a scenario's tags, or empty."""
    said = all_written(tags)
    return said[0] if said else ""


def all_written(tags):
    """Every case id in a scenario's tags, in the order written.

    More than one is normal and is not a mistake. A case is a thing that must
    be true; a scenario is one way of making it true. One scenario can settle
    two cases at once — `@ACME-INV-049 @ACME-INV-048` on the paid-invoice walk —
    and two scenarios can each settle the same case from different directions.
    Reading only the first tag turned both of those into a duplicate that was
    not there, and deleted work that was.

    Gherkin also lets the tags sit on several lines before the scenario, with
    comments in between, and they all apply. Whatever collects them has to
    collect all of them.
    """
    out = []
    for tag in tags:
        if WRITTEN.match(tag) and tag.lstrip("@") not in out:
            out.append(tag.lstrip("@"))
    return out


def derived(feature_file, scenario_name, prefix="ACME"):
    """A stable id for a scenario nobody tagged.

    feature_file may be a path or a bare name; only its base name counts, so the
    id survives the day somebody sorts the features into folders.
    """
    base = os.path.basename(str(feature_file or "")).strip().lower()
    if base.endswith(".feature"):
        base = base[: -len(".feature")]
    name = " ".join(str(scenario_name or "").split()).lower()
    seed = base + "\x00" + name
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6].upper()
    return "%s-GEN-%s" % (prefix.upper(), digest)


def identity(tags, feature_file, scenario_name, prefix="ACME"):
    """What to call this scenario, and whether anybody said so.

    Returns (id, told): told is False when the id was derived here, which is
    what the callers report and what a `generated: true` on the test records.
    """
    said = written(tags)
    if said:
        return said, True
    return derived(feature_file, scenario_name, prefix), False


def tags_of(element):
    """Cucumber JSON writes tags as objects; a .feature writes them as words."""
    out = []
    for tag in element.get("tags", []) or []:
        out.append(tag["name"] if isinstance(tag, dict) else str(tag))
    return out
