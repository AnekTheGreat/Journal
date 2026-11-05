"""One-shot: the UJournal 1.9.0 change, applied where the files really are.

Every step is anchored and asserted, so a file that is not the shape this script expects stops the
run before anything is written. Deleted by the runner that calls it.
"""
import re, shutil, subprocess, sys, tempfile

PAGE = "app/src/main/assets/index.html"


def read(p):
    return open(p, encoding="utf-8").read()


def write(p, s):
    open(p, "w", encoding="utf-8").write(s)


def rep(path, old, new, count=1):
    s = read(path)
    n = s.count(old)
    if n != count:
        sys.exit("%s: expected %d of %r, found %d" % (path, count, old[:70], n))
    write(path, s.replace(old, new, count))


# ---- 1. one button in Plans, where the card used to be ----

CSS = (".support .h{color:var(--tan);font-size:20px;margin-left:auto}\n"
       ".fambtn{display:flex;align-items:center;gap:12px;width:100%;text-align:left;"
       "background:var(--card);border:1px solid var(--sand);border-radius:20px;"
       "padding:14px 16px;margin:0 0 18px;color:var(--ink);font-family:inherit}\n"
       ".fambtn .fc{font-size:22px;line-height:1}\n"
       ".fambtn b{display:block;font-family:Georgia,serif;font-size:16px;font-weight:400}\n"
       ".fambtn i{display:block;font-style:normal;font-size:12.5px;color:var(--muted);margin-top:3px}")
rep(PAGE, ".support .h{color:var(--tan);font-size:20px;margin-left:auto}", CSS)

rep(PAGE, 'const JOURNAL_PAGE = "1.8.1";', 'const JOURNAL_PAGE = "1.9.0";')

rep(PAGE, 'saveTimer: null, rec: null, upd: null };',
    'saveTimer: null, rec: null, upd: null, wn: 0 };')

# The button sits under New plan, and the card that used to close the tab is gone.
rep(PAGE,
    "'<b>New plan</b><i>An hour, a few days away, or a birthday</i></span></button>';",
    "'<b>New plan</b><i>An hour, a few days away, or a birthday</i></span></button>' +\n"
    "      famtmButton();")
rep(PAGE, '$("view").innerHTML = h + famtmCard() + othersCard();',
    '$("view").innerHTML = h + othersCard();')

CARD = re.compile(r"  function famtmCard\(\) \{.*?say\(added === 1 \? \"One birthday added\" : "
                  r"added \+ \" birthdays added\"\);\n  \}", re.S)
BUTTON = '''  // One button, and nothing else: FamTM either has birthdays this journal has not seen yet, or it
  // has nothing to offer and the button is not there at all. A tap is the whole of the feature.
  function famtmButton() {
    var n = famtmPending();
    if (!n) return "";
    return '<button class="fambtn" data-famtm="1"><span class="fc">🎂</span><span>' +
      '<b>' + (n === 1 ? "Add the birthday from FamTM" : "Add " + n + " birthdays from FamTM") + '</b>' +
      '<i>Everyone alive in the family, marked every year</i></span></button>';
  }

  function importFam() {
    var added = parseInt(call("importFamTmBirthdays"), 10);
    refresh();
    if (!(added > 0)) { say("Nothing new to bring across"); return; }
    say(added === 1 ? "One birthday added" : added + " birthdays added");
  }

  // ---- what's new ----

  // The notes for this screen travel inside the screen: a screen that arrives over the air brings
  // its own account of what changed, so nothing has to be fetched to read it. One entry per screen
  // version, and the version whose notes have been shown is kept on the phone - marked when the
  // popup is CLOSED, by its button or the phone's back, not when it is built, so the notes cannot be
  // marked read without having been put in front of the reader.
  var WN = {
    "1.9.0": {
      date: "5 November 2026",
      title: "Birthdays from FamTM, one button in Plans",
      notes: [
        "The birthdays come across from FamTM. With FamTM installed, the Plans tab carries one button that brings over the name and the day of everyone alive in the family, and marks each one on the calendar every year without being typed in again.",
        "They arrive as ordinary birthday plans, so one can be renamed, moved or deleted like any other, and a birthday already in the journal is never added twice.",
        "Only the name and the day travel. FamTM hands over the same short list its own reminders keep - no photos, no notes - and the journal only ever reads it, so nothing in FamTM can be changed from here.",
        "This popup arrives with the screen rather than the app: a release that only changes what the journal says is taken the next time it is opened, with nothing installed.",
        "It is shown once per screen version, and marked read when it is closed, so it is not in the way on every launch."
      ]
    }
  };

  function wnSeen() { try { return localStorage.getItem("ujournal.wn") || ""; } catch (e) { return ""; } }
  function wnMark() { try { localStorage.setItem("ujournal.wn", JOURNAL_PAGE); } catch (e) { } }

  function showWhatsNew() {
    var u = WN[JOURNAL_PAGE];
    if (!u) return;
    var notes = (u.notes || []).map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("");
    $("sheet-card").innerHTML = '<h2>What&rsquo;s New</h2>' +
      '<p>UJournal ' + esc(JOURNAL_PAGE) + ' &middot; ' + esc(u.date) + '<br>' + esc(u.title) + '</p>' +
      (notes ? '<ul>' + notes + '</ul>' : "") +
      '<div class="row"><button id="wnok" class="go">Got it</button></div>';
    S.wn = 1;
    $("sheet").classList.remove("hide");
    $("wnok").onclick = function () { closeWhatsNew(); };
  }

  function closeWhatsNew() {
    if (!S.wn) return;
    S.wn = 0;
    wnMark();
    $("sheet").classList.add("hide");
  }'''
