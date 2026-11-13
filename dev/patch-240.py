#!/usr/bin/env python3
"""
UJournal 2.4 - room to write.

Two things were wrong with writing a day down, and both were in the screen:

  1. The writing box was a fixed 200px tall whatever was in it. A short entry left a band of empty
     screen under it - the gap you have to write across - and a long one scrolled inside a page
     that was already scrolling.
  2. The keyboard was never mentioned. From Android 15 the system draws the app edge to edge and
     lays the keys over it instead of shrinking it, so the line being typed finished underneath
     them. `visualViewport` is the part of the screen the keys are not using, so what it loses is
     handed to the day as its height, and the words end above the keys.

Run twice: the second run changes nothing. `--check` answers whether the tree already has it.
"""
import io
import sys

PAGE = 'app/src/main/assets/index.html'
GRADLE = 'app/build.gradle.kts'
NOTES = 'PATCH_NOTES.md'

VERSION = '2.4'

# ---- the screen -------------------------------------------------------------------------------
OLD_BODY = '#day-body{flex:1;overflow-y:auto;padding:0 20px 120px}'
NEW_BODY = (
    '/* 2.4 - the page ends where the writing ends. A fixed 120px of padding under the note was a\n'
    '   band of empty screen below every entry; it is the room the last line needs and nothing more,\n'
    '   and the keys are kept out of the page entirely (see watchKeys below). */\n'
    '#day-body{flex:1;overflow-y:auto;padding:0 20px 22px}'
)

OLD_TA = ('textarea.b{width:100%;min-height:200px;border:0;background:none;font-size:17px;'
          'line-height:1.55;color:var(--ink);padding:6px 0;outline:none;resize:none;font-family:inherit}')
NEW_TA = (
    'textarea.b{display:block;width:100%;min-height:0;height:auto;overflow:hidden;border:0;'
    'background:none;font-size:17px;line-height:1.55;color:var(--ink);padding:6px 0 10px;'
    'outline:none;resize:none;font-family:inherit}\n'
    '/* 2.4 - while the keys are up the note keeps a band of air above them, so the line being typed\n'
    '   is never the line against the keyboard. */\n'
    'body.keys #day-body{padding-bottom:max(72px,16vh)}'
)

OLD_BIND = """    $("t").addEventListener("input", touchSave);
    $("b").addEventListener("input", touchSave);
    $("t").addEventListener("blur", saveNow);
    $("b").addEventListener("blur", saveNow);
    bindAtts();
  }"""

NEW_BIND = """    $("t").addEventListener("input", touchSave);
    $("b").addEventListener("input", touchSave);
    $("b").addEventListener("input", growBody);
    $("t").addEventListener("blur", saveNow);
    $("b").addEventListener("blur", saveNow);
    bindAtts();
    growBody();
    watchKeys();
  }

  /* ---- 2.4: room to write ----
     The writing box is as tall as the words in it, the page ends just under the last line, and
     while the keys are up the day is exactly the part of the screen they are not using. */
  function growBody() {
    var b = $("b");
    if (!b) return;
    b.style.height = "auto";
    b.style.height = Math.max(0, b.scrollHeight) + "px";
  }
  function keysClear() {
    var b = $("b"), body = $("day-body");
    if (!b || !body) return;
    var seen = window.visualViewport
      ? window.visualViewport.height + (window.visualViewport.offsetTop || 0)
      : window.innerHeight;
    var r = b.getBoundingClientRect();
    if (r.bottom > seen - 24) body.scrollTop += r.bottom - seen + 56;
  }
  function watchKeys() {
    var vv = window.visualViewport;
    var day = $("day");
    if (!vv || !day) return;
    function apply() {
      var open = S.day && !day.classList.contains("hide");
      var cover = 0;
      if (open && (!vv.scale || vv.scale < 1.01)) {
        cover = Math.round(window.innerHeight - vv.height - (vv.offsetTop || 0));
        if (cover < 60) cover = 0;
      }
      document.body.classList.toggle("keys", cover > 0);
      day.style.height = cover > 0 ? (vv.height + (vv.offsetTop || 0)) + "px" : "";
      if (cover > 0) keysClear();
      growBody();
    }
    if (!watchKeys.wired) {
      watchKeys.wired = 1;
      vv.addEventListener("resize", apply);
      vv.addEventListener("scroll", apply);
      document.addEventListener("focusin", function () { setTimeout(apply, 90); });
      document.addEventListener("focusout", function () { setTimeout(apply, 90); });
    }
    apply();
  }"""

