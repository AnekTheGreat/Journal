#!/usr/bin/env python3
"""UJournal 1.9.2 - the journal asks Android for FamTM's list.

The birthdays never arrived because Android 11 and later hide one app from another unless the
first names it in <queries>. UJournal never named FamTM, so its query to
content://com.FamTM.app.birthdays/list was refused and the card in Plans said "FamTM is not
installed" with FamTM sitting on the same phone. This declares FamTM - the package, so it can be
found, and the one provider that is read - and carries the version to 1.9.2 so the release reaches
an installed copy.

Usage: python3 dev/patch-192.py [--check]
  --check  exit 0 when everything is already at 1.9.2, 1 when there is work to do, 2 on an error
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
GRADLE = ROOT / "app/build.gradle.kts"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

QUERIES = '''
    <!-- Android 11 and later hide one app from another unless the first asks for it by name, and a
         hidden app cannot be reached at all - not its package, not its provider. UJournal asked
         FamTM for the birthdays and was told FamTM was not installed, with FamTM sitting on the
         same phone. These lines are the asking: the package, so it can be found, and the one
         provider of FamTM's that is read. Nothing else of FamTM's is reachable. -->
    <queries>
        <package android:name="com.FamTM.app" />
        <provider android:authorities="com.FamTM.app.birthdays" />
    </queries>
'''

WN = '''    "1.9.2": {
      date: "6 November 2026",
      title: "The birthdays arrive now",
      notes: [
        "Sync birthdays works. Android hides one app from another unless the app asks for it by name, and the journal never asked: it asked FamTM for its list, was refused, and said FamTM was not installed while FamTM sat on the same phone. It names FamTM now - the app and the one list it reads - so the same button brings the birthdays across.",
        "What comes across is unchanged: a name and a day, added to Plans as birthday plans that come round every year. What is typed here is still published back for FamTM to read.",
        "This one lives in the app rather than only in the screen, so it arrives as an update. The screen came with it."
      ]
    },
'''

NOTE = '''## 1.9.2 — November 6, 2026

**The birthdays arrive: the journal now asks Android for FamTM's list**

### Fixed
- **Sync birthdays did nothing on a phone that has FamTM.** Android 11 and later hide one app from
  another unless the first names it, and UJournal never named FamTM: the query to
  content://com.FamTM.app.birthdays/list was refused and the card in Plans said FamTM was not
  installed. The app now declares FamTM - the package and the one provider it reads - so the same
  tap brings the birthdays across.
- **A screen written before this one still works.** The page only changes its own notes and its
  version; the import, the plans and the calendar are untouched by it.

### Unchanged
- The provider here still publishes this journal's birthdays back to FamTM, names and days only, and
  the plan durations and the tip heart are exactly as they were in 1.9.1.


'''


def edit(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch-192: %s: no such text to replace:\n  %r" % (path.name, old[:80]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    page = PAGE.read_text(encoding="utf-8")
    done = (
        '<provider android:authorities="com.FamTM.app.birthdays" />' in MANIFEST.read_text(encoding="utf-8")
        and 'versionName = "1.9.2"' in GRADLE.read_text(encoding="utf-8")
        and 'const JOURNAL_PAGE = "1.9.2";' in page
        and '"1.9.2": {' in page
        and "## 1.9.2 — November 6, 2026" in NOTES.read_text(encoding="utf-8")
    )
    if check:
        print("1.9.2 already applied" if done else "1.9.2 not applied yet")
        return 0 if done else 1
    if done:
        print("1.9.2 already applied - nothing to do")
        return 0

    # 1. The asking. <queries> is a child of <manifest>, beside the permissions and before <application>.
    edit(MANIFEST, [(
        '    <uses-permission android:name="android.permission.RECORD_AUDIO" />\n',
        '    <uses-permission android:name="android.permission.RECORD_AUDIO" />\n' + QUERIES,
    )])

    # 2. The version, which is what an installed copy compares against.
    edit(GRADLE, [('versionName = "1.9.1"', 'versionName = "1.9.2"')])

    # 3. The screen: its own version, and the note that says what changed.
    edit(PAGE, [
        ('const JOURNAL_PAGE = "1.9.1";', 'const JOURNAL_PAGE = "1.9.2";'),
        ('  var WN = {\n    "1.9.1": {', '  var WN = {\n' + WN + '    "1.9.1": {'),
    ])

    # 4. The notes the release publishes, newest first.
    edit(NOTES, [('## 1.9.1 — November 6, 2026', NOTE + '## 1.9.1 — November 6, 2026')])

    print("1.9.2 applied: FamTM declared, version 1.9.2, screen and notes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
