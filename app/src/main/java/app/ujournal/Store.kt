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

/** Plain files: filesDir/journal/YYYY-MM-DD/entry.json + attachments beside it. */
class Store(ctx: Context) {
    private val cr = ctx.contentResolver
    private val root = File(ctx.filesDir, "journal").apply { mkdirs() }

    fun dir(d: LocalDate) = File(root, d.toString())
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

    fun all(): List<Entry> = (root.listFiles() ?: emptyArray())
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
}
