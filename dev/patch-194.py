#!/usr/bin/env python3
"""UJournal 1.9.4 - birthdays add themselves, and they are rose, not tan.

FamTM publishes the birthdays of everyone alive in the family, and the journal could only get them
by tapping a card. Now the page reads that list when the journal opens and whenever Plans is opened,
and adds whatever is new - so the calendar carries the family's birthdays without being asked. The
same call the card makes is used, so nothing new reaches the plans: an existing birthday is still
never added twice.

In the calendar a birthday is drawn in rose, not in the tan a day with a journal entry gets. A day
that has both stays rose with the dot that means a plan, and a small key under the grid says which
colour is which.

Page only: no new permission, no new shell call. The version moves to 1.9.4 so an installed copy
takes this screen over the air.

Usage: python3 dev/patch-194.py [--check]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADLE = ROOT / "app/build.gradle.kts"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

CSS_VARS_OLD = ":root{--bg:#F4EBDD;--card:#FBF6EC;--tan:#C8AD8D;--sand:#E6D5BC;--ink:#4A3F35;--muted:#9C8B77}"
CSS_VARS_NEW = ":root{--bg:#F4EBDD;--card:#FBF6EC;--tan:#C8AD8D;--sand:#E6D5BC;--ink:#4A3F35;--muted:#9C8B77;--rose:#BE8681}"

GRID_OLD = """.grid button.has{background:var(--tan);color:#fff}
.grid button.pl::after{content:"";position:absolute;left:50%;bottom:5px;width:4px;height:4px;margin-left:-2px;border-radius:2px;background:var(--tan)}
.grid button.has.pl::after{background:#fff}"""

GRID_NEW = """.grid button.has{background:var(--tan);color:#fff}
/* A birthday is not a journal entry: it keeps its own colour, so a day someone was born on can be
   told from a day something was written about. Rose sits after the tan rule so a day with both is
   drawn rose, and the dot that means a plan keeps its white. */
.grid button.bd{background:var(--rose);color:#fff}
.grid button.bd.pl::after{background:#fff}
.grid button.pl::after{content:"";position:absolute;left:50%;bottom:5px;width:4px;height:4px;margin-left:-2px;border-radius:2px;background:var(--tan)}
.grid button.has.pl::after{background:#fff}
.cal-key{display:flex;gap:18px;justify-content:center;color:var(--muted);font-size:11.5px;padding:12px 0 2px}
.cal-key i{display:inline-block;width:9px;height:9px;border-radius:5px;margin-right:6px;vertical-align:1px}
.cal-key .k-tan{background:var(--tan)}
.cal-key .k-rose{background:var(--rose)}"""

CAL_OLD = """    var have = {}, planned = {};
    S.entries.forEach(function (e) { have[e.date] = 1; });
    // A plan marks the days it covers. A birthday marks its month and day in every year, which is
    // kept apart from the full dates by having no year in the key at all.
    (S.plans || []).forEach(function (p) {
      if (p.kind === "birthday") { planned[String(p.start).slice(5)] = 1; return; }"""

CAL_NEW = """    var have = {}, planned = {}, bday = {};
    S.entries.forEach(function (e) { have[e.date] = 1; });
    // A plan marks the days it covers. A birthday marks its month and day in every year, which is
    // kept apart from the full dates by having no year in the key at all - and apart from a plan as
    // well since 1.9.4: it is kept in its own map so the calendar can draw it in its own colour
    // instead of in the tan a day with a journal entry gets.
    (S.plans || []).forEach(function (p) {
      if (p.kind === "birthday") { bday[String(p.start).slice(5)] = 1; return; }"""

CELL_OLD = """      var pl = planned[k] || planned[k.slice(5)];
      h += '<button class="' + (have[k] ? "has" : "") + (pl ? " pl" : "") + '" data-date="' + k + '">' + n + '</button>';
    }
    h += '</div><div class="today"><button data-today="1">Today</button></div>';"""

CELL_NEW = """      var pl = planned[k] || planned[k.slice(5)];
      var bd = bday[k.slice(5)];
      h += '<button class="' + (have[k] ? "has" : "") + (pl ? " pl" : "") + (bd ? " bd" : "") +
        '" data-date="' + k + '">' + n + '</button>';
    }
    h += '</div><div class="cal-key"><span><i class="k-tan"></i>Entry</span>' +
      '<span><i class="k-rose"></i>Birthday</span></div>' +
      '<div class="today"><button data-today="1">Today</button></div>';"""

BUTTON_OLD = """  function famtmButton() {
    var n = famtmPending();
    var line = n > 0
      ? (n === 1 ? "1 new birthday from FamTM" : n + " new birthdays from FamTM")
      : n === -1
        ? "FamTM isn't installed on this phone"
        : n === -2
          ? "FamTM is here, but this copy can't read it"
          : "Bring FamTM's across, and share yours back";
    return '<button class="fambtn" data-sync="1"><span class="fc">🎂</span><span>' +
      '<b>Sync birthdays</b><i>' + line + '</i></span></button>';
  }"""

BUTTON_NEW = """  function famtmButton() {
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
  }"""

AUTOSYNC_ANCHOR = """    if (shared > 0) msg += " · " + (shared === 1 ? "1 shared back" : shared + " shared back");
    say(msg);
  }
"""

AUTOSYNC = """
  // 1.9.4 - nobody taps for a birthday. FamTM keeps the birthdays of everyone alive in the family and
  // hands them over read-only; they are read when the journal opens and whenever Plans is opened, and
  // anything not already here is added there and then. It is the same call the card makes, so the rule
  // that a birthday is never added twice still holds - the phone does the deduplicating, this only
  // asks. Throttled, because every tab change would otherwise ask again for a list that cannot have
  // changed in the last few seconds.
  var lastSync = 0;
  function autoSync() {
    if (!G || !G.syncBirthdays) return;                 // a browser, or an app older than 1.9.1
    var now = Date.now();
    if (now - lastSync < 30000) return;
    lastSync = now;
    var r = parse(call("syncBirthdays"), null) || {};
    var added = parseInt(r.added, 10) || 0;
    if (added > 0) {
      refresh();
      say(added === 1 ? "One birthday added from FamTM" : added + " birthdays added from FamTM");
    }
  }
"""

PICKTAB_OLD = "  function pickTab(n) {"
PICKTAB_NEW = "  function pickTab(n) {\n    if (n === 2) autoSync();"

RESUME_OLD = "  window.journalResume = function () { refresh(); };"
RESUME_NEW = "  window.journalResume = function () { refresh(); autoSync(); };"

BOOT_OLD = '  start();\n  call("ready");'
BOOT_NEW = '  start();\n  call("ready");\n  autoSync();'

WN = '''    "1.9.4": {
      date: "6 November 2026",
      title: "Birthdays add themselves, and they are not tan",
      notes: [
        "Nobody taps for a birthday any more. The journal reads FamTM when it opens and whenever Plans is opened, and every name and day that is not here yet is added there and then - so the birthdays of everyone alive in the family are on the calendar without being asked for.",
        "A birthday is drawn in rose in the calendar now, not in the tan a day with a journal entry gets, so a day someone was born on can be told from a day something was written about. A day with both stays rose, keeps the dot that means a plan, and a small key under the grid says which colour is which.",
        "The card in Plans says what is happening rather than what to do - Following FamTM, and how many birthdays are here - and still names the trouble when it cannot read the list.",
        "Only living people are in FamTM's list, so only living people arrive. Nothing is uploaded, and a birthday already here is never added twice."
      ]
    },
'''

NOTE = '''## 1.9.4 — November 6, 2026

**Birthdays add themselves, and a birthday is rose rather than tan**

### Changed
- **The birthdays arrive without a tap.** The page reads FamTM when the journal opens and whenever
  Plans is opened, and adds every name and day that is not in the journal yet. It is the same call
  the card made, so an existing birthday is still never added twice, and the read is bounded to once
  every thirty seconds so a tab change cannot repeat it.
- **The card in Plans is a status line now.** It reads Following FamTM with the number of birthdays
  held, and keeps the three-way answer - not installed, installed but unreadable, or N new - when the
  list cannot be read.
- **A birthday has its own colour in the calendar.** Days with a journal entry keep the tan fill; a
  birthday is filled rose, and a day with both stays rose with the dot that means a plan. A key under
  the grid names the two colours.

### Unchanged
- Only living people are in FamTM's list, so only living people arrive. Nothing is uploaded, the
  provider here still publishes this journal's birthdays back to FamTM, and the plan sheet, the
  durations and the tip heart are as they were in 1.9.3.


'''


def edit(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch-194: %s: no such text to replace:\n  %r" % (path.name, old[:90]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    page = PAGE.read_text(encoding="utf-8")
    done = (
        'const JOURNAL_PAGE = "1.9.4";' in page
        and '"1.9.4": {' in page
        and "function autoSync()" in page
        and "button.bd{" in page
        and 'versionName = "1.9.4"' in GRADLE.read_text(encoding="utf-8")
        and "## 1.9.4 — November 6, 2026" in NOTES.read_text(encoding="utf-8")
    )
    if check:
        print("1.9.4 already applied" if done else "1.9.4 not applied yet")
        return 0 if done else 1
    if done:
        print("1.9.4 already applied - nothing to do")
        return 0

    edit(PAGE, [
        ('const JOURNAL_PAGE = "1.9.3";', 'const JOURNAL_PAGE = "1.9.4";'),
        ('  var WN = {\n    "1.9.3": {', '  var WN = {\n' + WN + '    "1.9.3": {'),
        (CSS_VARS_OLD, CSS_VARS_NEW),
        (GRID_OLD, GRID_NEW),
        (CAL_OLD, CAL_NEW),
        (CELL_OLD, CELL_NEW),
        (BUTTON_OLD, BUTTON_NEW),
        (AUTOSYNC_ANCHOR, AUTOSYNC_ANCHOR + AUTOSYNC),
        (PICKTAB_OLD, PICKTAB_NEW),
        (RESUME_OLD, RESUME_NEW),
        (BOOT_OLD, BOOT_NEW),
    ])
    edit(GRADLE, [('versionName = "1.9.3"', 'versionName = "1.9.4"')])
    edit(NOTES, [('## 1.9.3 — November 6, 2026', NOTE + '## 1.9.3 — November 6, 2026')])

    print("1.9.4 applied: auto-sync on open and on Plans, rose birthdays with a key, notes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
