package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate

/**
 * Everything the page is allowed to ask the phone for, and nothing more.
 *
 * The screen is `assets/index.html`, so the parts that cannot live in a page live here: the journal
 * on disk, the entries, the plans in the calendar, the pickers and the recorder, the tip links, the
 * update, and the one file a journal can be carried to a new phone in. There is one journal - the
 * shelf this class used to expose is gone - so the page asks for the journal's name and nothing
 * else about which book it is looking at. Each method is a
 * small, named promise - the page cannot reach a file, a database or an intent that is not spelled
 * out below, which is what makes an over-the-air screen safe to accept.
 *
 * These are called on the WebView's JavaScript thread, so anything that touches the UI is handed to
 * the activity's main thread first.
 */
class Bridge(private val ui: MainActivity) {

    private val store = Store(ui.applicationContext)

    private fun main(block: () -> Unit) { ui.runOnUiThread { block() } }

    /** The page has drawn itself. Until this arrives the shell is ready to put the old screen back. */
    @JavascriptInterface
    fun ready() = ui.pageReady()

    @JavascriptInterface
    fun appVersion(): String = BuildConfig.VERSION_NAME

    @JavascriptInterface
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

    /** The journal's name, for the top bar. */
    @JavascriptInterface
    fun currentJournal(): String = runCatching { store.name() }.getOrDefault("")

    /** Every entry that has something in it, newest first. */
    @JavascriptInterface
    fun entries(): String {
        val all = JSONArray()
        // The object itself, not its text: putting the string here would hand the page an array of
        // strings, which is how the timeline came to draw NaN over its cards.
        runCatching { store.all().forEach { all.put(JSONObject(json(it))) } }
        return all.toString()
    }

    /** The open book's plans: timed, over several days, and the birthdays that repeat every year. */
    @JavascriptInterface
    fun plans(): String {
        val all = JSONArray()
        runCatching { store.plans().forEach { all.put(JSONObject(planJson(it))) } }
        return all.toString()
    }

    /** Save one plan and hand it back, so the page can draw the row the shell actually wrote. */
    @JavascriptInterface
    fun savePlan(json: String): String = runCatching {
        val o = JSONObject(json)
        val start = o.optString("start").ifBlank { LocalDate.now().toString() }
        planJson(
            store.savePlan(
                Plan(
                    id = o.optString("id"),
                    title = o.optString("title"),
                    start = start,
                    startTime = o.optString("startTime"),
                    end = o.optString("end").ifBlank { start },
                    endTime = o.optString("endTime"),
                    kind = o.optString("kind").ifBlank { "event" },
                    note = o.optString("note")
                )
            )
        )
    }.getOrDefault("")

    @JavascriptInterface
    fun removePlan(id: String) = runCatching { store.removePlan(id) }.let { }

    @JavascriptInterface
    fun load(date: String): String =
        runCatching { json(store.load(LocalDate.parse(date))) }.getOrElse { "{}" }

    /** The title and the body only: attachments are added and removed by name, never refused blind. */
    @JavascriptInterface
    fun save(date: String, title: String, body: String) {
        runCatching {
            val d = LocalDate.parse(date)
            store.save(Entry(d, title, body, store.load(d).atts))
        }
    }

    @JavascriptInterface
    fun pick(date: String, kind: String) = main { ui.pick(date, kind) }

    @JavascriptInterface
    fun recordStart(date: String): Boolean =
        runCatching { ui.startRecording(date) }.getOrDefault(false)

    @JavascriptInterface
    fun recordStop(date: String) = main { ui.stopRecording(date, true) }

    @JavascriptInterface
    fun recordCancel() = main { ui.stopRecording(null, false) }

    @JavascriptInterface
    fun remove(date: String, name: String) {
        runCatching {
            val d = LocalDate.parse(date)
            val e = store.load(d)
            val a = e.atts.firstOrNull { it.name == name } ?: return@runCatching
            store.save(store.remove(e, a))
        }
    }

    @JavascriptInterface
    fun open(date: String, name: String) = main { ui.openAttachment(date, name) }

    /** The page names an amount, never a URL: the links stay in [Support], where they are kept. */
    @JavascriptInterface
    fun tip(dollars: Int) = main {
        Support.LINKS.firstOrNull { it.first == dollars }?.let { Support.open(ui, it.second) }
    }

    /** The page names another app, never a URL: the addresses stay in [Siblings]. */
    @JavascriptInterface
    fun openApp(id: String): Boolean = Siblings.open(ui, id)

    /** One file with every journal, entry and attachment in it, written where the Save dialog points. */
    @JavascriptInterface
    fun backup() = main { ui.exportAll() }

