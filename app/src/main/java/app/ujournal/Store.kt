package app.ujournal

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate

data class Att(val name: String, val mime: String)
data class Entry(val date: LocalDate, val title: String, val body: String, val atts: List<Att>)

/** One book: what it is called, when it was started, and what is in it. */
data class Journal(val id: String, val name: String, val created: String, val entries: Int, val last: String?)

/**
 * Plain files, one folder per journal:
 *
 *   journals/<id>/journal.json        {"name":"...","created":"YYYY-MM-DD"}
 *   journals/<id>/YYYY-MM-DD/entry.json + attachments beside it
 *
 * A journal is a book, and there can be more than one, which is why a day is addressed through the
 * book it lives in. [current] is the one the page is looking at; [journals] is the shelf. The folder
 * 1.3 wrote - filesDir/journal - is moved into this shape once, on the first launch after the
 * update, so an existing journal becomes the first book and no entry is left behind.
 */
class Store(ctx: Context) {
    private val cr = ctx.contentResolver
    private val root = File(ctx.filesDir, DIR).apply { mkdirs() }

    /** The open book. Null only before the shelf has been read. */
    private var open: String? = null

    init { migrate(ctx) }

    /** The book being drawn, healing a stale id (a restore can replace the whole shelf). */
    val current: String get() = ensure()

    private fun ensure(): String {
        open?.let { if (File(root, it).isDirectory) return it }
        val first = journals().firstOrNull()?.id ?: newId()
        if (!File(root, first).isDirectory) writeMeta(first, "My Journal")
        open = first
        return first
    }

    private fun newId() = "j" + System.currentTimeMillis().toString(36)

    private fun meta(d: File): JSONObject =
        runCatching { JSONObject(File(d, META).readText()) }.getOrDefault(JSONObject())

    private fun writeMeta(id: String, name: String) {
        val d = File(root, id).apply { mkdirs() }
        File(d, META).writeText(
            JSONObject().put("name", name).put("created", LocalDate.now().toString()).toString()
        )
    }

    /** The shelf, most recently written in first; a book with no entries sorts by when it was made. */
    fun journals(): List<Journal> = (root.listFiles() ?: emptyArray())
        .filter { it.isDirectory && ID.matches(it.name) }
        .map { d ->
            val days = (d.listFiles() ?: emptyArray())
                .filter { it.isDirectory && DATE.matches(it.name) }
                .map { it.name }
            val m = meta(d)
            Journal(
                id = d.name,
                name = m.optString("name").ifBlank { "My Journal" },
                created = m.optString("created"),
                entries = days.size,
                last = days.maxOrNull()
            )
        }
        .sortedWith(compareByDescending<Journal> { it.last ?: it.created })

    fun create(name: String): String {
        val id = newId()
        writeMeta(id, name.trim().ifBlank { "My Journal" }.take(60))
        open = id
        return id
    }

    /** Open one of the shelf's books. False when the id is not on this phone. */
    fun open(id: String): Boolean {
        if (!ID.matches(id) || !File(root, id).isDirectory) return false
        open = id
        return true
    }

    fun name(id: String = current): String =
        meta(File(root, id)).optString("name").ifBlank { "My Journal" }

    fun rename(id: String, name: String) {
        if (!ID.matches(id) || !File(root, id).isDirectory) return
        val clean = name.trim().ifBlank { "My Journal" }.take(60)
        val m = meta(File(root, id)).put("name", clean)
        runCatching { File(File(root, id), META).writeText(m.toString()) }
    }

    fun dir(d: LocalDate) = File(File(root, current), d.toString())
    fun file(d: LocalDate, a: Att) = File(dir(d), a.name)

    fun load(d: LocalDate): Entry {
        val f = File(dir(d), "entry.json")
        if (!f.exists()) return Entry(d, "", "", emptyList())
        val j = JSONObject(f.readText())
        val arr = j.optJSONArray("atts") ?: JSONArray()
        val atts = (0 until arr.length()).map {
            val o = arr.getJSONObject(it); Att(o.getString("name"), o.getString("mime"))
        }
        return Entry(d, j.optString("title"), j.optString("body"), atts)
    }

    fun save(e: Entry) {
        if (e.title.isBlank() && e.body.isBlank() && e.atts.isEmpty()) {
            dir(e.date).deleteRecursively(); return
        }
        dir(e.date).mkdirs()
        val j = JSONObject().put("title", e.title).put("body", e.body)
            .put("atts", JSONArray(e.atts.map { JSONObject().put("name", it.name).put("mime", it.mime) }))
        File(dir(e.date), "entry.json").writeText(j.toString())
    }

    fun all(): List<Entry> = (File(root, current).listFiles() ?: emptyArray())
        .mapNotNull { runCatching { LocalDate.parse(it.name) }.getOrNull() }
        .map { load(it) }
        .filter { it.title.isNotBlank() || it.body.isNotBlank() || it.atts.isNotEmpty() }
        .sortedByDescending { it.date }

    fun attach(e: Entry, uris: List<Uri>): Entry {
        val d = dir(e.date).apply { mkdirs() }
        val added = uris.mapNotNull { u ->
            runCatching {
                var mime = cr.getType(u) ?: "application/octet-stream"
                var base = "file"
                cr.query(u, null, null, null, null)?.use { c ->
                    if (c.moveToFirst()) {
                        val i = c.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                        if (i >= 0) base = c.getString(i)
                    }
                }
                base = base.replace(Regex("[^A-Za-z0-9._ -]"), "_")
                if (mime == "application/octet-stream")
                    android.webkit.MimeTypeMap.getSingleton()
                        .getMimeTypeFromExtension(base.substringAfterLast('.', "").lowercase())?.let { mime = it }
                var name = base; var k = 1
                while (File(d, name).exists() || name == "entry.json") name = "${k++}_$base"
                cr.openInputStream(u)!!.use { i -> File(d, name).outputStream().use { o -> i.copyTo(o) } }
                Att(name, mime)
            }.getOrNull()
        }
        return e.copy(atts = e.atts + added)
    }

    fun remove(e: Entry, a: Att): Entry {
        file(e.date, a).delete()
        return e.copy(atts = e.atts - a)
    }

    /**
     * 1.3 kept one journal at filesDir/journal. It becomes the first book the first time this runs,
     * so the update changes where the entries are addressed from and nothing about where they are.
     */
    private fun migrate(ctx: Context) {
        val legacy = File(ctx.filesDir, OLD)
        if (!legacy.isDirectory) return
        val id = if (File(root, "first").exists()) newId() else "first"
        val target = File(root, id)
        if (!target.exists() && legacy.renameTo(target)) {
            if (!File(target, META).exists()) writeMeta(id, "My Journal")
        }
    }

    companion object {
        const val DIR = "journals"
        const val OLD = "journal"
        const val META = "journal.json"

        /** A folder name this store wrote: short, and no path in it. */
        val ID = Regex("[A-Za-z0-9_-]{1,40}")

        val DATE = Regex("[0-9]{4}-[0-9]{2}-[0-9]{2}")

        fun rootOf(files: File) = File(files, DIR)

        fun dirOf(files: File, id: String) = File(rootOf(files), id)
    }
}
