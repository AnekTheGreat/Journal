#!/usr/bin/env python3
"""UJournal 2.1 - the whole family on the list, and a tap that goes somewhere.

UJournal's Other apps list, and the same list under Settings, held three apps: FamTM, SideCut and
MeasureT. 1.9.10 had taken My Hub off because it had no store page, and UNote had never been on it,
so the journal was the shortest shelf in the family - and My Hub, the screen that launches
everything else, was the app it did not list.

2.1 lists the five apps beside this one - My Hub, FamTM, SideCut, MeasureT and UNote - in both
places, and the shell learns UNote's address so a tap on that row does something. The card, the
sheet, the guide line and the tab summary say the same five names, and the addresses in the shell
are the ones that answer today rather than four Play listings that are not up.

    python3 dev/patch-21.py            # apply
    python3 dev/patch-21.py --check    # verify only, writes nothing
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "app/src/main/assets/index.html"
BRIDGE = "app/src/main/java/app/ujournal/Bridge.kt"
GRADLE = "app/build.gradle.kts"
NOTES = "PATCH_NOTES.md"

V = "2.1"
OLD = "2.0"

LIST_NEW = """var {NAME} = [
    ["myhub", "My Hub", "One screen that launches the rest, and keeps each one up to date"],
    ["famtm", "FamTM", "The family tree in your pocket"],
    ["sidecut", "SideCut", "A music player with its own equaliser"],
    ["measuret", "MeasureT", "Elevation, location, a level and a converter"],
    ["unote", "UNote", "Notes that link themselves, behind a PIN"]
  ];"""

CARD_OLD = "'<div class=\"s2\">FamTM, SideCut and MeasureT.</div></div><div class=\"h\">\u203a</div></div>';"
CARD_NEW = "'<div class=\"s2\">My Hub, FamTM, SideCut, MeasureT and UNote.</div></div><div class=\"h\">\u203a</div></div>';"

SHEET_OLD = "'<h2>Other apps</h2><p>Three more, made the same way and free the same way.</p>'"
SHEET_NEW = "'<h2>Other apps</h2><p>Five more, made the same way and free the same way.</p>'"

GUIDE_OLD = '["Other apps", "FamTM, SideCut and MeasureT - the apps beside this one."]'
GUIDE_NEW = '["Other apps", "My Hub, FamTM, SideCut, MeasureT and UNote - the apps beside this one."]'

BRIDGE_NEW = '''    private val APPS = listOf(
        "journal" to "https://play.google.com/store/apps/details?id=app.ujournal",
        "famtm" to "https://github.com/AnekTheGreat/FamTM/releases/latest",
        "myhub" to "https://github.com/AnekTheGreat/My-Hub/releases/latest",
        "sidecut" to "https://play.google.com/store/apps/details?id=com.SideCut.myapp",
        // The package still carries its original Compass-EDC name; the app itself is MeasureT, and
        // its own page is where it is handed out.
        "measuret" to "https://anekthegreat.github.io/Compass-EDC/",
        // UNote is a page rather than a listing: the row opens it in the phone's browser, which is
        // also where it can be added to the home screen.
        "unote" to "https://anekthegreat.github.io/UNote/"
    )'''

WN_ENTRY = """      "2.1": {
        date: "8 November 2026",
        title: "The whole family on the list",
        notes: [
          "Other apps, and the same list under Settings, now carry all five apps beside this one: My Hub, FamTM, SideCut, MeasureT and UNote. My Hub had been taken off and UNote had never been on, so the journal had the shortest shelf in the family.",
          "The card, the sheet, the Guide's line and the tab summary all say the same five names now, so the shelf reads the same wherever you open it.",
          "Tapping UNote does something: the shell knows its address, which it did not before. The addresses that went to store pages which are not up yet now go to the release each app installs from."
        ]
      },
"""

NOTES_ENTRY = """## 2.1 - 8 November 2026

The whole family on the Other apps list.

- **Five apps, not three.** My Hub, FamTM, SideCut, MeasureT and UNote: the same five the rest of
  the family lists. My Hub had been removed in 1.9.10 for having no store page, and UNote was never
  added.
- **A tap that goes somewhere.** UNote's address was not in the shell, so the row could not open
  anything even if the page had listed it. It is in the shell now, and the row opens UNote's page in
  the phone's own browser. The other addresses open the release each app installs from, because
  only SideCut's Play listing is live.
- **One list, said four ways.** The card, the sheet, the Guide line and the tab summary all name the
  same five apps.