OLD_CLOSE = """  function closeDay() {
    saveNow();"""
NEW_CLOSE = """  function closeDay() {
    saveNow();
    if ($("day")) $("day").style.height = "";
    document.body.classList.remove("keys");"""

OLD_WN = '  var WN = {\n    "2.3": {'
NEW_WN = '''  var WN = {
    "2.4": {
      date: "13 November 2026",
      title: "The page ends where the writing does",
      notes: [
        "The day you are writing no longer sits in a box of empty screen. The box was a fixed height whatever was in it: a short entry left a band of nothing under it, and a long one scrolled inside a page that was already scrolling. It is now as tall as the words in it, and the page ends just under the last line.",
        "The keyboard is kept out of the page. From Android 15 the phone lays the keys over the app instead of shortening it, so the line being typed finished underneath them. While the keys are up the day ends above them, with a band of air under the line you are on.",
        "This one is in the screen, so it arrives over the air the next time the journal opens - nothing to install."
      ]
    },
    "2.3": {'''

NOTES_HEAD = '''## 2.4 - 13 November 2026

The page ends where the writing does, and the keys stay out of it.

- **No empty box under the note.** The writing box was a fixed height whatever was in it - a short
  day left a band of empty screen below it, a long one scrolled inside a page that was already
  scrolling. It is now as tall as the words in it, and the page ends just under the last line.
- **The keyboard no longer covers the words.** From Android 15 the phone lays the keys over the app
  instead of shortening it, so the line being typed finished underneath them. While the keys are up
  the day is as tall as the part of the screen they are not using, with a band of air under the
  line you are on.
- **Nothing to install.** Both of these are in the screen, which arrives over the air the next time
  the journal opens.

'''


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def apply(page):
    """Each edit is done only if it is not there already, so a second run is a no-op."""
    if NEW_BODY not in page:
        page = page.replace(OLD_BODY, NEW_BODY, 1)
    if 'body.keys #day-body' not in page:
        page = page.replace(OLD_TA, NEW_TA, 1)
    if 'function watchKeys()' not in page:
        page = page.replace(OLD_BIND, NEW_BIND, 1)
        page = page.replace(OLD_CLOSE, NEW_CLOSE, 1)
    if '"2.4": {' not in page:
        page = page.replace(OLD_WN, NEW_WN, 1)
    page = page.replace('const JOURNAL_PAGE = "2.3";', 'const JOURNAL_PAGE = "%s";' % VERSION, 1)
    return page


def main():
    page = read(PAGE)
    gradle = read(GRADLE)
    notes = read(NOTES)

    new_page = apply(page)
    new_gradle = gradle.replace('versionName = "2.3"', 'versionName = "%s"' % VERSION, 1)
    if new_gradle == gradle and 'versionName = "%s"' % VERSION not in gradle:
        sys.exit('FATAL: build.gradle.kts names neither 2.3 nor %s' % VERSION)
    new_notes = notes if '## %s' % VERSION in notes else NOTES_HEAD + notes

    if '--check' in sys.argv:
        problems = []
        if new_page != page:
            problems.append('%s does not have the new writing layout' % PAGE)
        if new_gradle != gradle:
            problems.append('%s does not name %s' % (GRADLE, VERSION))
        if new_notes != notes:
            problems.append('%s has no %s entry' % (NOTES, VERSION))
        for p in problems:
            print('not applied: ' + p)
        sys.exit(1 if problems else 0)

    if new_page == page and new_gradle == gradle and new_notes == notes:
        print('already applied: nothing changed')
        return
    write(PAGE, new_page)
    write(GRADLE, new_gradle)
    write(NOTES, new_notes)
    print('applied %s: the writing box is as tall as the words, and the keys are outside the page'
          % VERSION)


if __name__ == '__main__':
    main()
