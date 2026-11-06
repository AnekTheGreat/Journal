#!/usr/bin/env python3
"""UJournal 1.9.3 - the birthdays card says what it actually saw.

1.9.2 declared FamTM in <queries>, which is the asking Android wants. If the card still says FamTM
is not installed, that sentence is wrong: the app was never asking the question the message claimed.
This release stops guessing. It looks the FamTM package up, reads the version it finds, asks for the
list, and reports which of those three things failed - the app is not there, the app is there but its
list cannot be read, or it answered and had nothing new. The journal's own version goes into the
message too, because the screen updates over the air while the asking lives in the app, so an old
app with a new screen is the one case that looks exactly like "not working".

Usage: python3 dev/patch-193.py [--check]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADLE = ROOT / "app/build.gradle.kts"
FAMTM = ROOT / "app/src/main/java/app/ujournal/FamTm.kt"
BRIDGE = ROOT / "app/src/main/java/app/ujournal/Bridge.kt"
PAGE = ROOT / "app/src/main/assets/index.html"
NOTES = ROOT / "PATCH_NOTES.md"

FAMTM_KT = '''package app.ujournal

import android.content.Context
import android.net.Uri
import org.json.JSONArray

/**
 * The birthdays FamTM keeps for the family, read through the read-only provider it publishes at
 * `content://com.FamTM.app.birthdays/list`.
 *
 * FamTM hands over exactly the list its own birthday reminders use - a name, a month and a day for
 * each living person, plus the year when one was given - and nothing else: no photos, no notes, no
 * addresses. The provider answers a query and refuses every write, so this is a one-way read of a
 * short list, not a way to reach the family.
 *
 * Since 1.9.3 it also says which of the three cases it is in, because the card used to call all of
 * them "FamTM is not installed" and that was wrong twice out of three times: the app may be missing,
 * or it may be there and its list unreadable (an older FamTM with no provider, or an Android build
 * that hides it), or it may answer with an empty list. [version] is the package lookup, [birthdays]
 * is the read, and an empty answer is no longer confused with a refusal.
 */
internal object FamTm {

    private const val PACKAGE = "com.FamTM.app"

    /** One person's birthday: the day it repeats on, and the year when one was recorded. */
    class Birthday(val name: String, val month: Int, val day: Int, val year: Int) {

        /** MM-DD: the part of a birthday that comes round every year. */
        val md: String =
            (if (month < 10) "0" else "") + month + "-" + (if (day < 10) "0" else "") + day

        /**
         * A date the plans table accepts. The year does not matter to a birthday - the page matches
         * on the month and the day - but a year FamTM knows is kept as it is.
         */
        val date: String = (if (year in 1..9999) year else 2000).toString() + "-" + md
    }

    private val URI: Uri = Uri.parse("content://${PACKAGE}.birthdays/list")

    /**
     * The version of FamTM on this phone, or null when there is none. This is the package lookup and
     * not the provider, so it can tell "not installed" from "installed but its list could not be
     * read" - the two cases the old message ran together.
     */
    fun version(ctx: Context): String? = try {
        @Suppress("DEPRECATION")
        ctx.packageManager.getPackageInfo(PACKAGE, 0)?.versionName
    } catch (e: Exception) {
        null
    }

    /** Whether FamTM is on the phone at all, whatever its list does. */
    fun installed(ctx: Context): Boolean = version(ctx) != null

    /**
     * The list FamTM publishes. Empty when it answered with nothing, and null only when it could not
     * be read at all - no provider, a refusal, or a phone that will not let this app see it.
     */
    fun birthdays(ctx: Context): List<Birthday>? = try {
        val c = ctx.contentResolver.query(URI, null, null, null, null) ?: return null
        c.use { cur ->
            if (!cur.moveToFirst()) {
                emptyList()
            } else {
                val i = cur.getColumnIndex("json")
                if (i < 0) {
                    emptyList()
                } else {
                    val raw = cur.getString(i) ?: "[]"
                    val arr = runCatching { JSONArray(raw) }.getOrElse { JSONArray() }
                    (0 until arr.length()).mapNotNull { k ->
                        val o = arr.optJSONObject(k) ?: return@mapNotNull null
                        val name = o.optString("n").trim().take(80)
                        val m = o.optInt("m")
                        val d = o.optInt("d")
                        if (name.isEmpty() || m !in 1..12 || d !in 1..31) null
                        else Birthday(name, m, d, o.optInt("y"))
                    }
                }
            }
        }
    } catch (e: Exception) {
        null
    }
}
'''

BRIDGE_OLD = '''    @JavascriptInterface
    fun famtmBirthdays(): Int = runCatching {
        val list = FamTm.birthdays(ui) ?: return@runCatching -1
        val have = birthdays()
        list.count { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have }
    }.getOrDefault(-1)
'''

BRIDGE_NEW = '''    /**
     * What the Plans card draws before a tap: how many of FamTM's birthdays are not in the journal
     * yet, and -1 or -2 when there is no answer to give. -1 is no FamTM on the phone, -2 is FamTM on
     * the phone whose list could not be read, and the card says the two differently now.
     */
    @JavascriptInterface
    fun famtmBirthdays(): Int = runCatching {
        if (!FamTm.installed(ui)) return@runCatching -1
        val list = FamTm.birthdays(ui) ?: return@runCatching -2
        val have = birthdays()
        list.count { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have }
    }.getOrDefault(-2)
'''

SYNC_OLD = '''    fun syncBirthdays(): String = runCatching {
        val offered = FamTm.birthdays(ui) ?: emptyList()
        val have = birthdays()
        var added = 0
        offered.filter { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have }
            .forEach { b ->
                store.savePlan(Plan("", b.name, b.date, "", b.date, "", "birthday", FROM_FAMTM))
                added++
            }
        JSONObject()
            .put("added", added)
            .put("offered", offered.size)
            .put("installed", FamTm.installed(ui))
'''

SYNC_NEW = '''    fun syncBirthdays(): String = runCatching {
        val app = FamTm.version(ui)
        val read = FamTm.birthdays(ui)
        val offered = read ?: emptyList()
        val have = birthdays()
        var added = 0
        offered.filter { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have }
            .forEach { b ->
                store.savePlan(Plan("", b.name, b.date, "", b.date, "", "birthday", FROM_FAMTM))
                added++
            }
        JSONObject()
            .put("added", added)
            .put("offered", offered.size)
            .put("installed", app != null)
            // Why there is nothing to add, in the one word the card can turn into a sentence:
            // no-app is no FamTM on the phone, no-read is FamTM there but unreadable, ok is an
            // answer that simply held nothing new.
            .put("why", when {
                app == null -> "no-app"
                read == null -> "no-read"
                else -> "ok"
            })
            .put("app", app ?: "")
'''

CARD_OLD = '''  function famtmPending() {
    var n = parseInt(call("famtmBirthdays"), 10);
    return isNaN(n) || n < 0 ? 0 : n;
  }
'''

CARD_NEW = '''  // -1 is no FamTM on the phone, -2 is FamTM there whose list this app could not read. They are
  // different problems and the card says so, instead of calling both of them "not installed".
  function famtmPending() {
    var n = parseInt(call("famtmBirthdays"), 10);
    return isNaN(n) ? 0 : n;
  }

  // The version of the app the screen is running in. The screen turns up over the air while the
  // asking lives in the app, so this is the one line that tells an old app from a broken one.
  function appVer() {
    try { return String(call("appVersion") || ""); } catch (e) { return ""; }
  }
'''

BUTTON_OLD = '''  function famtmButton() {
    var n = famtmPending();
    var line = n > 0
      ? (n === 1 ? "1 new birthday from FamTM" : n + " new birthdays from FamTM")
      : "Bring FamTM's across, and share yours back";
'''

BUTTON_NEW = '''  function famtmButton() {
    var n = famtmPending();
    var line = n > 0
      ? (n === 1 ? "1 new birthday from FamTM" : n + " new birthdays from FamTM")
      : n === -1
        ? "FamTM isn't installed on this phone"
        : n === -2
          ? "FamTM is here, but this copy can't read it"
          : "Bring FamTM's across, and share yours back";
'''

SYNCMSG_OLD = '''  function runSync() {
    var r = parse(call("syncBirthdays"), null) || {};
    refresh();
    var added = parseInt(r.added, 10) || 0;
    var shared = parseInt(r.shared, 10) || 0;
    var installed = r.installed === true || r.installed === "true";
    var msg = added > 0
      ? (added === 1 ? "One birthday added from FamTM" : added + " birthdays added from FamTM")
      : (installed ? "FamTM had nothing new" : "Nothing new here, and FamTM is not installed");
'''

SYNCMSG_NEW = '''  function runSync() {
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

WN = '''    "1.9.3": {
      date: "6 November 2026",
      title: "The birthdays card says what it actually found",
      notes: [
        "The card no longer calls every failure FamTM not installed. It looks the app up on the phone, and then says which thing is true: FamTM is not there, FamTM is there and this copy of the journal could not read its list, or FamTM answered and had nothing new.",
        "When it cannot read the list it names both versions - the FamTM on the phone and the journal you are holding - because the screen updates over the air while the asking lives in the app, so an older app with the newest screen looks exactly like a broken one.",
        "Nothing about the birthdays changed: a name and a day come across, and what is typed here is still published back for FamTM to read."
      ]
    },
'''

NOTE = '''## 1.9.3 — November 6, 2026

**The birthdays card now says which of the three things happened**

### Fixed
- **"FamTM is not installed" was said for two other problems as well.** The card had one failure
  message and three ways to reach it: no FamTM on the phone, FamTM on the phone whose list this app
  could not read, and a list it read that was empty. The app now looks the FamTM package up first,
  reads its version, and only then asks for the list - so the sentence on the card matches what
  actually happened.
- **The journal's own version is named when the read fails.** The screen arrives over the air while
  the asking lives in the app, so an older app with the newest screen behaves exactly like a broken
  one. The message now names both versions, which is the difference between "update the app" and
  "something is wrong with the list".
- **An empty list is no longer treated as a refusal.** A FamTM that answers with an empty list is a
  FamTM with nothing in it, and the card says that instead of blaming the install.

### Unchanged
- The provider here still publishes this journal's birthdays back to FamTM, names and days only, and
  the plan durations, the tip heart and the screen are as they were in 1.9.2.


'''


def edit(path, pairs):
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch-193: %s: no such text to replace:\n  %r" % (path.name, old[:90]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    page = PAGE.read_text(encoding="utf-8")
    done = (
        'versionName = "1.9.3"' in GRADLE.read_text(encoding="utf-8")
        and 'const JOURNAL_PAGE = "1.9.3";' in page
        and '"1.9.3": {' in page
        and 'why === "no-read"' in page
        and 'fun version(ctx: Context)' in FAMTM.read_text(encoding="utf-8")
        and 'return@runCatching -2' in BRIDGE.read_text(encoding="utf-8")
        and "## 1.9.3 — November 6, 2026" in NOTES.read_text(encoding="utf-8")
    )
    if check:
        print("1.9.3 already applied" if done else "1.9.3 not applied yet")
        return 0 if done else 1
    if done:
        print("1.9.3 already applied - nothing to do")
        return 0

    edit(GRADLE, [('versionName = "1.9.2"', 'versionName = "1.9.3"')])
    FAMTM.write_text(FAMTM_KT, encoding="utf-8")
    edit(BRIDGE, [(BRIDGE_OLD, BRIDGE_NEW), (SYNC_OLD, SYNC_NEW)])
    edit(PAGE, [
        ('const JOURNAL_PAGE = "1.9.2";', 'const JOURNAL_PAGE = "1.9.3";'),
        ('  var WN = {\n    "1.9.2": {', '  var WN = {\n' + WN + '    "1.9.2": {'),
        (CARD_OLD, CARD_NEW),
        (BUTTON_OLD, BUTTON_NEW),
        (SYNCMSG_OLD, SYNCMSG_NEW),
    ])
    edit(NOTES, [('## 1.9.2 — November 6, 2026', NOTE + '## 1.9.2 — November 6, 2026')])

    print("1.9.3 applied: package lookup, three-way message, versions named, notes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
