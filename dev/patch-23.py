#!/usr/bin/env python3
"""UJournal 2.3 - videos play here, and a quiet update stops interrupting.

    python3 dev/patch-23.py            # apply
    python3 dev/patch-23.py --check    # verify only, writes nothing

Two things a reader runs into every day:

  * an attached video could only be watched if another app on the phone claimed the file. On a
    phone with nothing that plays MP4s - or a player that refuses a private file - the tap was a
    toast and nothing else. 2.3 draws the player in the page itself: a video opens full screen over
    the day, with the phone's own controls, and still offers "Open in another app";

  * the journal opened, a silent check finished a second later, and the screen reloaded underneath
    the first sentence being typed - then the fresh screen put What's New over the keyboard. A
    quiet update now writes the page and waits for the next start, which is what the app has always
    said it does. An update asked for by hand still swaps straight away.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "app/src/main/assets/index.html"
GRADLE = "app/build.gradle.kts"
NOTES = "PATCH_NOTES.md"
ACTIVITY = "app/src/main/java/app/ujournal/MainActivity.kt"

V = "2.3"
OLD = "2.2"

WN_NEW = '''  var WN = {
    "2.3": {
      date: "9 November 2026",
      title: "Videos play, and nothing reloads under your hands",
      notes: [
        "A video attached to a day now plays inside the journal: tap it and it opens full screen over the page, with the phone's own play and pause. It used to be handed to another app, which on a phone with no video player meant a toast and a file nobody could watch. Open in another app is still there under the player.",
        "The screen no longer restarts while you are writing. A check that finished a second after launch used to load the new screen under the keyboard and then put this sheet on top of it; a quiet update now waits for the next time the journal opens, and an update you ask for still applies at once.",
        "What's New waits for the day to close if a day is already open, rather than landing on the first sentence."
      ]
    },
'''

CSS_NEW = '''#vid{position:fixed;inset:0;background:#000;z-index:70;display:flex;align-items:center;justify-content:center}
#vid.hide{display:none}
#vid video{width:100%;max-height:100%;background:#000}
#vid .vclose{position:absolute;top:14px;right:14px;background:rgba(255,255,255,.16);color:#fff;border:0;border-radius:16px;padding:9px 16px;font-family:inherit;font-size:14px}
#vid .vopen{position:absolute;right:14px;bottom:16px;background:none;border:0;color:#e9e2d6;font-family:inherit;font-size:13px;text-decoration:underline;padding:8px}
#vid .vname{position:absolute;left:16px;right:130px;bottom:22px;color:#e9e2d6;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
'''

OVERLAY_HTML = '''<div id="vid" class="hide"><video id="vp" controls playsinline preload="metadata"></video><button class="vclose" id="vclose">Done</button><div class="vname" id="vname"></div><button class="vopen" id="vopen">Open in another app</button></div>
'''

VIDEO_JS = '''  // ---- playing a video, here ----

  // 2.3 - A VIDEO PLAYS WHERE IT IS. A tile used to hand the file to whatever app claimed to open it,
  // and that was the end of the story when nothing on the phone did: a toast, and an attachment nobody
  // could watch. The journal has the file and the page can draw a player, so a video opens full screen
  // over the day with the phone's own controls and nothing installed. Open in another app stays one
  // tap away for anyone who wants it.
  function playVideo(path, name) {
    var v = $("vp");
    if (!v) return;
    $("vname").textContent = name || "Video";
    try { v.pause(); } catch (e) { }
    v.src = fileUrl(path);
    $("vid").classList.remove("hide");
    try { v.currentTime = 0; } catch (e) { }
    var p = v.play();
    if (p && p.catch) p.catch(function () { });
  }

  function closeVideo() {
    var v = $("vp");
    if (!v) return;
    try { v.pause(); } catch (e) { }
    v.removeAttribute("src");
    try { v.load(); } catch (e) { }
    $("vid").classList.add("hide");
  }

  $("vclose").onclick = function () { closeVideo(); };
  $("vopen").onclick = function () {
    var n = $("vname").textContent;
    closeVideo();
    if (n) call("open", S.day, n);
  };

  // ---- attaching ----
'''

ASK_JS = '''  // 2.3 - NOT OVER SOMETHING BEING WRITTEN. The notes belong to the moment the journal opens. If a day
  // is already open, or a field has the keyboard, they wait for the day to be closed instead of
  // landing on the first sentence.
  function askWhatsNew() {
    var a = document.activeElement;
    var busy = S.day || (a && /^(INPUT|TEXTAREA)$/.test(a.tagName));
    if (busy) { S.wnWait = 1; return; }
    showWhatsNew();
  }

'''

NOTES_MD = '''## 2.3 - 9 November 2026

Videos play in the journal, and a quiet update stops interrupting.

- **A video opens where it is.** Tapping one used to hand the file to another app; on a phone with
  nothing that plays MP4s that was a toast and an attachment nobody could watch. It now opens full
  screen over the day with the phone's own controls, and **Open in another app** is still one tap
  away.
- **No more blinking under the first sentence.** A check that finished just after launch used to
  load the new screen underneath the keyboard, and the fresh screen then put What's New over the
  words being typed. A quiet update now waits for the next start, which is what the app always
  promised; an update you ask for still swaps straight away.
- **The notes wait for the day.** If a day is open, or a field has the keyboard, What's New arrives
  when the day is closed rather than on top of it.

'''


def path(p):
    return os.path.join(ROOT, p)


def read(p):
    return open(path(p), encoding="utf-8").read()


def write(p, s):
    open(path(p), "w", encoding="utf-8").write(s)


def applied():
    return ('const JOURNAL_PAGE = "%s";' % V) in read(PAGE)


def sub(text, old, new, why):
    if text.count(old) != 1:
        sys.exit(why)
    return text.replace(old, new, 1)


def check():
    page = read(PAGE)
    gradle = read(GRADLE)
    notes = read(NOTES)
    activity = read(ACTIVITY)
    probes = [
        ('const JOURNAL_PAGE = "%s";' % V in page, "the page does not say %s" % V),
        ('    "%s": {' % V in page, "What's New has no %s entry" % V),
        ('<div id="vid" class="hide">' in page, "there is no player in the page"),
        ('function playVideo(path, name) {' in page, "playVideo is missing"),
        ('function closeVideo() {' in page, "closeVideo is missing"),
        ('data-vid="' in page, "a video tile does not carry its file"),
        ('if (vpath !== null) { playVideo(vpath' in page, "a video tap does not open the player"),
        ('if (!$("vid").classList.contains("hide")) { closeVideo(); return true; }' in page,
         "back does not close the player"),
        ("function askWhatsNew() {" in page, "the notes are not gated while a day is open"),
        ("else if (wnIsNewer()) askWhatsNew();" in page, "boot still opens the notes directly"),
        ('const JOURNAL_PAGE = "%s";' % OLD not in page, "the page still says %s" % OLD),
        ('versionName = "%s"' % V in gradle, "build.gradle.kts does not carry %s" % V),
        ("## %s " % V in notes, "PATCH_NOTES has no %s entry" % V),
        ("if (quiet) {" in activity, "a quiet update still swaps the screen"),
        ("UJournal $version opens next time" in activity, "a quiet update says nothing"),
        ("private fun editing(and: (Boolean) -> Unit)" in activity, "there is no typing guard"),
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
    print("%s: the player is in the page, and a quiet update waits for the next start" % V)


def main():
    if applied():
        check()
        print("already applied - nothing written")
        return

    page = read(PAGE)

    # ---- the page names itself 2.3, and knows what changed -----------------
    page = sub(page, 'const JOURNAL_PAGE = "%s";' % OLD,
               'const JOURNAL_PAGE = "%s";' % V, "the page is not where it was expected")
    page = sub(page, "  var WN = {\n", "  var WN = {\n" + WN_NEW.split("  var WN = {\n", 1)[1],
               "there is no list of notes to add to")

    # ---- a player, full screen, over the day ------------------------------
    page = sub(page, ".dots .dot.on{background:var(--tan);width:18px}\n",
               ".dots .dot.on{background:var(--tan);width:18px}\n" + CSS_NEW,
               "the stylesheet is not where it was expected")
    page = sub(page, '<div id="say" class="hide"></div>\n',
               OVERLAY_HTML + '<div id="say" class="hide"></div>\n',
               "the body is not where it was expected")

    # a video tile says which file it is, so a tap can play it here
    page = sub(page,
               """      h += '<div class="tile" data-open="' + esc(a.name) + '">';\n""",
               """      var vp = /^video\\//.test(mime) ? ' data-vid="' + esc(a.path || "") + '"' : "";\n"""
               """      h += '<div class="tile" data-open="' + esc(a.name) + '"' + vp + '">';\n""",
               "the attachment tile is not where it was expected")

    page = sub(page,
               """      var o = ev.target.closest("[data-open]");\n"""
               """      if (o) call("open", S.day, o.getAttribute("data-open"));\n""",
               """      var o = ev.target.closest("[data-open]");\n"""
               """      if (o) {\n"""
               """        var vpath = o.getAttribute("data-vid");\n"""
               """        if (vpath !== null) { playVideo(vpath, o.getAttribute("data-open")); return; }\n"""
               """        call("open", S.day, o.getAttribute("data-open"));\n"""
               """      }\n""",
               "the attachment tap is not where it was expected")

    page = sub(page, "  // ---- attaching ----\n", VIDEO_JS,
               "the attaching section is not where it was expected")

    # ---- the notes never land on the keyboard ----------------------------
    page = sub(page, "    else if (wnIsNewer()) showWhatsNew();",
               "    else if (wnIsNewer()) askWhatsNew();",
               "boot does not open the notes where it was expected")
    page = sub(page, "  function pickTab(n) {", ASK_JS + "  function pickTab(n) {",
               "pickTab is not where it was expected")
    page = sub(page,
               """    $("fab").style.display = "block";\n    refresh();\n    return was;\n  }\n""",
               """    $("fab").style.display = "block";\n    refresh();\n"""
               """    if (S.wnWait) { S.wnWait = 0; askWhatsNew(); }\n    return was;\n  }\n""",
               "closeDay is not where it was expected")

    # ---- back closes the player before anything else ---------------------
    page = sub(page,
               """  window.journalBack = function () {\n    if (S.tour >= 0)""",
               """  window.journalBack = function () {\n"""
               """    if (!$("vid").classList.contains("hide")) { closeVideo(); return true; }\n"""
               """    if (S.tour >= 0)""",
               "journalBack is not where it was expected")

    write(PAGE, page)

    # ---- the shell: a quiet update waits, and a video still opens elsewhere
    activity = read(ACTIVITY)
    activity = sub(activity,
                   """            runOnUiThread {\n                if (saved) {\n                    loadPage()\n"""
                   """                    main.postDelayed(\n"""
                   """                        { eval("JR&&JR.toast('Updated to $version')") },\n"""
                   """                        if (quiet) 700 else 1500\n"""
                   """                    )\n                } else {\n""",
                   """            runOnUiThread {\n                if (saved) {\n"""
                   """                    if (quiet) {\n"""
                   """                        // 2.3 - A QUIET UPDATE WAITS FOR THE NEXT START. Loading the page here is what\n"""
                   """                        // made the journal blink and begin again a second after it opened - the moment\n"""
                   """                        // someone had started to type - and the fresh screen then put its What's New\n"""
                   """                        // sheet over the keyboard. The file is already in place, so the next start draws\n"""
                   """                        // it: nothing on screen is replaced under a pen.\n"""
                   """                        editing { busy ->\n"""
                   """                            if (!busy) eval("JR&&JR.toast('UJournal $version opens next time')")\n"""
                   """                        }\n"""
                   """                    } else {\n"""
                   """                        loadPage()\n"""
                   """                        main.postDelayed({ eval("JR&&JR.toast('Updated to $version')") }, 1500)\n"""
                   """                    }\n                } else {\n""",
                   "the page swap in write() is not where it was expected")

    activity = sub(activity,
                   "    /**\n     * Fetch the page a release published and put it in place.",
                   "    /**\n"
                   "     * 2.3 - Is a day open? Only the page knows, so it is asked. A quiet update uses this to\n"
                   "     * stay silent while someone is writing: the file is already saved, so saying so can wait.\n"
                   "     */\n"
                   "    private fun editing(and: (Boolean) -> Unit) {\n"
                   "        if (!::web.isInitialized) {\n"
                   "            and(false)\n"
                   "            return\n"
                   "        }\n"
                   "        web.evaluateJavascript(\"(window.journalEditing&&journalEditing())?'y':'n'\") { answer ->\n"
                   "            and(answer != null && answer.contains(\"y\"))\n"
                   "        }\n"
                   "    }\n\n"
                   "    /**\n     * Fetch the page a release published and put it in place.",
                   "takePage is not where it was expected")

    activity = sub(activity, "import android.content.Intent\n",
                   "import android.content.ClipData\nimport android.content.Intent\n",
                   "the imports are not where they were expected")

    activity = sub(activity,
                   """        val i = Intent(Intent.ACTION_VIEW)\n"""
                   """            .setDataAndType(uri, a.mime)\n"""
                   """            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)\n""",
                   """        val i = Intent(Intent.ACTION_VIEW)\n"""
                   """            .setDataAndType(uri, a.mime)\n"""
                   """            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)\n"""
                   """        // 2.3 - the grant travels with the file for players that read the clip, not the intent.\n"""
                   """        i.clipData = ClipData.newRawUri(a.name, uri)\n""",
                   "openAttachment is not where it was expected")
    write(ACTIVITY, activity)

    # ---- the build carries the same number -------------------------------
    gradle = read(GRADLE)
    gradle = sub(gradle, 'versionName = "%s"' % OLD, 'versionName = "%s"' % V,
                 "build.gradle.kts does not name %s" % OLD)
    write(GRADLE, gradle)

    # ---- the release notes, read by release.yml --------------------------
    notes = read(NOTES)
    if ("## %s " % V) not in notes:
        write(NOTES, NOTES_MD + notes)

    check()
    print("UJournal %s applied to the page, the shell, build.gradle.kts and PATCH_NOTES.md" % V)


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        main()