"""


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def write(rel, text):
    with io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def swap_list(page, name):
    new = LIST_NEW.replace("{NAME}", name)
    if new in page:
        return page, False
    head = "var %s = [" % name
    if head not in page:
        sys.exit("the page has no %s list" % name)
    i = page.index(head)
    j = page.index("];", i) + 2
    return page[:i] + new + page[j:], True


def main():
    check = "--check" in sys.argv
    page = read(PAGE)
    bridge = read(BRIDGE)
    gradle = read(GRADLE)
    notes = read(NOTES)
    touched = []

    page, a = swap_list(page, "OTHERS")
    page, b = swap_list(page, "SETAPPS")
    if a or b:
        touched.append("the two lists")

    for old, new, why in ((CARD_OLD, CARD_NEW, "the card"),
                          (SHEET_OLD, SHEET_NEW, "the sheet"),
                          (GUIDE_OLD, GUIDE_NEW, "the guide line")):
        if new not in page:
            if old not in page:
                sys.exit("%s is neither the old one nor the new one" % why)
            page = page.replace(old, new, 1)
            touched.append(why)

    if '"unote" to' not in bridge:
        if "private val APPS = listOf(" not in bridge:
            sys.exit("Bridge.kt has no APPS list")
        i = bridge.index("    private val APPS = listOf(")
        j = bridge.index("\n    )", i) + len("\n    )")
        bridge = bridge[:i] + BRIDGE_NEW + bridge[j:]
        touched.append("the addresses in Bridge.kt")

    if ('const JOURNAL_PAGE = "%s";' % V) not in page:
        if ('const JOURNAL_PAGE = "%s";' % OLD) not in page:
            sys.exit("the page does not say %s" % OLD)
        page = page.replace('const JOURNAL_PAGE = "%s";' % OLD, 'const JOURNAL_PAGE = "%s";' % V, 1)
        if "  var WN = {\n" not in page:
            sys.exit("the page has no What's New block")
        page = page.replace("  var WN = {\n", "  var WN = {\n" + WN_ENTRY, 1)
        touched.append("JOURNAL_PAGE and What's New")

    if ('versionName = "%s"' % V) not in gradle:
        if ('versionName = "%s"' % OLD) not in gradle:
            sys.exit("build.gradle.kts does not say %s" % OLD)
        gradle = gradle.replace('versionName = "%s"' % OLD, 'versionName = "%s"' % V, 1)
        touched.append("versionName")

    if "## %s " % V not in notes:
        notes = NOTES_ENTRY + notes
        touched.append("PATCH_NOTES")

    others = page.split("var OTHERS = [")[1].split("];")[0]
    setapps = page.split("var SETAPPS = [")[1].split("];")[0]
    probes = [
        (LIST_NEW.replace("{NAME}", "OTHERS") in page, "the five rows are not in OTHERS"),
        (LIST_NEW.replace("{NAME}", "SETAPPS") in page, "the five rows are not in SETAPPS"),
        (others.count('["') == 5, "OTHERS does not hold five apps"),
        (setapps.count('["') == 5, "SETAPPS does not hold five apps"),
        ('"myhub"' in others and '"unote"' in others, "My Hub or UNote is missing from OTHERS"),
        ('"myhub"' in setapps and '"unote"' in setapps, "My Hub or UNote is missing from SETAPPS"),
        (CARD_NEW in page, "the card still names three"),
        (SHEET_NEW in page, "the sheet still says three more"),
        (GUIDE_NEW in page, "the guide line still names three"),
        ('"unote" to "https://anekthegreat.github.io/UNote/"' in bridge, "Bridge.kt cannot open UNote"),
        ("github.com/AnekTheGreat/My-Hub/releases/latest" in bridge, "Bridge.kt still sends My Hub to Play"),
        (bridge.count("play.google.com/store/apps/details?id=") == 2,
         "Bridge.kt still sends somebody to a Play listing that is not there"),
        ('const JOURNAL_PAGE = "%s";' % V in page, "the page does not say %s" % V),
        ('"%s": {' % V in page, "What's New has no %s entry" % V),
        ('versionName = "%s"' % V in gradle, "build.gradle.kts does not say %s" % V),
        ("## %s " % V in notes, "PATCH_NOTES has no %s entry" % V),
        ("ujournal-page" in page, "the page lost its marker"),
    ]
    bad = [why for ok, why in probes if not ok]
    if bad:
        sys.exit("; ".join(bad))

    if check:
        print("all %d checks pass - the tree carries UJournal %s" % (len(probes), V))
        print("untouched this run" if not touched else "applied: " + ", ".join(touched))
        return

    write(PAGE, page)
    write(BRIDGE, bridge)
    write(GRADLE, gradle)
    write(NOTES, notes)
    print("UJournal %s written to the page, Bridge.kt, build.gradle.kts and PATCH_NOTES.md" % V)
    print("next: the apply workflow commits it, then release.yml for %s" % V)


if __name__ == "__main__":
    main()
