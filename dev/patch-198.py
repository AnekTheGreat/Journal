#!/usr/bin/env python3
"""UJournal 1.9.8 - a settings sheet with tabs, and the whole family in Other apps.

The journal's own things were three separate buttons along the top bar: the ... for a
backup, the heart for a tip and the arrow for an update. They are all behind one gear
now, cut into tabs - Journal, Transfer, Updates, Support, Other apps - so the bar is a
name and one button, and nothing has to be remembered.

The row of tabs scrolls sideways, because five tabs do not fit across a phone. Tapping
one redraws the sheet, and the redraw used to throw the row's scroll position away, so
the row snapped back to its first tab. It keeps its place now, and brings the tab you
picked into view instead of snapping.

Other apps is the whole family in one list: FamTM, My Hub, SideCut and MeasureT, which
are the four keys the shell already knows how to open.

Page only, so it arrives over the air. Run twice and the second run changes nothing;
--check only verifies.
"""
import os
import sys

PAGE = "app/src/main/assets/index.html"
NOTES = "PATCH_NOTES.md"
CHECK = "--check" in sys.argv

NEW_VER = "1.9.8"
OLD_VER = "1.9.7"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    if not CHECK:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def swap(text, old, new, what):
    if new in text:
        return text, False
    if old not in text:
        sys.exit("could not find " + what)
    return text.replace(old, new, 1), True


HEADER_OLD = '<button id="more" title="Back up or move to a new device">⋯</button>'
HEADER_NEW = '<button id="set" title="Settings" aria-label="Settings">⚙</button>'

BUTTON_CSS_OLD = "#check,#more,#tip{background:none;border:0;color:var(--muted);font-size:20px;padding:6px 8px}"
BUTTON_CSS_NEW = "#check,#set,#more,#tip{background:none;border:0;color:var(--muted);font-size:20px;padding:6px 8px}"

STYLE_OLD = "</style>"
STYLE_NEW = """.settabs{display:flex;gap:8px;overflow-x:auto;overscroll-behavior-x:contain;padding:2px 0 14px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.settabs::-webkit-scrollbar{display:none}
.settab{flex:0 0 auto;padding:8px 14px;border-radius:99px;border:1px solid var(--sand);background:none;color:var(--muted);font:600 13px -apple-system,Roboto,system-ui,sans-serif;white-space:nowrap;transition:background .15s ease,color .15s ease,border-color .15s ease}
.settab.on{background:var(--tan);border-color:var(--tan);color:#fff}
.sheet-card .sbtn{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid var(--sand);border-radius:0;background:none;color:var(--ink);padding:13px 2px}
.sheet-card .sbtn b{display:block;font-weight:600;font-size:15.5px}
.sheet-card .sbtn i{display:block;font-style:normal;font-size:12.5px;color:var(--muted);margin-top:3px}
.sheet-card .sbtn.go b{color:var(--tan)}
.sheet-card .sbtn[data-armed] b{color:#B4533F}
.sheet-card .sver{margin:16px 0 0;font-size:12px;color:var(--muted);text-align:center}
</style>"""

PANEL_ANCHOR = "  // ---- wiring ----"