    /** Read one of those files back and make it this phone's shelf. The page asks once before calling it. */
    @JavascriptInterface
    fun restore() = main { ui.importAll() }

    /**
     * How many birthdays FamTM is holding that this journal does not have yet, or -1 when FamTM is
     * not installed or publishes none. Names and days only: that is all the provider hands over.
     */
    /**
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

    /** Bring them across as birthday plans; returns how many were actually added. */
    @JavascriptInterface
    fun importFamTmBirthdays(): Int = runCatching {
        val list = FamTm.birthdays(ui) ?: return@runCatching 0
        val have = birthdays()
        var added = 0
        list.filter { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have }
            .forEach { b ->
                store.savePlan(Plan("", b.name, b.date, "", b.date, "", "birthday", FROM_FAMTM))
                added++
            }
        added
    }.getOrDefault(0)

    /**
     * Both directions at once, which is what the one button in Plans runs: FamTM's birthdays come in,
     * and this journal's go out through [Birthdays] at `content://app.ujournal.birthdays/list`, where
     * FamTM reads them the same way this app reads its list. Returns what actually changed.
     */
    @JavascriptInterface
    fun syncBirthdays(): String = runCatching {
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
            // What this journal publishes back, counted after the import so the number is the truth
            // of the list FamTM will read, not of the list before the tap.
            .put("shared", store.plans().count { it.kind == "birthday" })
            .toString()
    }.getOrDefault("{}")

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

    /** Every birthday already in the plans, as name|MM-DD, which is what a birthday repeats on. */
    private fun birthdays(): Set<String> = store.plans()
        .filter { it.kind == "birthday" }
        .map { it.title.lowercase() + "|" + it.start.takeLast(5) }
        .toSet()

    @JavascriptInterface
    fun checkUpdates() = main { ui.checkUpdates(silent = false) }

    @JavascriptInterface
    fun updateNow(url: String, version: String) = ui.applyPage(url, version)

    @JavascriptInterface
    fun openRelease(version: String) = main { ui.openRelease(version) }

    private companion object {
        /** Where an imported birthday says it came from, so one is recognisable in the plans list. */
        const val FROM_FAMTM = "From FamTM"
        /** The preferences the page's "shown once" markers live in, beside the page's own copy. */
        const val SEEN = "seen"
    }

    private fun planJson(p: Plan): String = JSONObject()
        .put("id", p.id)
        .put("title", p.title)
        .put("start", p.start)
        .put("startTime", p.startTime)
        .put("end", p.end)
        .put("endTime", p.endTime)
        .put("kind", p.kind)
        .put("note", p.note)
        .toString()

    private fun json(e: Entry): String = JSONObject()
        .put("date", e.date.toString())
        .put("title", e.title)
        .put("body", e.body)
        .put("atts", JSONArray().apply {
            e.atts.forEach { a ->
                put(
                    JSONObject()
                        .put("name", a.name)
                        .put("mime", a.mime)
                        // The page draws a thumbnail straight from the file, so it needs the path.
                        .put("path", store.file(e.date, a).absolutePath)
                )
            }
        })
        .toString()
}

/**
 * The other apps this collection has, each behind a name the page is allowed to say. The addresses
 * live here and not in the page for the same reason the tip links do: an over-the-air screen can be
 * replaced, so the set of places it can send someone is fixed by the app, not by the page.
 *
 * These are Play listings, not the repositories. The releases page is where the APKs are kept for
 * sideloading, which is not what "get this app" means to someone reading it: a Play listing is the
 * place an app is installed from, updated from, and uninstalled from, and it is the one address that
 * survives a rename of the repository. An id here is the package name the app was published under,
 * so a listing that is not up yet answers with Play's own "not found" page rather than sending
 * anyone to a download they would have to keep updated by hand.
 */
internal object Siblings {
    private val APPS = listOf(
        "journal" to "https://play.google.com/store/apps/details?id=app.ujournal",
        "famtm" to "https://play.google.com/store/apps/details?id=com.FamTM.app",
        "myhub" to "https://play.google.com/store/apps/details?id=com.myhub.app",
        "sidecut" to "https://play.google.com/store/apps/details?id=com.SideCut.myapp",
        // The package still carries its original Compass-EDC name; the app itself is MeasureT.
        "measuret" to "https://play.google.com/store/apps/details?id=com.CompassEDC.myapp"
    )

    fun url(id: String): String? = APPS.firstOrNull { it.first == id }?.second

    fun open(ctx: Context, id: String): Boolean {
        val address = url(id) ?: return false
        return runCatching {
            ctx.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(address)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
            true
        }.getOrDefault(false)
    }
}
