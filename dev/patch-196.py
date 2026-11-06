#!/usr/bin/env python3
"""UJournal 1.9.6 - the other-apps card leaves the journal, and stays in Plans.

The journal's own list ended with the card that offers SideCut, FamTM and the rest. It belongs with
the plans, not under the entries: writing an entry should end with the journal, not with a shelf of
other apps. The card is untouched in Plans, where someone is looking for things to do.

Usage: python3 dev/patch-196.py [--check]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADLE = ROOT / "app/build.gradle.kts"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

EMPTY_OLD = """      v.innerHTML = top + '<div class="empty">This journal is waiting.<br>Tap ＋ to write today.</div>' +
        othersCard();
      return;"""

EMPTY_NEW = """      v.innerHTML = top + '<div class="empty">This journal is waiting.<br>Tap ＋ to write today.</div>';
      return;"""

LIST_OLD = """    v.innerHTML = top + h + othersCard();
  }"""

LIST_NEW = """    // No other-apps card here: the journal's own list ends with the journal. It stays in Plans,
    // under the birthdays and the plans, where it is being looked for.
    v.innerHTML = top + h;
  }"""

WN = '''    "1.9.6": {
      date: "6 November 2026",
      title: "The journal ends with the journal",
      notes: [
        "The card offering the other apps is gone from the journal's list. Writing an entry now ends with the entries, not with a shelf of other apps.",
        "It is still in Plans, under the plans and the birthdays, where someone is looking for what else there is to open."
      ]
    },
'''

NOTE = '''## 1.9.6 — November 6, 2026

**The other-apps card leaves the journal list and stays in Plans**

### Changed
- **No other-apps card under the entries.** The journal's own list drew the card for SideCut, FamTM
  and the rest after the last entry, so every list ended with a shelf of other apps. The list now
  ends with the journal itself.
- **Plans keeps it.** The same card is still at the bottom of Plans, where the plans and the
  birthdays are, so nothing became unreachable.

### Unchanged
- The birthdays still add themselves, the rose colour in the calendar and the provider back to FamTM
  are as they were in 1.9.5.


'''


def edit(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch-196: %s: no such text to replace:\n  %r" % (path.name, old[:90]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    page = PAGE.read_text(encoding="utf-8")
    done = (
        'const JOURNAL_PAGE = "1.9.6";' in page
        and '"1.9.6": {' in page
        and "v.innerHTML = top + h;" in page
        and 'versionName = "1.9.6"' in GRADLE.read_text(encoding="utf-8")
        and "## 1.9.6 — November 6, 2026" in NOTES.read_text(encoding="utf-8")
    )
    if check:
        print("1.9.6 already applied" if done else "1.9.6 not applied yet")
        return 0 if done else 1
    if done:
        print("1.9.6 already applied - nothing to do")
        return 0

    edit(PAGE, [
        ('const JOURNAL_PAGE = "1.9.5";', 'const JOURNAL_PAGE = "1.9.6";'),
        ('  var WN = {\n    "1.9.5": {', '  var WN = {\n' + WN + '    "1.9.5": {'),
        (EMPTY_OLD, EMPTY_NEW),
        (LIST_OLD, LIST_NEW),
    ])
    edit(GRADLE, [('versionName = "1.9.5"', 'versionName = "1.9.6"')])
    edit(NOTES, [('## 1.9.5 — November 6, 2026', NOTE + '## 1.9.5 — November 6, 2026')])

    # The card must still be in Plans, or it would have been removed rather than moved.
    page = PAGE.read_text(encoding="utf-8")
    if '$("view").innerHTML = h + othersCard();' not in page:
        raise SystemExit("patch-196: the card is gone from Plans as well - stopped")
    if "othersCard()" in page.split("function drawList")[1].split("function drawPlans")[0]:
        raise SystemExit("patch-196: the card is still drawn under the entries - stopped")
    print("1.9.6 applied: the list ends with the journal, Plans keeps the card")
    return 0


if __name__ == "__main__":
    sys.exit(main())