PANEL = '''  // ---- settings, in one place and cut into tabs ----

  // The journal's own things used to be three buttons in the top bar. They are all behind the gear
  // now, cut into tabs, and the buttons that were there still work for anyone used to them.
  var SETTABS = [["journal", "Journal"], ["transfer", "Transfer"], ["updates", "Updates"], ["support", "Support"], ["apps", "Other apps"]];

  // The apps beside this one, and the key the shell knows each one by. The addresses live in the
  // app, so a page that arrives over the air can list them but cannot choose where a tap goes.
  var SETAPPS = [
    ["famtm", "FamTM", "The family tree in your pocket"],
    ["myhub", "My Hub", "One screen for the apps you use most"],
    ["sidecut", "SideCut", "A music player with its own equaliser"],
    ["measuret", "MeasureT", "Elevation, location, level, converter and currency"]
  ];

  function showSettings(sec) {
    var s = "journal";
    SETTABS.forEach(function (t) { if (t[0] === sec) s = sec; });
    // Where the row of tabs is scrolled to right now, so the redraw below can put it back: five tabs
    // do not fit across a phone, so the row is scrolled sideways to reach the last of them.
    var prev = $("sheet-card").querySelector(".settabs");
    var sx = prev ? prev.scrollLeft : 0;
    var tabs = SETTABS.map(function (t) {
      return '<button class="settab' + (t[0] === s ? " on" : "") + '" data-settab="' + t[0] + '">' + esc(t[1]) + "</button>";
    }).join("");
    var pane;
    if (s === "journal") {
      pane = '<button class="sbtn go" data-setdo="today"><b>Open today&rsquo;s page</b><i>The entry you are about to write</i></button>' +
        '<button class="sbtn" data-setdo="sync"><b>Birthdays from FamTM</b><i>Bring them in, and share the ones typed here back</i></button>' +
        "<p>Your journals live on this phone. Nothing here needs an account, and nothing is uploaded.</p>";
    } else if (s === "transfer") {
      pane = '<button class="sbtn go" data-setdo="backup"><b>Save a backup</b><i>One file: every journal and everything attached to it</i></button>' +
        '<button class="sbtn" data-setdo="restore"><b>Restore a backup</b><i>Replaces every journal on this phone, and asks first</i></button>' +
        "<p>A backup goes wherever the phone&rsquo;s own Save dialog points &mdash; Downloads, a card, a cloud folder.</p>";
    } else if (s === "updates") {
      pane = '<button class="sbtn go" data-setdo="check"><b>Check for updates</b><i>Ask now instead of waiting for the next open</i></button>' +
        '<button class="sbtn" data-setdo="news"><b>What&rsquo;s New</b><i>The notes for this version</i></button>' +
        "<p>A new screen puts itself in place the next time the journal opens, with nothing from a store. Only a change to the app itself comes from the release page.</p>";
    } else if (s === "support") {
      pane = "<p>UJournal is free and has no ads. A tip is a thank you, and nothing unlocks.</p><div class=\"row\">" +
        [2, 5, 10, 25, 50].map(function (d) { return '<button data-tip-amount="' + d + '">$' + d + "</button>"; }).join("") +
        '</div><button class="sbtn" data-setdo="release"><b>Release notes on the web</b><i>The same notes, in a browser</i></button>';
    } else {
      pane = SETAPPS.map(function (a) {
        return '<button class="sbtn" data-setapp="' + a[0] + '"><b>' + esc(a[1]) + "</b><i>" + esc(a[2]) + "</i></button>";
      }).join("") + "<p>Made by the same person, and not one of them asks you to sign in.</p>";
    }
    var app = appVer();
    $("sheet-card").innerHTML = '<h2>Settings</h2><div class="settabs">' + tabs + "</div>" + pane +
      '<p class="sver">UJournal ' + esc(JOURNAL_PAGE) + (app && app !== JOURNAL_PAGE ? " &middot; app " + esc(app) : "") + "</p>";
    $("sheet").classList.remove("hide");

    // Put the row back where it was, then make sure the tab just picked is the one you can see.
    var strip = $("sheet-card").querySelector(".settabs");
    if (strip) {
      strip.scrollLeft = sx;
      var on = strip.querySelector(".settab.on");
      if (on) {
        var r = on.getBoundingClientRect(), b = strip.getBoundingClientRect();
        if (r.left < b.left) strip.scrollLeft = Math.max(0, strip.scrollLeft - (b.left - r.left) - 10);
        else if (r.right > b.right) strip.scrollLeft += r.right - b.right + 10;
      }
    }
    $("sheet-card").querySelectorAll("[data-settab]").forEach(function (b) {
      b.onclick = function () { showSettings(b.getAttribute("data-settab")); };
    });
    $("sheet-card").querySelectorAll("[data-setapp]").forEach(function (b) {
      b.onclick = function () {
        var ok = call("openApp", b.getAttribute("data-setapp"));
        if (ok === false || ok === "false") say("No browser to open that with");
        else $("sheet").classList.add("hide");
      };
    });
    $("sheet-card").querySelectorAll("[data-setdo]").forEach(function (b) {
      b.onclick = function () {
        var what = b.getAttribute("data-setdo");
        // Restoring replaces every journal on the phone, so it asks once, in place.
        if (what === "restore" && !b.getAttribute("data-armed")) {
          b.setAttribute("data-armed", "1");
          b.querySelector("b").textContent = "Replace your journal?";
          return;
        }
        $("sheet").classList.add("hide");
        if (what === "today") openDay(today());
        else if (what === "sync") runSync();
        else if (what === "backup") call("backup");
        else if (what === "restore") call("restore");
        else if (what === "check") { say("Checking for updates…"); call("checkUpdates"); }
        else if (what === "news") showWhatsNew();
        else if (what === "release") call("openRelease", appVer() || JOURNAL_PAGE);
      };
    });
  }

'''

