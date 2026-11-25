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
     * 2.9 - THE SAME LIST, CARRIED BY HAND. The exchange with FamTM is a provider read, and on a
     * phone where that read is the thing that does not work there was no way to bring a birthday
     * across at all. This saves the whole card - FamTM's list as it is today, plus the ones typed
     * here - as one file wherever the phone's Save dialog points, to be kept or taken to another
     * phone.
     */
    @JavascriptInterface
    fun saveBirthdays() = main { ui.exportBirthdays() }

    /** And the other half: a birthdays file, or a FamTM backup, read back into the plans. */
    @JavascriptInterface
    fun loadBirthdays() = main { ui.importBirthdays() }

    /** What [saveBirthdays] writes: every birthday this app knows, and where each one came from. */
    internal fun birthdaysFile(): String {
        val app = FamTm.version(ui)
        val read = FamTm.birthdays(ui) ?: emptyList()
        val out = ArrayList<BirthdayFile.Birthday>()
        val seen = HashSet<String>()
        read.filter { it.name.isNotBlank() }.forEach { b ->
            out.add(BirthdayFile.Birthday(b.name, b.month, b.day, b.year, true))
            seen.add(b.name.lowercase() + "|" + b.md)
        }
        store.plans().filter { it.kind == "birthday" && it.title.isNotBlank() }.forEach { p ->
            val md = p.start.takeLast(5)
            if ((p.title.lowercase() + "|" + md) in seen) return@forEach
            val m = md.take(2).toIntOrNull() ?: return@forEach
            val d = md.takeLast(2).toIntOrNull() ?: return@forEach
            // 2.9.1 - a birthday a file brought is FamTM's list too, so it travels as one: a file
            // saved here and loaded on another phone keeps the same meaning there.
            val famTm = p.note == FROM_FAMTM || p.note == FROM_FILE
            out.add(BirthdayFile.Birthday(p.title, m, d, p.start.take(4).toIntOrNull() ?: 0, famTm))
            seen.add(p.title.lowercase() + "|" + md)
        }
        return BirthdayFile.write(out, PageStore.running(ui), app ?: "", LocalDate.now().toString())
    }

    /**
     * 2.9 - A FILE IS NOT A FAMILY THAT LOST SOMEBODY. Reading a birthdays file adds what is missing
     * and corrects a birthday from FamTM where it already is, on the same name and day rules the
     * Re-check uses - but it never takes one out. A file is a snapshot somebody carried, and a short
     * one is far more likely than a family that shrank; only a live read of FamTM's own list is
     * trusted with a removal.
     */
    internal fun birthdaysFromFile(text: String): String {
        val read = BirthdayFile.read(text)
            ?: return JSONObject().put("why", "not-birthdays").toString()
        if (read.list.isEmpty()) {
            return JSONObject().put("why", "none").put("from", read.from).toString()
        }
        // What is already here, whoever typed it: a birthday is never added twice.
        val have = birthdays().toMutableSet()
        // Only the ones that came from FamTM - live or in an earlier file - are corrected in place,
        // exactly as a Re-check does. A birthday typed here is never touched by a file either.
        val mine = store.plans()
            .filter { it.kind == "birthday" && (it.note == FROM_FAMTM || it.note == FROM_FILE) }
            .toMutableList()
        var added = 0
        var updated = 0
        var same = 0
        for (b in read.list) {
            val key = b.name.lowercase() + "|" + b.md
            if (key in have) {
                same++
                continue
            }
            // 2.9.1 - ONLY A NAME IS A MATCH, and this is the bug that was reported. It fell back to
            // the same month and day, which in a family of many birthdays is no coincidence: a new
            // person who shares a day with one already here was found by the day and written over
            // that row, so the file's new birthday changed somebody's name instead of arriving - and
            // the more old birthdays were here, the fewer of the new ones came in. A file cannot say
            // whether a shared day is a rename or a second person, so only the same name corrects a
            // row, and everyone else is added beside the ones already here.
            val old = mine.firstOrNull { it.title.equals(b.name, true) }
            if (old != null) {
                if (old.title == b.name && old.start == b.date) {
                    same++
                } else {
                    // The note is left as it was: a birthday a file brought stays one.
                    store.savePlan(old.copy(title = b.name, start = b.date, end = b.date))
                    updated++
                }
                mine.remove(old)
            } else {
                store.savePlan(
                    Plan("", b.name, b.date, "", b.date, "", "birthday", if (b.fromFamTm) FROM_FILE else "")
                )
                added++
            }
            have.add(key)
        }
        return JSONObject()
            .put("why", "ok")
            .put("from", read.from)
            .put("added", added)
            .put("updated", updated)
            .put("same", same)
            .put("shared", store.plans().count { it.kind == "birthday" })
            .toString()
    }

    /**
     * Both directions at once, which is what the one button in Plans runs: FamTM's birthdays come in,
     * and this journal's go out through [Birthdays] at `content://app.ujournal.birthdays/list`, where
     * FamTM reads them the same way this app reads its list. Returns what actually changed.
     *
     * 2.8 - AND IT IS A RE-CHECK, NOT AN APPEND. Up to 2.7 this only ever added: a day corrected in
     * FamTM arrived a second time beside the old one, a renamed person came in as a stranger, and
     * someone taken out of FamTM stayed on the calendar for good. A tapped Re-check that changes
     * nothing the family just changed reads as a button that does nothing, which is exactly how it
     * was reported. So the ones that came from FamTM - the plans carrying [FROM_FAMTM], never a
     * birthday typed here - are brought back in line with the list FamTM publishes now: the same
     * name and day is left alone, a day or a name that changed over there is corrected in place,
     * and one FamTM no longer lists is taken out.
     */
    @JavascriptInterface
    fun syncBirthdays(): String = runCatching {
        val app = FamTm.version(ui)
        val read = FamTm.birthdays(ui)
        val offered = (read ?: emptyList()).filter { it.name.isNotBlank() }
        // Every birthday already here, whoever typed it: the rule that one is never added twice is
        // older than this reconcile and still holds for a birthday entered by hand.
        val have = birthdays()

        // What came from FamTM, and what is still waiting to be matched against it. A birthday a
        // file brought counts here too: it is the same list, and a change made over there should
        // correct it where it is instead of arriving beside it.
        val mine = store.plans()
            .filter { it.kind == "birthday" && (it.note == FROM_FAMTM || it.note == FROM_FILE) }
            .toMutableList()
        val left = offered.toMutableList()
        var added = 0
        var updated = 0
        var removed = 0

        // 1. name and day both still match: the birthday here is the one FamTM has.
        val same = left.filter { b -> mine.any { it.title.equals(b.name, true) && it.start.takeLast(5) == b.md } }
        left.removeAll(same)
        mine.removeAll { p -> same.any { b -> p.title.equals(b.name, true) && p.start.takeLast(5) == b.md } }

        // 2. FamTM still has the person, under the same name with another day or the same day under
        //    another name - a correction, so the row is changed rather than a second one added.
        for (b in left.toList()) {
            val old = mine.firstOrNull { it.title.equals(b.name, true) }
                ?: mine.firstOrNull { it.start.takeLast(5) == b.md }
            if (old != null) {
                // 2.9.1 - the row keeps the note it had. A birthday a file brought is kept in line
                // with FamTM like any other, but it is not turned into one the removal below may
                // take out: a file can know people the list this phone publishes does not.
                val note = if (old.note == FROM_FILE) FROM_FILE else FROM_FAMTM
                store.savePlan(old.copy(title = b.name, start = b.date, end = b.date, note = note))
                mine.remove(old)
                left.remove(b)
                updated++
            }
        }

        // 3. what is left is somebody this journal has never had - unless the same name and day is
        //    already here as a birthday typed by hand, which is still never duplicated.
        for (b in left) {
            if ((b.name.lowercase() + "|" + b.md) in have) continue
            store.savePlan(Plan("", b.name, b.date, "", b.date, "", "birthday", FROM_FAMTM))
            added++
        }

        // 4. and what FamTM no longer lists is taken out - but only against an answer that has
        //    somebody in it. An empty list is the one answer that can mean FamTM never wrote its
        //    own list (an older FamTM, its page never opened), and losing every birthday here to
        //    that would be a worse trade than leaving them until the next real answer.
        if (read != null && offered.isNotEmpty()) {
            for (p in mine) {
                // 2.9.1 - A FILE'S BIRTHDAYS ARE NEVER TAKEN OUT. The list FamTM publishes can be
                // older or shorter than a backup carried from elsewhere, and a file that knows
                // somebody the provider does not used to have that birthday removed again on the
                // very next open - which read as the file not being allowed to add anything while
                // there were old birthdays here. Only the rows that came from a live read go.
                if (p.note != FROM_FAMTM) continue
                store.removePlan(p.id)
                removed++
            }
        }

        JSONObject()
            .put("added", added)
            .put("updated", updated)
            .put("removed", removed)
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
    }.getOrElse {
        // 2.8 - A CALL THAT THREW IS NOT AN EMPTY FAMTM. The answer used to be "{}" here, and the
        // page reads a missing why/offered as a successful read of a list with nobody in it - so a
        // read that broke mid-tap was announced as "FamTM read fine". It gets a word of its own now.
        JSONObject()
            .put("added", 0)
            .put("updated", 0)
            .put("removed", 0)
            .put("offered", -1)
            .put("installed", runCatching { FamTm.installed(ui) }.getOrDefault(false))
            .put("why", "failed")
            .put("app", runCatching { FamTm.version(ui) ?: "" }.getOrDefault(""))
            .put("shared", runCatching { store.plans().count { it.kind == "birthday" } }.getOrDefault(0))
            .toString()
    }

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
        val have = birthdays()
        JSONObject()
            .put("app", app ?: "")
            .put("offered", read?.size ?: -1)
            .put("kept", store.plans().count { it.kind == "birthday" })
            // 2.6 - how many of FamTM's birthdays are not in the journal yet. The card used to read
            // the same whether there was nothing to bring across or three people added in FamTM this
            // week; this is the number that lets it offer to add them.
            .put("new", read?.count { it.name.isNotBlank() && (it.name.lowercase() + "|" + it.md) !in have } ?: 0)
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
        /**
         * 2.9.1 - and where one that arrived in a file says it did. It is FamTM's list all the same,
         * so a Re-check still corrects it, but it is never one of the rows a Re-check takes out: the
         * list this phone publishes can be older than the file, and the file is the half that was
         * chosen by hand.
         */
        const val FROM_FILE = "From a birthdays file"
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
        "famtm" to "https://github.com/AnekTheGreat/FamTM/releases/latest",
        "myhub" to "https://github.com/AnekTheGreat/My-Hub/releases/latest",
        "sidecut" to "https://play.google.com/store/apps/details?id=com.SideCut.myapp",
        // The package still carries its original Compass-EDC name; the app itself is MeasureT, and
        // its own page is where it is handed out.
        "measuret" to "https://anekthegreat.github.io/Compass-EDC/",
        // UNote is a page rather than a listing: the row opens it in the phone's browser, which is
        // also where it can be added to the home screen.
        "unote" to "https://anekthegreat.github.io/UNote/"
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
