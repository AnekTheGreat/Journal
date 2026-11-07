#!/usr/bin/env python3
"""UJournal 2.0 - two numbers, and a quieter bar.

The version becomes 2.0: a major and a minor, no third number, and the build number is worked
out from that with a missing part counting as zero. The top bar keeps the heart and the gear
only - backing up, moving to a new device and checking for updates are all in Settings, where
they already were - and the gear sits at the far right.

    python3 dev/patch-200.py            # apply
    python3 dev/patch-200.py --check    # verify only, writes nothing
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "app/src/main/assets/index.html"
GRADLE = "app/build.gradle.kts"
NOTES = "PATCH_NOTES.md"

V = "2.0"
OLD = "1.9.11"

BAR_OLD = ('<header id="bar"><div id="brand">UJournal</div>'
           '<button id="set" title="Settings" aria-label="Settings">\u2699</button>'
           '<button id="more" title="Back up or move to a new device">\u22ef</button>'
           '<button id="tip" title="Support UJournal">\u2665</button>'
           '<button id="check" title="Check for updates">\u27f3</button></header>')

BAR_NEW = ('<header id="bar"><div id="brand">UJournal</div>'
           '<button id="tip" title="Support UJournal">\u2665</button>'
           '<button id="set" title="Settings" aria-label="Settings">\u2699</button></header>')

WN_HEAD = '''  var WN = {
    "1.9.11": {'''

WN_NEW = '''  var WN = {
    "2.0": {
      date: "7 November 2026",
      title: "UJournal 2.0 - two numbers, and a quieter bar",
      notes: [
        "This is 2.0, and a version here is two parts from now on: a major and a minor. The third number is gone - 1.9.10 and 1.9.11 were the last of it.",
        "The top bar keeps only the heart and the gear. Backing up, moving to a new device and checking for updates all live in Settings, where they already were, and the gear is now the last button on the right.",
        "A screen that does not arrive in one piece is not fetched again and again any more. It is tried once, and again only when you ask, or when six hours have passed.",
        "The welcome, the tour and these notes are remembered by the app itself as well as by the screen, so a phone that clears the screen's storage no longer meets the same popup on every launch."
      ]
    },
    "1.9.11": {'''

MOVE_OLD = '''  // One file holds every journal, every entry and everything attached to it. The shell writes it
  // where the phone's own Save dialog points, so a backup can go to Downloads, a card or a cloud
  // folder; Restore reads one back and replaces the shelf, which is why it asks twice.
  function showMove() {
    $("sheet-card").innerHTML =
      '<h2>Move to a new device</h2>' +
      '<p>One file holds every journal and everything attached to it. Save it somewhere you can ' +
      'reach from the new phone, then choose Restore there.</p>' +
      '<p>The file is written by the phone itself, so it goes wherever you point the Save dialog ' +
      '&mdash; Downloads, a card, a cloud folder. Nothing is uploaded anywhere.</p>' +
      '<div class="row"><button id="bk">Save a backup</button>' +
      '<button id="rs" class="go">Restore a backup</button></div>' +
      '<p style="margin-top:14px;font-size:12px">Restoring replaces every journal on this phone ' +
      'with the ones in the file. It asks once before it does.</p>';
    $("sheet").classList.remove("hide");
    $("bk").onclick = function () { $("sheet").classList.add("hide"); call("backup"); };
    $("rs").onclick = function () {
      if (!this.getAttribute("data-armed")) {
        this.setAttribute("data-armed", "1");
        this.textContent = "Replace your journal?";
        return;
      }
      $("sheet").classList.add("hide");
      call("restore");
    };
  }

'''

MOVE_NEW = '''  // 2.0 - MOVE TO A NEW DEVICE IS NOT A SHEET OF ITS OWN. Save a backup and Restore a backup are
  // the first two buttons under the gear, in Transfer, which is where someone looking for them
  // looks first. This used to be a third sheet behind a \u22ef in the top bar, and the bar is now the
  // heart and the gear only.

'''

CSS_OLD = '#check,#set,#more,#tip{background:none;border:0;color:var(--muted);font-size:20px;padding:6px 8px}'
CSS_NEW = '#set,#tip{background:none;border:0;color:var(--muted);font-size:20px;padding:6px 8px}'

WIRE_OLD = '''  $("more").onclick = showMove;
  $("set").onclick = function () { showSettings(""); };
  $("tip").onclick = showTips;
  $("check").onclick = function () { say("Checking for updates\u2026"); call("checkUpdates"); };'''

WIRE_NEW = '''  $("tip").onclick = showTips;
  $("set").onclick = function () { showSettings(""); };'''

GRADLE_OLD = '''        versionName = "1.9.11"
        // Three digits of room per part. The old 10_000 / 100 / 1 layout gave 1.9.100 and 1.11.0
        // the same code, and a code that does not go up is a release Android refuses to install.
        versionCode = versionName!!.split(".").let { p ->
            p[0].toInt() * 1_000_000 + p[1].toInt() * 1_000 + p[2].toInt()
        }'''

GRADLE_NEW = '''        versionName = "2.0"
        // A version here is major.minor, so a part that is not there counts as zero instead of
        // crashing the build. Three digits of room per part: no two versions can share a code, and
        // a code that does not go up is a release Android refuses to install over the one before it.
        versionCode = versionName!!.split(".").let { p ->
            p[0].toInt() * 1_000_000 +
                p.getOrElse(1) { "0" }.toInt() * 1_000 +
                p.getOrElse(2) { "0" }.toInt()
        }'''

NOTE_HEAD = "## 1.9.11 \u2014 November 7, 2026"

NOTE_NEW = '''## 2.0 \u2014 November 7, 2026

**Two numbers, and a quieter bar.**

- The version is 2.0: a major and a minor, no third number. 1.9.10 and 1.9.11 were the last of
  the three-part numbers.
- The top bar keeps only the heart and the gear. Backing up, moving to a new device and checking
  for updates are all in Settings, where they already were, and the gear is the last button on the
  right.
- A screen that does not arrive in one piece is no longer fetched again on every launch and every
  return. It is tried once, and again only on a check you asked for, or after six hours.
- The welcome, the tour and What's New are kept by the app as well as by the screen, so a cleared
  cache cannot bring the same popup back on every launch.

''' + NOTE_HEAD

EDITS = [
    (PAGE, 'const JOURNAL_PAGE = "%s";' % OLD, 'const JOURNAL_PAGE = "%s";' % V),
    (PAGE, BAR_OLD, BAR_NEW),
    (PAGE, CSS_OLD, CSS_NEW),
    (PAGE, MOVE_OLD, MOVE_NEW),
    (PAGE, WIRE_OLD, WIRE_NEW),
    (PAGE, WN_HEAD, WN_NEW),
    (GRADLE, GRADLE_OLD, GRADLE_NEW),
    (NOTES, NOTE_HEAD, NOTE_NEW),
]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def write(rel, text):
    with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
        f.write(text)


def main():
    check = "--check" in sys.argv
    touched = []

    for rel, old, new in EDITS:
        text = read(rel)
        if new in text:
            continue
        if old not in text:
            sys.exit("%s: the anchor for this edit is not there - the tree is not at %s" % (rel, OLD))
        write(rel, text.replace(old, new, 1))
        touched.append(rel)

    page = read(PAGE)
    gradle = read(GRADLE)
    notes = read(NOTES)

    bar = page[page.index('<header id="bar">'):]
    bar = bar[:bar.index('</header>')]

    probes = [
        ('const JOURNAL_PAGE = "%s";' % V in page, "the page does not say %s" % V),
        ('    "%s": {' % V in page, "What's New has no %s entry" % V),
        ('const JOURNAL_PAGE = "%s";' % OLD not in page, "the page still says %s" % OLD),
        ('id="more"' not in page, "the move-to-a-new-device button is still in the bar"),
        ('id="check"' not in page, "the check-for-updates button is still in the bar"),
        ('showMove' not in page, "the move sheet is still in the page"),
        ('$("check").onclick' not in page, "the removed button is still wired"),
        ('id="set"' in bar and 'id="tip"' in bar, "the bar lost the heart or the gear"),
        (bar.rindex('id="set"') > bar.rindex('id="tip"'), "the gear is not the last button on the right"),
        ('#set,#tip{' in page, "a style still names the removed buttons"),
        ('ujournal-page' in page, "the page lost its ujournal-page marker"),
        ('remembered("ujournal.wn")' in page, "the markers are not kept by the app as well"),
        ('versionName = "%s"' % V in gradle, "build.gradle.kts does not carry %s" % V),
        ('getOrElse(1) { "0" }' in gradle, "a two-part version would crash the build"),
        ('getOrElse(2) { "0" }' in gradle, "a two-part version would crash the build"),
        ("## %s " % V in notes, "PATCH_NOTES has no %s entry" % V),
    ]
    bad = [why for ok, why in probes if not ok]
    if bad:
        sys.exit("; ".join(bad))

    if check:
        print("all %d checks pass - the tree carries %s" % (len(probes), V))
        print("untouched this run" if not touched else "applied: " + ", ".join(sorted(set(touched))))
        return

    print("UJournal %s applied to index.html, build.gradle.kts and PATCH_NOTES.md" % V)
    print("next: the apply workflow commits it, then release.yml on tag v%s" % V)


if __name__ == "__main__":
    main()
