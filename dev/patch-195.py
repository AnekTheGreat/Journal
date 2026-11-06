#!/usr/bin/env python3
"""UJournal 1.9.5 - the birthdays card reports what FamTM actually holds.

1.9.4 adds birthdays without a tap, but every way of getting nothing looked the same: no FamTM, a
FamTM that cannot be read, and a FamTM that is readable and simply has no birthdays in it all ended
as "nothing new". That is why it can look like the sync is broken when it is FamTM's list that is
empty.

The card now asks one question and draws the answer: which FamTM is on the phone, how many birthdays
it offers, and how many this journal already keeps. A list that was read and is empty says so, and
the tap says the same in a sentence.

Usage: python3 dev/patch-195.py [--check]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADLE = ROOT / "app/build.gradle.kts"
BRIDGE = ROOT / "app/src/main/java/app/ujournal/Bridge.kt"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

BRIDGE_ANCHOR = '''            .put("app", app ?: "")
            // What this journal publishes back, counted after the import so the number is the truth
            // of the list FamTM will read, not of the list before the tap.
            .put("shared", store.plans().count { it.kind == "birthday" })
            .toString()
    }.getOrDefault("{}")
'''

BRIDGE_ADD = '''
    /**
     * Everything the card needs, in one read: which FamTM is on the phone, how many birthdays it
     * offers, and how many this journal already keeps. Offered is -1 when the list could not be read
     * at all, which is a different thing from a list that was read and is empty - the difference
     * between a broken exchange and a FamTM with nobody's birthday in it.
     */
    @JavascriptInterface
    fun famtmState(): String = runCatching {
        val app = FamTm.version(ui)
        val read = FamTm.birthdays(ui)
        JSONObject()
            .put("app", app ?: "")
            .put("offered", read?.size ?: -1)
            .put("kept", store.plans().count { it.kind == "birthday" })
            .put("why", when {
                app == null -> "no-app"
                read == null -> "no-read"
                read.isEmpty() -> "empty"
                else -> "ok"
            })
            .toString()
    }.getOrDefault("{}")
'''

CARD_OLD = '''  // -1 is no FamTM on the phone, -2 is FamTM there whose list this app could not read. They are
  // different problems and the card says so, instead of calling both of them "not installed".
  function famtmPending() {
    var n = parseInt(call("famtmBirthdays"), 10);
    return isNaN(n) ? 0 : n;
  }
'''

CARD_NEW = '''  // What the card knows, in one read: which FamTM is on the phone, how many birthdays it offers, and
  // how many are already here. Offered -1 means the list could not be read at all, which is not the
  // same as a list that was read and turned out to be empty.
  function famtmState() {
    var s = parse(call("famtmState"), null);
    if (s && s.why) return s;
    // An app older than 1.9.5 only answers with a count of the ones that are new here.
    var n = parseInt(call("famtmBirthdays"), 10);
    return {
      why: n === -1 ? "no-app" : n === -2 ? "no-read" : "ok",
      app: "", offered: n > 0 ? n : 0, kept: 0
    };
  }
'''

BUTTON_OLD = '''  function famtmButton() {
    var n = famtmPending();
    var kept = (S.plans || []).filter(function (p) { return p.kind === "birthday"; }).length;
    var line = n === -1
      ? "FamTM isn't installed on this phone"
      : n === -2
        ? "FamTM is here, but this copy can't read it"
        : n > 0
          ? (n === 1 ? "1 new birthday from FamTM" : n + " new birthdays from FamTM")
          : kept
            ? (kept === 1 ? "Following FamTM · 1 birthday" : "Following FamTM · " + kept + " birthdays")
            : "Following FamTM · none yet";
    return '<button class="fambtn" data-sync="1"><span class="fc">🎂</span><span>' +
      '<b>Birthdays from FamTM</b><i>' + line + '</i></span></button>';
  }
'''

BUTTON_NEW = '''  function famtmButton() {
    var s = famtmState();
    var app = s.app ? "FamTM " + s.app : "FamTM";
    var line;
    if (s.why === "no-app") line = "FamTM isn't installed on this phone";
    else if (s.why === "no-read") line = app + " is here, but this copy can't read it";
    else if (s.why === "empty") line = app + " has nobody with a birthday in it";
    else line = s.offered + " in FamTM · " + s.kept + " here";
    return '<button class="fambtn" data-sync="1"><span class="fc">🎂</span><span>' +
      '<b>Birthdays from FamTM</b><i>' + line + '</i></span></button>';
  }
'''

SYNC_OLD = '''  function runSync() {
    var r = parse(call("syncBirthdays"), null) || {};
    refresh();
    var added = parseInt(r.added, 10) || 0;
    var shared = parseInt(r.shared, 10) || 0;
    var why = String(r.why || "");
    var fam = String(r.app || "");
    var mine = appVer() || JOURNAL_PAGE;
    var msg;
    if (added > 0) {
      msg = added === 1 ? "One birthday added from FamTM" : added + " birthdays added from FamTM";
    } else if (why === "no-app") {
      msg = "FamTM isn't installed on this phone";
    } else if (why === "no-read") {
      msg = (fam ? "FamTM " + fam + " is installed" : "FamTM is installed") +
        ", but this copy of the journal" + (mine ? " (" + mine + ")" : "") +
        " couldn't read its list – update the journal app, open FamTM once, then try again";
    } else {
      msg = "FamTM had nothing new";
    }
'''

SYNC_NEW = '''  function runSync() {
    var r = parse(call("syncBirthdays"), null) || {};
    refresh();
    var added = parseInt(r.added, 10) || 0;
    var shared = parseInt(r.shared, 10) || 0;
    var offered = parseInt(r.offered, 10) || 0;
    var why = String(r.why || "");
    var fam = String(r.app || "");
    var mine = appVer() || JOURNAL_PAGE;
    var msg;
    if (added > 0) {
      msg = added === 1 ? "One birthday added from FamTM" : added + " birthdays added from FamTM";
    } else if (why === "no-app") {
      msg = "FamTM isn't installed on this phone";
    } else if (why === "no-read") {
      msg = (fam ? "FamTM " + fam + " is installed" : "FamTM is installed") +
        ", but this copy of the journal" + (mine ? " (" + mine + ")" : "") +
        " couldn't read its list – update the journal app, open FamTM once, then try again";
    } else if (offered === 0) {
      msg = "FamTM read fine, and has nobody with a birthday in it yet – a born date with a day and a month is what it shares";
    } else {
      msg = "Already up to date · " + (shared || 0) + " here";
    }
'''

WN = '''    "1.9.5": {
      date: "6 November 2026",
      title: "The birthdays card says what FamTM actually holds",
      notes: [
        "Every way of getting nothing used to look the same. The card now says which one it is: FamTM is not on the phone, FamTM is here and this copy of the journal cannot read it, or FamTM was read and has nobody with a birthday in it yet.",
        "It also shows the two counts plainly - how many birthdays FamTM offers, and how many this journal already keeps - so an exchange that is working and an exchange that has nothing to carry can be told apart at a glance.",
        "A born date with a day and a month is what FamTM shares. A year on its own has no day to keep, so that person is not in the list, and the card now says so instead of going quiet."
      ]
    },
'''

NOTE = '''## 1.9.5 — November 6, 2026

**The birthdays card reports what FamTM actually holds**

### Fixed
- **Three different things all read as "nothing new".** No FamTM, FamTM that cannot be read, and a
  FamTM that was read and has nobody in it were indistinguishable on the card. The shell now answers
  with the FamTM version, the number of birthdays it offers and the number already kept, and the card
  draws that: an empty list is reported as an empty list rather than as a failed exchange.
- **The counts are visible.** The card reads N in FamTM and M here, so the difference between an
  exchange that works and one with nothing to carry is on the screen.
- **The tap says it in a sentence.** Up to date, nobody with a birthday in FamTM yet, or the versions
  of both apps when the list could not be read.

### Unchanged
- Birthdays still add themselves on open and when Plans is opened, nothing is uploaded, and the rose
  colour in the calendar, the provider back to FamTM and the plan sheet are as they were in 1.9.4.


'''


def edit(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch-195: %s: no such text to replace:\n  %r" % (path.name, old[:90]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    page = PAGE.read_text(encoding="utf-8")
    done = (
        'const JOURNAL_PAGE = "1.9.5";' in page
        and '"1.9.5": {' in page
        and "function famtmState()" in page
        and 'has nobody with a birthday in it' in page
        and 'versionName = "1.9.5"' in GRADLE.read_text(encoding="utf-8")
        and "fun famtmState()" in BRIDGE.read_text(encoding="utf-8")
        and "## 1.9.5 — November 6, 2026" in NOTES.read_text(encoding="utf-8")
    )
    if check:
        print("1.9.5 already applied" if done else "1.9.5 not applied yet")
        return 0 if done else 1
    if done:
        print("1.9.5 already applied - nothing to do")
        return 0

    edit(BRIDGE, [(BRIDGE_ANCHOR, BRIDGE_ANCHOR + BRIDGE_ADD)])
    edit(PAGE, [
        ('const JOURNAL_PAGE = "1.9.4";', 'const JOURNAL_PAGE = "1.9.5";'),
        ('  var WN = {\n    "1.9.4": {', '  var WN = {\n' + WN + '    "1.9.4": {'),
        (CARD_OLD, CARD_NEW),
        (BUTTON_OLD, BUTTON_NEW),
        (SYNC_OLD, SYNC_NEW),
    ])
    edit(GRADLE, [('versionName = "1.9.4"', 'versionName = "1.9.5"')])
    edit(NOTES, [('## 1.9.4 — November 6, 2026', NOTE + '## 1.9.4 — November 6, 2026')])

    print("1.9.5 applied: famtmState, card counts, empty-list sentence, notes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