WIRE_OLD = '  $("more").onclick = showMove;'
WIRE_NEW = '  $("more").onclick = showMove;\n  $("set").onclick = function () { showSettings(""); };'

WN_ANCHOR = "  var WN = {\n"

WN_ENTRY = '''    "1.9.8": {
      date: "6 November 2026",
      title: "One gear, and the whole family in it",
      notes: [
        "Settings is one sheet now, behind a gear in the top bar, cut into tabs: Journal, Transfer, Updates, Support and Other apps. The row of tabs scrolls sideways, and the buttons that were along the bar still work for anyone used to them.",
        "Other apps lists the whole family in one place: FamTM, My Hub, SideCut and MeasureT.",
        "The row of tabs keeps the place you scrolled it to. Picking a tab further along used to redraw the sheet and snap the row back to its first tab; now it stays where you left it and brings the tab you picked into view."
      ]
    },
'''

NOTE_SECTION = """## 1.9.8 — November 6, 2026

**One gear, and the whole family in it**

### Changed

- Settings is one sheet, behind a gear in the top bar, cut into tabs: Journal, Transfer, Updates,
  Support and Other apps. The row of tabs scrolls sideways, and keeps the place you scrolled it to
  instead of snapping back to its first tab.
- Other apps is the whole family in one list: FamTM, My Hub, SideCut and MeasureT.
- The ... , heart and arrow in the top bar still work; the gear is the one place that holds
  everything.

Page only, so it arrives over the air.


"""


def main():
    page = read(PAGE)
    notes = read(NOTES) if os.path.exists(NOTES) else None
    changed = []

    page, did = swap(page, HEADER_OLD, HEADER_NEW + HEADER_OLD, "the gear in the top bar")
    changed.append(did)
    page, did = swap(page, BUTTON_CSS_OLD, BUTTON_CSS_NEW, "the top bar's button style")
    changed.append(did)
    page, did = swap(page, STYLE_OLD, STYLE_NEW, "the end of the stylesheet")
    changed.append(did)
    page, did = swap(page, PANEL_ANCHOR, PANEL + PANEL_ANCHOR, "the wiring marker")
    changed.append(did)
    page, did = swap(page, WIRE_OLD, WIRE_NEW, "where the top bar is wired")
    changed.append(did)
    page, did = swap(page, 'const JOURNAL_PAGE = "%s";' % OLD_VER, 'const JOURNAL_PAGE = "%s";' % NEW_VER, "the version line")
    changed.append(did)
    page, did = swap(page, WN_ANCHOR, WN_ANCHOR + WN_ENTRY, "the notes the popup reads")
    changed.append(did)

    if notes is not None:
        if "## %s — November 6, 2026" % NEW_VER not in notes:
            anchor = "## %s — November 6, 2026" % OLD_VER
            if anchor not in notes:
                sys.exit("could not find where the notes start")
            notes = notes.replace(anchor, NOTE_SECTION + anchor, 1)
            changed.append(True)
        else:
            changed.append(False)

    write(PAGE, page)
    if notes is not None:
        write(NOTES, notes)

    if not any(changed):
        print("already at " + NEW_VER + " - nothing to do")
        return
    print("wrote " + NEW_VER)


if __name__ == "__main__":
    main()
