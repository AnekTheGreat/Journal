#!/usr/bin/env python3
"""UJournal 1.9.9 - a welcome on the first launch, a tour, and a Guide under the gear.

The page is the app: this writes the welcome overlay, the five-step tour that walks the screens a
new person has to find, and a Guide tab in Settings that holds the same tour and every feature in
one list, so nothing has to be discovered twice.

Idempotent: every insertion is guarded by a marker, so a second run writes the same bytes.
  python3 dev/patch-199.py           apply
  python3 dev/patch-199.py --check   report only
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "app" / "src" / "main" / "assets" / "index.html"
NOTES = ROOT / "PATCH_NOTES.md"
VERSION = "1.9.9"

CHECK = "--check" in sys.argv


def insert_after(src, anchor, addition, marker, what):
    """Put `addition` right after `anchor`, once. `marker` proves it is already there."""
    if marker in src:
        print(f"  already: {what}")
        return src
    n = src.count(anchor)
    if n != 1:
        raise SystemExit(f"!! {what}: anchor appears {n} times, expected 1")
    print(f"  added:   {what}")
    return src.replace(anchor, anchor + addition, 1)


def insert_before(src, anchor, addition, marker, what):
    if marker in src:
        print(f"  already: {what}")
        return src
    n = src.count(anchor)
    if n != 1:
        raise SystemExit(f"!! {what}: anchor appears {n} times, expected 1")
    print(f"  added:   {what}")
    return src.replace(anchor, addition + anchor, 1)


def swap(src, old, new, marker, what):
    if marker in src:
        print(f"  already: {what}")
        return src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"!! {what}: old text appears {n} times, expected 1")
    print(f"  changed: {what}")
    return src.replace(old, new, 1)


src = PAGE.read_text(encoding="utf-8")
if '"page":"1.9.9"' in src:
    raise SystemExit("!! page already carries the 1.9.9 marker")

# ---- the version the page calls itself ------------------------------------------------------
src = swap(
    src,
    'const JOURNAL_PAGE = "1.9.8";',
    f'const JOURNAL_PAGE = "{VERSION}";',
    f'const JOURNAL_PAGE = "{VERSION}";',
    f"page version -> {VERSION}",
)

# ---- styles: the welcome, the tour, the guide ----------------------------------------------
CSS = """#hello{position:fixed;inset:0;z-index:40;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:24px 20px;overflow-y:auto}
#hello.hide{display:none}
.hello-card{max-width:430px;width:100%;text-align:center}
.hello-mark{width:62px;height:62px;border-radius:31px;background:var(--tan);color:#fff;font-family:Georgia,serif;font-size:23px;display:flex;align-items:center;justify-content:center;margin:0 auto 15px}
.hello-card h1{font-family:Georgia,serif;font-size:28px;font-weight:400;margin:0 0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hello-card>p{color:var(--muted);font-size:14.5px;line-height:1.5;margin:0 0 18px}
.hello-list{text-align:left;margin:0 0 20px}
.hello-list div{border-top:1px solid var(--sand);padding:11px 2px}
.hello-list b{display:block;font-size:15px;font-weight:600}
.hello-list i{display:block;font-style:normal;color:var(--muted);font-size:12.5px;margin-top:3px}
.hello-go{display:block;width:100%;border:0;border-radius:16px;background:var(--tan);color:#fff;font-size:16px;font-weight:600;padding:15px;font-family:inherit}
.hello-skip{display:block;width:100%;border:0;background:none;color:var(--muted);font-size:13.5px;padding:15px 0 0;font-family:inherit}
.sheet-card .tcount{margin:0 0 10px;font-size:11.5px;color:var(--muted);letter-spacing:.6px;text-transform:uppercase}
.tourstep b{display:block;font-family:Georgia,serif;font-size:19px;font-weight:400;margin:0 0 6px}
.tourstep p{margin:0;font-size:14.5px;line-height:1.55}
.dots{display:flex;gap:6px;justify-content:center;margin:14px 0 0}
.dots .dot{width:7px;height:7px;border-radius:4px;background:var(--sand)}
.dots .dot.on{background:var(--tan);width:18px}
.sheet-card .tourskip{display:block;width:100%;border:0;background:none;color:var(--muted);font-size:13px;padding:14px 0 0;border-radius:0}
.gline{border-top:1px solid var(--sand);padding:10px 2px}
.gline b{display:block;font-size:14.5px;font-weight:600}
.gline i{display:block;font-style:normal;color:var(--muted);font-size:12.5px;margin-top:2px}
"""
src = insert_before(src, "</style>\n</head>", CSS, ".hello-card{max-width", "welcome and tour styles")

# ---- the overlay itself --------------------------------------------------------------------
src = insert_after(
    src,
    "<main id=\"view\"></main>\n",
    '<div id="hello" class="hide"></div>\n',
    '<div id="hello" class="hide"></div>',
    "the welcome overlay",
)

# ---- state ---------------------------------------------------------------------------------
src = swap(
    src,
    "rec: null, upd: null, wn: 0 };",
    "rec: null, upd: null, wn: 0, hello: 0, tour: -1 };",
    "hello: 0, tour: -1 };",
    "tour state",
)

# ---- what's new for 1.9.9 ------------------------------------------------------------------
WN_ENTRY = {
    "date": "6 November 2026",
    "title": "A welcome, a tour, and a Guide under the gear",
    "notes": [
        "A first launch opens on a welcome now: what the journal is for in three lines, and two buttons, Show me around and Skip. It comes up once, on the launch after the update, and never again.",
        "The tour walks five screens - writing a day, the three tabs, the gear, backups and updates - with Next, Back and Skip, and it closes without leaving the journal anywhere else.",
        "Settings has a Guide tab. It holds the same tour, the welcome, and every feature of the app in one list, so a feature learned once is never a thing you have to remember where it was.",
        "What's New waits until after the welcome, so a new phone is not met by two popups at once.",
        "The screen arrives over the air as usual: this one is in the page, so it is taken the next time the journal opens, with nothing installed.",
    ],
}
wn = (
    f'    "{VERSION}": {{\n'
    f'      date: "{WN_ENTRY["date"]}",\n'
    f'      title: "{WN_ENTRY["title"]}",\n'
    "      notes: [\n"
    + ",\n".join(f'        "{n}"' for n in WN_ENTRY["notes"])
    + "\n      ]\n    },\n"
)
src = insert_after(src, "  var WN = {\n", wn, f'"{VERSION}": {{\n      date:', "what's new entry")

# ---- the welcome, the tour and the guide ---------------------------------------------------
TOUR_JS = r'''  // ---- the welcome, and the tour that goes with it ----

  // A first launch is the one moment the journal can explain itself without being in the way. The
  // welcome says what the book is for; the tour walks the screens a new person has to find; and the
  // same tour lives in Settings > Guide, so nothing here is a thing seen once and then lost.
  var TOUR = [
    { t: "Every day is a page", b: "The journal opens on today. Tap the + button to write: a title, the words, a photo, and a voice note if you would rather say it." },
    { t: "Three ways into one book", b: "Journal is everything you have written, newest first. Calendar is the same entries on a month, one tap from the day. Plans holds what is still ahead." },
    { t: "Everything else is behind the gear", b: "The gear in the top bar opens Settings in tabs: Transfer, Updates, Support, Other apps - and Guide, which is this tour." },
    { t: "Nothing to sign in to", b: "Every journal stays on this phone, and nothing is uploaded. A backup is one file from Transfer, holding the journals and everything attached to them." },
    { t: "The screen keeps itself new", b: "A newer screen puts itself in place the next time the journal opens, with nothing from a store. Updates, Check for updates asks right away." }
  ];

  // Every feature in one list, for the Guide tab: what each part of the app is for, in the order it
  // is worth knowing. The tour and the guide read different things because they answer different
  // questions - where to start, and what is there at all.
  var GUIDE = [
    ["Write a day", "A page for each date: a title, the words, photos and a voice note."],
    ["Journal tab", "Every entry, newest first, one tap from the day it was written."],
    ["Calendar tab", "The same entries on a month, with the days you wrote marked on it."],
    ["Plans tab", "Dates ahead, birthdays, and FamTM's birthdays brought across in one button."],
    ["Transfer", "One file holds every journal. Restoring asks first, because it replaces them."],
    ["Updates", "New screens arrive on open. Check for updates asks now, and What's New says what changed."],
    ["Support", "The tip, and the release notes in a browser. Nothing is locked behind it."],
    ["Other apps", "FamTM, My Hub, SideCut and MeasureT - the apps beside this one."]
  ];

  function helloSeen() { try { return localStorage.getItem("ujournal.hello") === "1"; } catch (e) { return true; } }
  function helloMark() { try { localStorage.setItem("ujournal.hello", "1"); } catch (e) { } }

  // The welcome is marked seen the moment it is shown rather than when it is closed: a phone put
  // down mid-screen should not open on the same screen again tomorrow.
  function showHello() {
    helloMark();
    wnMark();
    S.hello = 1;
    $("hello").innerHTML =
      '<div class="hello-card">' +
      '<div class="hello-mark">UJ</div>' +
      "<h1>" + esc(S.name || "UJournal") + "</h1>" +
      "<p>A journal that keeps every day, on this phone, with nobody to sign in to.</p>" +
      '<div class="hello-list">' +
      "<div><b>Write the day</b><i>A page for each date, with photos and a voice note</i></div>" +
      "<div><b>See it three ways</b><i>The list of entries, a calendar, and the plans ahead</i></div>" +
      "<div><b>Keep it yours</b><i>One file holds every journal. Nothing is uploaded</i></div>" +
      "</div>" +
      '<button id="hellogo" class="hello-go">Show me around</button>' +
      '<button id="helloskip" class="hello-skip">Skip &mdash; I will find my way</button>' +
      "</div>";
    $("hello").classList.remove("hide");
    $("hellogo").onclick = function () { closeHello(); startTour(); };
    $("helloskip").onclick = closeHello;
  }

  function closeHello() {
    S.hello = 0;
    $("hello").classList.add("hide");
  }

  function startTour() { S.tour = 0; drawTour(); }

  function drawTour() {
    var i = S.tour, n = TOUR.length, step = TOUR[i];
    if (!step) { closeTour(); return; }
    var dots = "";
    for (var k = 0; k < n; k++) dots += '<span class="dot' + (k === i ? " on" : "") + '"></span>';
    $("sheet-card").innerHTML = "<h2>Show me around</h2>" +
      '<p class="tcount">Step ' + (i + 1) + " of " + n + "</p>" +
      '<div class="tourstep"><b>' + esc(step.t) + "</b><p>" + esc(step.b) + "</p></div>" +
      '<div class="dots">' + dots + "</div>" +
      '<div class="row">' + (i > 0 ? '<button id="tprev">Back</button>' : "") +
      '<button id="tnext" class="go">' + (i === n - 1 ? "Done" : "Next") + "</button></div>" +
      '<button id="tskip" class="tourskip">Skip the tour</button>';
    $("sheet").classList.remove("hide");
    if ($("tprev")) $("tprev").onclick = function () { S.tour = i - 1; drawTour(); };
    $("tnext").onclick = function () { if (i === n - 1) closeTour(); else { S.tour = i + 1; drawTour(); } };
    $("tskip").onclick = closeTour;
  }

  function closeTour() {
    S.tour = -1;
    $("sheet").classList.add("hide");
    try { localStorage.setItem("ujournal.tour", JOURNAL_PAGE); } catch (e) { }
  }

'''
src = insert_before(
    src,
    "  // ---- settings, in one place and cut into tabs ----",
    TOUR_JS,
    "function drawTour()",
    "the welcome and the tour",
)

# ---- the Guide tab -------------------------------------------------------------------------
src = swap(
    src,
    'var SETTABS = [["journal", "Journal"], ["transfer", "Transfer"], ["updates", "Updates"], ["support", "Support"], ["apps", "Other apps"]];',
    'var SETTABS = [["journal", "Journal"], ["transfer", "Transfer"], ["updates", "Updates"], ["support", "Support"], ["apps", "Other apps"], ["guide", "Guide"]];',
    '["guide", "Guide"]];',
    "the Guide tab",
)

GUIDE_PANE = r'''    } else if (s === "guide") {
      pane = '<button class="sbtn go" data-setdo="tour"><b>Walk through the app</b><i>Five screens: writing, the tabs, the gear, backups, updates</i></button>' +
        '<button class="sbtn" data-setdo="hello"><b>Show the welcome again</b><i>The screen a new phone starts on</i></button>' +
        GUIDE.map(function (g) { return '<div class="gline"><b>' + esc(g[0]) + "</b><i>" + esc(g[1]) + "</i></div>"; }).join("");
'''
src = insert_before(
    src,
    "    } else {\n      pane = SETAPPS.map(",
    GUIDE_PANE,
    'data-setdo="tour"',
    "the Guide pane",
)

src = swap(
    src,
    '        $("sheet").classList.add("hide");\n        if (what === "today") openDay(today());',
    '        // The tour and the welcome put something back in the sheet, so they do not close it first.\n'
    '        if (what === "tour") { S.tour = 0; drawTour(); return; }\n'
    '        if (what === "hello") { showHello(); return; }\n'
    '        $("sheet").classList.add("hide");\n        if (what === "today") openDay(today());',
    'if (what === "tour")',
    "the Guide buttons",
)

# ---- first launch, and the back button -----------------------------------------------------
src = swap(
    src,
    "    // A new screen says what changed in it - once, and only after it has been read.\n"
    "    if (wnSeen() !== JOURNAL_PAGE) showWhatsNew();",
    "    // A new phone starts with the welcome; anyone else gets the notes for a screen they have not\n"
    "    // seen yet. Never both at once: two popups over each other is the opposite of a welcome.\n"
    "    if (!helloSeen()) showHello();\n"
    "    else if (wnSeen() !== JOURNAL_PAGE) showWhatsNew();",
    "if (!helloSeen()) showHello();",
    "the first launch",
)

src = swap(
    src,
    "  window.journalBack = function () {\n    if (S.wn) { closeWhatsNew(); return true; }",
    "  window.journalBack = function () {\n"
    "    if (S.tour >= 0) { closeTour(); return true; }\n"
    "    if (S.hello) { closeHello(); return true; }\n"
    "    if (S.wn) { closeWhatsNew(); return true; }",
    "if (S.tour >= 0) { closeTour();",
    "the back button over the welcome and the tour",
)

# ---- notes ---------------------------------------------------------------------------------
notes = NOTES.read_text(encoding="utf-8")
if f"## {VERSION}" not in notes:
    section = (
        f"## {VERSION} — November 6, 2026\n\n"
        "**A welcome, a tour, and a Guide under the gear.**\n\n"
        "- A first launch opens on a welcome: three lines on what the journal is for, and two buttons,\n"
        "  Show me around and Skip. Shown once, marked seen when it appears rather than when it closes.\n"
        "- The tour is five steps - writing a day, the three tabs, the gear, backups and updates - with\n"
        "  Next, Back and Skip. It draws in the settings sheet, so it uses the same card as the rest of\n"
        "  the app and closes without leaving the journal anywhere else.\n"
        "- Settings gains a Guide tab: the same tour, the welcome, and every feature in one list.\n"
        "- What's New waits behind the welcome, so a new phone is not met by two popups at once.\n\n"
    )
    i = notes.find("## ")
    notes = notes[:i] + section + notes[i:] if i >= 0 else notes + "\n" + section
    print("  added:   PATCH_NOTES.md section")
else:
    print("  already: PATCH_NOTES.md section")

# ---- write ---------------------------------------------------------------------------------
if CHECK:
    print(f"page: {len(src)} bytes (version {VERSION}, welcome present: {'function showHello()' in src})")
    print("check only - nothing written")
else:
    PAGE.write_text(src, encoding="utf-8")
    NOTES.write_text(notes, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)}: {len(src)} bytes")
