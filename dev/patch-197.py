#!/usr/bin/env python3
"""UJournal 1.9.7 - the birthdays arrive together, not one at a time.

FamTM hands over a name and a day for everyone alive in the family, and the journal imports them as
birthday plans. Every imported plan was given an id made from the clock - and a family's list is
saved in a single loop, inside the same millisecond. So every birthday after the first was given
the id the one before it already had, each save replaced the last, and eight birthdays arrived as
one. The next open did the same thing again, so the number never went up.

A new plan now takes an id of its own. Nothing about the exchange changed: the same list is read
from FamTM's read-only provider, the same birthdays come across in rose in the calendar, and the
journal's own are still published back.

Usage: python3 dev/patch-197.py [--check]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "app/src/main/java/app/ujournal/Store.kt"
GRADLE = ROOT / "app/build.gradle.kts"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

STORE_IMPORT_OLD = "import java.time.LocalDate\n"
STORE_IMPORT_NEW = "import java.time.LocalDate\nimport java.util.UUID\n"
UUID_IMPORT = "import java.util.UUID"

STORE_ID_OLD = """        val id = if (ID.matches(p.id)) p.id else "p" + System.currentTimeMillis().toString(36)
"""

STORE_ID_NEW = """        // A new plan needs an id no other plan has. The clock was not enough: a family's birthdays
        // are imported one after another inside the same millisecond, so every one of them was given
        // the id the one before it had, and each save replaced the last - eight birthdays arrived as
        // one, every time. A random id has no such order to collide on.
        val id = if (ID.matches(p.id)) p.id
        else "p" + UUID.randomUUID().toString().replace("-", "")
"""

GRADLE_OLD = 'versionName = "1.9.6"'
GRADLE_NEW = 'versionName = "1.9.7"'

PAGE_VERSION_OLD = 'const JOURNAL_PAGE = "1.9.6";'
PAGE_VERSION_NEW = 'const JOURNAL_PAGE = "1.9.7";'

WN_OLD = "  var WN = {"

WN_NEW = '''  var WN = {
    "1.9.7": {
      date: "6 November 2026",
      title: "The birthdays arrive together",
      notes: [
        "The birthdays from FamTM now arrive as the whole list. Each one is saved with an id of its own, so eight people's birthdays are eight birthdays - they used to be given the same id inside the same moment, and each one overwrote the one before it, so a family's list arrived as a single birthday.",
        "Every one of them is a birthday plan on its month and day in every year, drawn in rose in the calendar beside the tan of a day with an entry, and still shared back to FamTM the same way."
      ]
    },'''.replace("    },", "    },")

NOTES_OLD = "## 1.9.6 \u2014 November 6, 2026"

NOTES_NEW = """## 1.9.7 \u2014 November 6, 2026

**The birthdays arrive together**

### Fixed
- **A family's birthdays arrived as one.** Importing from FamTM gave each birthday an id made from
  the clock, and the whole list is saved in one loop inside the same millisecond: every birthday
  after the first was given an id the one before it already had, so each save replaced the last.
  Eight birthdays in FamTM arrived as one, and the next open did exactly the same again. A new plan
  now takes an id no other plan has, so the list arrives whole.
- **They are drawn in the calendar.** Every imported birthday is a birthday plan on its month and
  day in every year, in rose beside the tan of a day with an entry.

### Unchanged
- Still on the phone only: FamTM's living family, a name and a day each, read through its read-only
  provider, with this journal's own birthdays published back the same way.


## 1.9.6 \u2014 November 6, 2026"""


def apply(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new, done in pairs:
        if done in text:
            continue  # this edit is already in place
        if old not in text:
            raise SystemExit("patch-197: %s: no such text to replace:\n  %r" % (path.name, old[:100]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def verify():
    problems = []
    store = STORE.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    gradle = GRADLE.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    if store.count("import java.util.UUID") != 1:
        problems.append("Store.kt imports java.util.UUID %d times, not once" % store.count("import java.util.UUID"))
    if 'UUID.randomUUID().toString().replace("-", "")' not in store:
        problems.append("Store.kt still builds a new plan id from the clock")
    if '"p" + System.currentTimeMillis()' in store:
        problems.append("Store.kt still stamps a plan id from the clock")
    if 'versionName = "1.9.7"' not in gradle:
        problems.append("versionName is not 1.9.7")
    if 'const JOURNAL_PAGE = "1.9.7";' not in page:
        problems.append("the page does not name 1.9.7")
    if '"1.9.7": {' not in page:
        problems.append("the page has no 1.9.7 notes")
    if "## 1.9.7" not in notes:
        problems.append("PATCH_NOTES has no 1.9.7 entry")
    if problems:
        raise SystemExit("patch-197: " + "; ".join(problems))
    print("1.9.7: a new plan gets an id of its own, so a family's birthdays arrive together")


if __name__ == "__main__":
    if "--check" in sys.argv:
        verify()
    else:
        for path, pairs in (
            (STORE, ((STORE_IMPORT_OLD, STORE_IMPORT_NEW, UUID_IMPORT),
                     (STORE_ID_OLD, STORE_ID_NEW, 'UUID.randomUUID()'))),
            (GRADLE, ((GRADLE_OLD, GRADLE_NEW, GRADLE_NEW),)),
            (PAGE, ((PAGE_VERSION_OLD, PAGE_VERSION_NEW, PAGE_VERSION_NEW),
                    (WN_OLD, WN_NEW, '"1.9.7": {'))),
            (NOTES, ((NOTES_OLD, NOTES_NEW, "## 1.9.7"),)),
        ):
            apply(path, pairs)
        verify()
