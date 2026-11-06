#!/usr/bin/env python3
"""UJournal 1.9.10 - My Hub comes off the Other apps list.

Every row on that list is a store listing, and the shell opens each one in the browser. My Hub has no
store page, so a tap went somewhere that could not install anything. It comes off both lists the
journal keeps - the card's and the settings tab's - off the Guide line that describes it, and the
page says 1.9.10.

Idempotent: every change is guarded by the text that proves it is already there.
  python3 dev/patch-1910.py           apply
  python3 dev/patch-1910.py --check   report only
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "app" / "src" / "main" / "assets" / "index.html"
NOTES = ROOT / "PATCH_NOTES.md"
GRADLE = ROOT / "app" / "build.gradle.kts"
VERSION = "1.9.10"
OLD = "1.9.9"

CHECK = "--check" in sys.argv


def swap(src, old, new, marker, what):
    if marker in src:
        print(f"  already: {what}")
        return src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"!! {what}: text appears {n} times, expected 1")
    print(f"  changed: {what}")
    return src.replace(old, new, 1)


src = PAGE.read_text(encoding="utf-8")

src = swap(
    src,
    f'const JOURNAL_PAGE = "{OLD}";',
    f'const JOURNAL_PAGE = "{VERSION}";',
    f'const JOURNAL_PAGE = "{VERSION}";',
    f"page version -> {VERSION}",
)

# ---- the row, in both lists the journal keeps ----------------------------------------------
row = '    ["myhub", "My Hub", "One screen for the apps you use most"],\n'
if '"myhub"' not in src:
    print("  already: My Hub off both lists")
else:
    n = src.count(row)
    if n != 2:
        raise SystemExit(f"!! My Hub: the row appears {n} times, expected 2 (card list and settings)")
    src = src.replace(row, "", 2)
    print("  changed: My Hub off both lists")

# ---- the two lines of prose that named it --------------------------------------------------
src = swap(
    src,
    "'<div class=\"s2\">FamTM, My Hub, SideCut and MeasureT.</div></div><div class=\"h\">›</div></div>';",
    "'<div class=\"s2\">FamTM, SideCut and MeasureT.</div></div><div class=\"h\">›</div></div>';",
    "'<div class=\"s2\">FamTM, SideCut and MeasureT.</div></div>",
    "the card that leads to the list",
)

src = swap(
    src,
    "var h = '<h2>Other apps</h2><p>Four more, made the same way and free the same way.</p>';",
    "var h = '<h2>Other apps</h2><p>Three more, made the same way and free the same way.</p>';",
    "<p>Three more, made the same way and free the same way.</p>",
    "the line above the list",
)

# ---- the Guide's line for that tab ---------------------------------------------------------
src = swap(
    src,
    '["Other apps", "FamTM, My Hub, SideCut and MeasureT - the apps beside this one."]',
    '["Other apps", "FamTM, SideCut and MeasureT - the apps beside this one."]',
    '["Other apps", "FamTM, SideCut and MeasureT - the apps beside this one."]',
    "the Guide line for Other apps",
)

# ---- what's new ----------------------------------------------------------------------------
wn = (
    f'    "{VERSION}": {{\n'
    '      date: "6 November 2026",\n'
    '      title: "My Hub is off the Other apps list",\n'
    "      notes: [\n"
    '        "Other apps, and the card that leads to it, list the three apps beside this one that a tap can install: FamTM, SideCut and MeasureT. My Hub has no store page, so tapping it opened somewhere that could not install anything.",\n'
    '        "The Guide\'s line for Other apps says the same three.",\n'
    '        "This one is in the page: it arrives the next time the app opens, with nothing to install."\n'
    "      ]\n"
    "    },\n"
)
if f'"{VERSION}": {{\n      date:' in src:
    print("  already: what's new entry")
else:
    src = swap(src, "  var WN = {\n", "  var WN = {\n" + wn, f'"{VERSION}": {{\n      date:', "what's new entry")

# ---- notes ---------------------------------------------------------------------------------
notes = NOTES.read_text(encoding="utf-8")
heading = f"## {VERSION}"
if heading not in notes:
    section = (
        f"{heading} — November 6, 2026\n\n"
        "**My Hub is off the Other apps list.**\n\n"
        "- Other apps, and the card in Support that leads to it, list the three apps beside this one\n"
        "  that a tap can install: FamTM, SideCut and MeasureT. My Hub has no store page, so a tap on\n"
        "  it went somewhere that could not install anything.\n"
        "- The Guide's line for Other apps says the same three.\n"
        "- This one is in the page: it arrives the next time the app opens, with nothing to install.\n\n"
    )
    i = notes.find("## ")
    notes = notes[:i] + section + notes[i:] if i >= 0 else notes + "\n" + section
    print("  added:   PATCH_NOTES.md section")
else:
    print("  already: PATCH_NOTES.md section")

# ---- the version the APK carries -----------------------------------------------------------
# release.yml refuses to publish when build.gradle.kts, the page and the tag disagree, so all three
# move together. The version code is derived from the name in that file, so the name is the only edit.
gradle = GRADLE.read_text(encoding="utf-8")
old_name = f'versionName = "{OLD}"'
if f'versionName = "{VERSION}"' in gradle:
    print("  already: build.gradle.kts version")
else:
    if gradle.count(old_name) != 1:
        raise SystemExit("!! build.gradle.kts: the version line is not the one expected")
    gradle = gradle.replace(old_name, f'versionName = "{VERSION}"', 1)
    print(f"  changed: build.gradle.kts version -> {VERSION}")

# ---- write ---------------------------------------------------------------------------------
if CHECK:
    print(f"page: {len(src)} bytes (version {VERSION}, My Hub present: {'myhub' in src})")
    print("check only - nothing written")
else:
    PAGE.write_text(src, encoding="utf-8")
    NOTES.write_text(notes, encoding="utf-8")
    GRADLE.write_text(gradle, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)}: {len(src)} bytes")
