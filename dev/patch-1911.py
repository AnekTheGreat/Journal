#!/usr/bin/env python3
"""UJournal 1.9.11 - the update that kept coming back.

Moves the version off 1.9.10; remembers a screen that was tried and refused instead of fetching
it again on every check; keeps the welcome, the tour and What's New in the app as well as in the
page; and gives the build number room for every part.

    python3 dev/patch-1911.py            # apply
    python3 dev/patch-1911.py --check    # verify only, writes nothing
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = "app/src/main/assets/index.html"
GRADLE = "app/build.gradle.kts"
ACT = "app/src/main/java/app/ujournal/MainActivity.kt"
BRIDGE = "app/src/main/java/app/ujournal/Bridge.kt"
NOTES = "PATCH_NOTES.md"

V = "1.9.11"
OLD = "1.9.10"

WN_HEAD = '''  var WN = {
    "%s": {''' % OLD

WN_NEW = '''  var WN = {
    "1.9.11": {
      date: "7 November 2026",
      title: "The update that kept coming back",
      notes: [
        "A screen that does not arrive in one piece is not fetched again and again any more. It was asked for on every launch and every return, so an update that the release promised and the file refused looked like an update that never stopped arriving. It is tried once now, and again only when you ask, or when six hours have passed.",
        "The welcome, the tour and these notes are remembered by the app itself as well as by the screen, so a phone that clears the screen's storage no longer meets the same popup on every launch.",
        "No version here ends in ten: 1.9.11 follows 1.9.9. The number the phone compares builds by has room for any part now, so an update always installs over the one before it."
      ]
    },
    "1.9.10": {'''

HELP_OLD = '''  function wnSeen() { try { return localStorage.getItem("ujournal.wn") || ""; } catch (e) { return ""; } }
  function wnMark() { try { localStorage.setItem("ujournal.wn", JOURNAL_PAGE); } catch (e) { } }'''

HELP_NEW = '''  // 1.9.11 - A MARKER THAT OUTLIVES THE SCREEN'S STORAGE. What has been shown once is kept in two
  // places: the page's own storage, where it has always been, and the app, which outlives it. A
  // WebView that loses its storage used to lose the marker with it and put the same popup back on
  // the next launch, which is a popup that never goes away.
  function remembered(key) {
    try { var mine = localStorage.getItem(key); if (mine) return mine; } catch (e) { }
    try { var theirs = call("seen", key); return theirs ? String(theirs) : ""; } catch (e) { return ""; }
  }
  function remember(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { }
    try { call("markSeen", key, value); } catch (e) { }
  }

  function wnSeen() { return remembered("ujournal.wn"); }
  function wnMark() { remember("ujournal.wn", JOURNAL_PAGE); }'''

HELLO_OLD = '''  function helloSeen() { try { return localStorage.getItem("ujournal.hello") === "1"; } catch (e) { return true; } }
  function helloMark() { try { localStorage.setItem("ujournal.hello", "1"); } catch (e) { } }'''

HELLO_NEW = '''  function helloSeen() { return remembered("ujournal.hello") === "1"; }
  function helloMark() { remember("ujournal.hello", "1"); }'''

TOUR_OLD = '    try { localStorage.setItem("ujournal.tour", JOURNAL_PAGE); } catch (e) { }'
TOUR_NEW = '    remember("ujournal.tour", JOURNAL_PAGE);'

GRADLE_OLD = '''        versionName = "1.9.10"
        versionCode = versionName!!.split(".").let { p ->
            p[0].toInt() * 10_000 + p[1].toInt() * 100 + p[2].toInt()
        }'''

GRADLE_NEW = '''        versionName = "1.9.11"
        // Three digits of room per part. The old 10_000 / 100 / 1 layout gave 1.9.100 and 1.11.0
        // the same code, and a code that does not go up is a release Android refuses to install.
        versionCode = versionName!!.split(".").let { p ->
            p[0].toInt() * 1_000_000 + p[1].toInt() * 1_000 + p[2].toInt()
        }'''

OFFER_OLD = '''        if (pageUrl != null && pv != null && Updater.newer(pv, page)) {
            // A screen is a file, not an install: there is nothing to consent to and nothing the
            // phone has to ask, so it is taken as soon as it is found. Waiting to be tapped is most
            // of why an update used to feel slow - the app had found it and then stood still.
            takePage(pageUrl, pv)
            return
        }'''

OFFER_NEW = '''        if (pageUrl != null && pv != null && Updater.newer(pv, page)) {
            // 1.9.11 - ONCE A VERSION, NOT ONCE A CHECK. A screen the release promises and the file
            // refuses is not new information on the next launch, and it is not new information ten
            // minutes later either. Fetching it again on every silent check is what an update that
            // never stops arriving looks like from the sofa: the phone asks, the file disagrees, and
            // the ask is made again before the reader has closed the journal. A version that failed
            // is remembered, and only a check somebody asked for - or six hours - retries it.
            if (!silent || !pageFailedRecently(pv)) {
                // A screen is a file, not an install: there is nothing to consent to and nothing
                // the phone has to ask, so it is taken as soon as it is found. Waiting to be tapped
                // is most of why an update used to feel slow - the app had found it and then stood
                // still.
                takePage(pageUrl, pv)
                return
            }
        }'''

REM_OLD = '''    private fun remember(version: String) {
        getSharedPreferences(UPDATES, MODE_PRIVATE).edit().putString(OFFERED, "app:$version").apply()
    }'''

REM_NEW = '''    private fun remember(version: String) {
        getSharedPreferences(UPDATES, MODE_PRIVATE).edit().putString(OFFERED, "app:$version").apply()
    }

    /**
     * Whether this screen version was tried and refused a short while ago. A failure is worth
     * remembering and worth forgetting: the same page is not asked for on every launch, and a
     * download that broke on a train is still offered once the signal is back.
     */
    private fun pageFailedRecently(version: String): Boolean {
        val p = getSharedPreferences(UPDATES, MODE_PRIVATE)
        if (p.getString(FAILED, "") != "page:$version") return false
        return System.currentTimeMillis() - p.getLong(FAILED_AT, 0L) < RETRY_PAGE
    }

    /** A screen that did not arrive in one piece, and when: what keeps a silent check quiet. */
    private fun rememberPageFailure(version: String) {
        getSharedPreferences(UPDATES, MODE_PRIVATE).edit()
            .putString(FAILED, "page:$version")
            .putLong(FAILED_AT, System.currentTimeMillis())
            .apply()
    }'''

WRITE_OLD = '''                } else if (!quiet) {
                    eval("JR&&JR.toast('That update did not arrive in one piece')")
                }'''

WRITE_NEW = '''                } else {
                    // Remembered before it is reported: the next launch must not ask for the same
                    // file again, whether or not anyone saw the toast.
                    rememberPageFailure(version)
                    if (!quiet) eval("JR&&JR.toast('That update did not arrive in one piece')")
                }'''

COMP_OLD = '''        /** Where an app offer already seen is remembered, so a launch cannot repeat it. */
        const val UPDATES = "updates"
        const val OFFERED = "offered"'''

COMP_NEW = '''        /** Where an app offer already seen is remembered, so a launch cannot repeat it. */
        const val UPDATES = "updates"
        const val OFFERED = "offered"
        /** A screen version that was tried and refused, and when it was. */
        const val FAILED = "page-failed"
        const val FAILED_AT = "page-failed-at"
        /** A refused screen is retried by a check of its own only after this long. */
        const val RETRY_PAGE = 6 * 60 * 60 * 1000L'''

BR_OLD = '''    @JavascriptInterface
    fun pageVersion(): String = PageStore.running(ui)

    /** The journal's name, for the top bar. */'''

BR_NEW = '''    @JavascriptInterface
    fun pageVersion(): String = PageStore.running(ui)

    /**
     * 1.9.11 - what the page has already shown once, kept where a cleared WebView cannot reach it.
     * The page still keeps its own copy; this is the one that survives the storage being cleared,
     * which is the difference between a popup shown once and a popup that returns every launch.
     */
    @JavascriptInterface
    fun seen(key: String): String =
        ui.getSharedPreferences(SEEN, Context.MODE_PRIVATE).getString(key, "") ?: ""

    @JavascriptInterface
    fun markSeen(key: String, value: String) {
        ui.getSharedPreferences(SEEN, Context.MODE_PRIVATE).edit().putString(key, value).apply()
    }

    /** The journal's name, for the top bar. */'''

BRKEY_OLD = '''    private companion object {
        /** Where an imported birthday says it came from, so one is recognisable in the plans list. */
        const val FROM_FAMTM = "From FamTM"
    }'''

BRKEY_NEW = '''    private companion object {
        /** Where an imported birthday says it came from, so one is recognisable in the plans list. */
        const val FROM_FAMTM = "From FamTM"
        /** The preferences the page's "shown once" markers live in, beside the page's own copy. */
        const val SEEN = "seen"
    }'''

NOTE_HEAD = "## 1.9.10 \u2014 November 6, 2026"

NOTE_NEW = '''## 1.9.11 \u2014 November 7, 2026

**The update that kept coming back.**

- A screen that does not arrive in one piece is no longer fetched again on every launch and every
  return. It is tried once, and again only on a check you asked for, or after six hours.
- The welcome, the tour and What's New are kept by the app as well as by the screen, so a cleared
  cache cannot bring the same popup back on every launch.
- No version here ends in ten: 1.9.11 follows 1.9.9, and the build number the phone compares has
  room for any part, so an update always installs over the one before it.

''' + NOTE_HEAD

EDITS = [
    (PAGE, 'const JOURNAL_PAGE = "%s";' % OLD, 'const JOURNAL_PAGE = "%s";' % V),
    (PAGE, WN_HEAD, WN_NEW),
    (PAGE, HELP_OLD, HELP_NEW),
    (PAGE, HELLO_OLD, HELLO_NEW),
    (PAGE, TOUR_OLD, TOUR_NEW),
    (GRADLE, GRADLE_OLD, GRADLE_NEW),
    (ACT, OFFER_OLD, OFFER_NEW),
    (ACT, REM_OLD, REM_NEW),
    (ACT, WRITE_OLD, WRITE_NEW),
    (ACT, COMP_OLD, COMP_NEW),
    (BRIDGE, BR_OLD, BR_NEW),
    (BRIDGE, BRKEY_OLD, BRKEY_NEW),
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
    act = read(ACT)
    bridge = read(BRIDGE)
    notes = read(NOTES)

    probes = [
        ('const JOURNAL_PAGE = "%s";' % V in page, "the page does not say %s" % V),
        ('    "%s": {' % V in page, "What's New has no %s entry" % V),
        ('remembered("ujournal.wn")' in page, "What's New is not kept by the app as well"),
        ('remember("ujournal.hello", "1")' in page, "the welcome is not kept by the app as well"),
        ('remember("ujournal.tour", JOURNAL_PAGE)' in page, "the tour is not kept by the app as well"),
        ('localStorage.setItem("ujournal.wn"' not in page, "a marker still lives only in the page"),
        ('ujournal-page' in page, "the page lost its ujournal-page marker"),
        ('const JOURNAL_PAGE = "%s";' % OLD not in page, "the page still says %s" % OLD),
        ('versionName = "%s"' % V in gradle, "build.gradle.kts does not carry %s" % V),
        ('1_000_000' in gradle, "the build number has no room for a part over two digits"),
        ('pageFailedRecently' in act, "a refused screen is not remembered"),
        ('rememberPageFailure(version)' in act, "a failed download does not record itself"),
        ('const val RETRY_PAGE' in act, "there is no wait before a refused screen is retried"),
        ('fun markSeen(' in bridge and 'fun seen(' in bridge, "the app cannot keep a marker for the page"),
        ("## %s " % V in notes, "PATCH_NOTES has no %s entry" % V),
    ]
    bad = [why for ok, why in probes if not ok]
    if bad:
        sys.exit("; ".join(bad))

    if check:
        print("all %d checks pass - the tree carries %s" % (len(probes), V))
        print("untouched this run" if not touched else "applied: " + ", ".join(sorted(set(touched))))
        return

    print("UJournal %s applied to index.html, build.gradle.kts, MainActivity.kt, Bridge.kt and "
          "PATCH_NOTES.md" % V)
    print("next: the apply workflow commits it, then release.yml on tag v%s" % V)


if __name__ == "__main__":
    main()
