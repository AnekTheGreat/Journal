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
 * The screen is `assets/index.html`, so the parts that cannot live in a page live here: the shelf of
 * journals, the entries on disk, the plans in the calendar, the pickers and the recorder, the tip
 * links, the update, and the one file a journal can be carried to a new phone in. Each method is a
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

    /** The shelf: id, name, how many days it holds and the last one written in. */
    @JavascriptInterface
    fun journals(): String {
        val all = JSONArray()
        runCatching {
            store.journals().forEach { j ->
                all.put(
                    JSONObject()
                        .put("id", j.id)
                        .put("name", j.name)
                        .put("created", j.created)
                        .put("entries", j.entries)
                        .put("last", j.last ?: "")
                )
            }
        }
        return all.toString()
    }

    /** Start a book and open it. The page asks for a name first, and gets the open book's name back. */
    @JavascriptInterface
    fun create(name: String): String = runCatching { store.create(name) }.getOrDefault("")

    /** Open a book from the shelf. Empty when that id is not on this phone. */
    @JavascriptInterface
    fun openJournal(id: String): String = runCatching {
        if (store.open(id)) store.name() else ""
    }.getOrDefault("")

    /** The open book's name, for the top bar. */
    @JavascriptInterface
    fun currentJournal(): String = runCatching { store.name() }.getOrDefault("")

    /** Every entry that has something in it in the open book, newest first. */
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

    @JavascriptInterface
    fun checkUpdates() = main { ui.checkUpdates(silent = false) }

    @JavascriptInterface
    fun updateNow(url: String, version: String) = ui.applyPage(url, version)

    @JavascriptInterface
    fun openRelease(version: String) = main { ui.openRelease(version) }

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
        "famtm" to "https://play.google.com/store/apps/details?id=com.familytree.app",
        "myhub" to "https://play.google.com/store/apps/details?id=com.myhub.app",
        "sidecut" to "https://play.google.com/store/apps/details?id=com.SideCut.myapp",
        "compass" to "https://play.google.com/store/apps/details?id=com.CompassEDC.myapp"
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