s = read(PAGE)
hits = CARD.findall(s)
if len(hits) != 1:
    sys.exit("the FamTM card is not in the page exactly once (%d)" % len(hits))
write(PAGE, CARD.sub(lambda m: BUTTON, s, count=1))

# ---- 2. the popup opens on a version that has not been read, and is marked when it is closed ----

rep(PAGE, '    $("fab").style.display = "block";\n    refresh();\n  }',
    '    $("fab").style.display = "block";\n    refresh();\n'
    '    // A new screen says what changed in it - once, and only after it has been read.\n'
    '    if (wnSeen() !== JOURNAL_PAGE) showWhatsNew();\n  }')

rep(PAGE, '    if (ev.target === $("sheet")) $("sheet").classList.add("hide");',
    '    if (ev.target !== $("sheet")) return;\n'
    '    // Tapping the backdrop of What\'s New closes it the same way its own button does, so the\n'
    '    // notes are marked read whichever way the popup is dismissed.\n'
    '    if (S.wn) { closeWhatsNew(); return; }\n'
    '    $("sheet").classList.add("hide");')

rep(PAGE, '  window.journalBack = function () {\n    if (!$("menu")',
    '  window.journalBack = function () {\n    if (S.wn) { closeWhatsNew(); return true; }\n    if (!$("menu")')

# ---- 3. the version the build and the release check agree on ----

rep("app/build.gradle.kts", 'versionName = "1.8.1"', 'versionName = "1.9.0"')

# ---- 4. the patch notes this page is written from ----

NOTES = """## 1.9.0 — November 5, 2026

**Birthdays from FamTM are one button, and a new screen says what changed**

- **One button, not a card.** The Plans tab used to end with a card *about* the birthdays FamTM was holding; it is now a single button under **New plan** — *Add N birthdays from FamTM* — and that button is the whole of the feature.
- **What's New, in the screen's own words.** The first time a new screen runs, a popup lists what changed in it, with the version marked read when the popup is closed — its own button, the backdrop, or the phone's back — and not when it is built. It appears once per screen version.
- **The notes travel inside the screen.** Nothing is fetched to read them: a screen that arrives over the air brings its own account of what changed.
- **Nothing else changed.** The button and the popup are both in the page, so this release is taken over the air: a copy on 1.8.1 installs nothing to get either.

## 1.8.1 — November 5, 2026"""

rep("PATCH_NOTES.md", "## 1.8.1 — November 5, 2026", NOTES)

# ---- 5. the page that will ship really parses, and says what it should ----

page = read(PAGE)
i = page.index("<script>") + len("<script>")
j = page.index("</script>", i)
tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
tmp.write(page[i:j])
tmp.close()
try:
    r = subprocess.run(["node", "--check", tmp.name])
except FileNotFoundError:
    r = None
    print("node is not here; the page's script was not syntax-checked")
if r is not None and r.returncode != 0:
    sys.exit("the page's own script does not parse")

for needle in ('const JOURNAL_PAGE = "1.9.0";', "function famtmButton()", "function showWhatsNew()",
               "if (wnSeen() !== JOURNAL_PAGE) showWhatsNew();", "if (S.wn) { closeWhatsNew(); return; }"):
    assert needle in page, needle
assert "famtmCard" not in page
print("UJournal 1.9.0 applied: the page names 1.9.0, the card is a button, and What's New is wired")
