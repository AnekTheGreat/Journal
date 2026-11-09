#!/usr/bin/env python3
"""UJournal 2.2 - What's New stops coming back.

    python3 dev/patch-22.py            # apply
    python3 dev/patch-22.py --check    # verify only, writes nothing

Two ordinary things made the sheet open on launch after launch even though the journal was already
on that version:

  * the test was "the version is not equal", so a screen that went back to an earlier copy - the
    one the app fetched last time, then the one inside the APK - differed in both directions and
    asked again each way round;
  * the mark was written when "Got it" was tapped, not when the sheet appeared, so closing the app
    with the sheet open counted as never having read it.

Now the mark is written as the sheet appears and it only ever moves forwards, so only a screen that
is really newer opens it, once. The welcome and the tour already mark themselves on the way in; they
keep doing so. The notes are still one tap away under Settings, Updates.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "app/src/main/assets/index.html"
GRADLE = "app/build.gradle.kts"
NOTES = "PATCH_NOTES.md"

V = "2.2"
OLD = "2.1"

WN_NEW = '''  var WN = {
    "2.2": {
      date: "9 November 2026",
      title: "What's New stops coming back",
      notes: [
        "The sheet opens once now, and only when the journal is really newer than the last screen it showed you. It used to open whenever the version merely differed, which included going back to an earlier screen, so the same notes could arrive again and again.",
        "Closing the journal while the sheet was open counted as never having read it, so the next launch put it back. It counts as read the moment it appears.",
        "The welcome and the tour are remembered the same way, so nothing that has been shown once returns by itself."
      ]
    },
'''

HELPERS = '''  // 2.2 - ONLY A SCREEN THAT IS REALLY NEWER. "Not equal" also means "older", and the shell can
  // hand the page an earlier copy than the one it saw last time, so the same notes came back. A
  // dotted comparison answers the only question worth asking: is this newer than what was seen?
  function verNum(v) {
    return String(v || "").split(".").map(function (x) { return parseInt(x, 10) || 0; });
  }
  function isNewer(a, b) {
    var x = verNum(a), y = verNum(b), n = Math.max(x.length, y.length);
    for (var i = 0; i < n; i++) {
      var p = x[i] || 0, q = y[i] || 0;
      if (p !== q) return p > q;
    }
    return false;
  }
  function wnIsNewer() {
    var seen = wnSeen();
    if (!seen) return true;
    return isNewer(JOURNAL_PAGE, seen);
  }

'''

COMMENT_OLD = '''  // The notes for this screen travel inside the screen: a screen that arrives over the air brings
  // its own account of what changed, so nothing has to be fetched to read it. One entry per screen
  // version, and the version whose notes have been shown is kept on the phone - marked when the
  // popup is CLOSED, by its button or the phone's back, not when it is built, so the notes cannot be
  // marked read without having been put in front of the reader.
'''

COMMENT_NEW = '''  // The notes for this screen travel inside the screen: a screen that arrives over the air brings
  // its own account of what changed, so nothing has to be fetched to read it. One entry per screen
  // version, and the version whose notes have been shown is kept on the phone. 2.2 - marked the
  // moment the sheet APPEARS rather than when it is closed: a phone swiped away with the sheet open
  // counted as never having read it, and the same notes came back on the next launch. It is on the
  // screen by then, which is all "read" ever meant.
'''

NOTES_MD = '''## 2.2 - 9 November 2026

The popups stop coming back.

- **What's New opens once.** It opens only when the journal is genuinely newer than the last screen
  it showed you, instead of whenever the version merely differed - which also meant a screen that
  went back to an earlier copy asked again, over and over.
- **Closed is closed.** Leaving the journal with the sheet open used to count as never having read
  it. It counts as read the moment it appears, so the next launch is quiet.
- **Nothing else returns either.** The welcome and the tour were already marked on the way in, and
  they still are; the notes stay one tap away under Settings, Updates.

'''


def path(p):
    return os.path.join(ROOT, p)


def read(p):
    return open(path(p), encoding="utf-8").read()


def write(p, s):
    open(path(p), "w", encoding="utf-8").write(s)


def applied():
    return ('const JOURNAL_PAGE = "%s";' % V) in read(PAGE)


def check():
    page = read(PAGE)
    gradle = read(GRADLE)
    notes = read(NOTES)
    probes = [
        ('const JOURNAL_PAGE = "%s";' % V in page, "the page does not say %s" % V),
        ('    "%s": {' % V in page, "What's New has no %s entry" % V),
        ("else if (wnIsNewer()) showWhatsNew();" in page,
         "the sheet still opens whenever the version merely differs"),
        ("wnSeen() !== JOURNAL_PAGE" not in page, "the old not-equal test is still there"),
        ("function isNewer(a, b) {" in page, "there is no dotted comparison"),
        ("    wnMark();\n    var notes" in page,
         "the sheet is still marked only when its button is tapped"),
        ('versionName = "%s"' % V in gradle, "build.gradle.kts does not carry %s" % V),
        ("## %s " % V in notes, "PATCH_NOTES has no %s entry" % V),
        ('const JOURNAL_PAGE = "%s";' % OLD not in page, "the page still says %s" % OLD),
    ]
    bad = [why for ok, why in probes if not ok]
    if bad:
        sys.exit("; ".join(bad))

    def code(v):
        p = [int(x) for x in v.split(".")]
        while len(p) < 3:
            p.append(0)
        return p[0] * 1000000 + p[1] * 1000 + p[2]

    if not code(V) > code(OLD):
        sys.exit("%s does not carry a higher build number than %s" % (V, OLD))


def main():
    if not os.path.exists(path(PAGE)):
        sys.exit("run this from the repository root")

    if "--check" in sys.argv:
        check()
        print("all checks pass - the tree carries %s" % V)
        return

    if applied():
        check()
        print("already applied - nothing to do")
        return

    page = read(PAGE)

    # ---- the version --------------------------------------------------------
    page = page.replace('const JOURNAL_PAGE = "%s";' % OLD, 'const JOURNAL_PAGE = "%s";' % V, 1)

    # ---- the comment above them stops describing the old behaviour ----------
    if page.count(COMMENT_OLD) != 1:
        sys.exit("the comment above the notes is not where it was expected")
    page = page.replace(COMMENT_OLD, COMMENT_NEW, 1)

    # ---- its own notes, newest first ---------------------------------------
    page = page.replace("  var WN = {\n", WN_NEW, 1)

    # ---- open it once, and only for a newer screen -------------------------
    old_boot = "else if (wnSeen() !== JOURNAL_PAGE) showWhatsNew();"
    if page.count(old_boot) != 1:
        sys.exit("the launch line is not where it was expected")
    page = page.replace(old_boot, "else if (wnIsNewer()) showWhatsNew();", 1)

    # ---- the comparison it needs -------------------------------------------
    anchor = '  function wnSeen() { return remembered("ujournal.wn"); }'
    if page.count(anchor) != 1:
        sys.exit("wnSeen is not where it was expected")
    page = page.replace(anchor, HELPERS + anchor, 1)

    # ---- a sheet on screen has been read -----------------------------------
    mark_old = "  function showWhatsNew() {\n    var u = WN[JOURNAL_PAGE];\n    if (!u) return;\n"
    if page.count(mark_old) != 1:
        sys.exit("showWhatsNew is not where it was expected")
    page = page.replace(
        mark_old,
        mark_old + "    // 2.2 - read the moment it is on screen, not when its button is tapped.\n"
        "    wnMark();\n",
        1,
    )

    write(PAGE, page)

    # ---- the build carries the same number ---------------------------------
    gradle = read(GRADLE)
    old_name = 'versionName = "%s"' % OLD
    if gradle.count(old_name) != 1:
        sys.exit("build.gradle.kts does not name %s" % OLD)
    write(GRADLE, gradle.replace(old_name, 'versionName = "%s"' % V, 1))

    # ---- the release notes, read by release.yml ----------------------------
    notes = read(NOTES)
    if "## %s " % V not in notes:
        write(NOTES, NOTES_MD + notes)

    check()
    print("UJournal %s applied to index.html, build.gradle.kts and PATCH_NOTES.md" % V)
    print("next: the apply workflow commits it, then release.yml on tag v%s" % V)


if __name__ == "__main__":
    main()
