package app.ujournal

import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener

/**
 * A list of birthdays in a file.
 *
 * The exchange with FamTM runs through a read-only provider, and on some phones that read is the one
 * thing that does not work - an older FamTM that publishes nothing yet, or an Android build that
 * hides one app from another. This is the same list carried by hand instead: a FamTM backup
 * (`family-tree-backup.json`, written by Transfer > Export everything over there) can be read here,
 * and this journal can write its own list out as a file of its own, so the birthdays can be moved to
 * another phone, or kept, without a full backup of every entry.
 *
 * Only a name and a day travel, which is all the provider ever hands over. A born date with no day
 * and month has no birthday to keep, and someone with a death date is not given one.
 */
internal object BirthdayFile {

    /** One person's birthday, and whether it came from FamTM or was typed in a journal. */
    class Birthday(
        val name: String,
        val month: Int,
        val day: Int,
        val year: Int,
        val fromFamTm: Boolean
    ) {
        /** MM-DD: the part that comes round every year, which is what a birthday is matched on. */
        val md: String = pad(month) + "-" + pad(day)

        /** A date the plans table accepts; a year is kept when one was given. */
        val date: String = (if (year in 1..9999) year else 2000).toString() + "-" + md
    }

    /** Everything one file held, and which app wrote it. */
    class Read(val list: List<Birthday>, val from: String)

    /**
     * The file this journal saves. `app` and `kind` are the marker a later import checks, `from` says
     * which list it was taken from, and every entry carries where it came from, so a birthday that
     * came across from FamTM is still one FamTM listed when the file is read back.
     */
    fun write(list: List<Birthday>, page: String, famTm: String, made: String): String {
        val arr = JSONArray()
        list.forEach { b ->
            arr.put(
                JSONObject()
                    .put("n", b.name)
                    .put("m", b.month)
                    .put("d", b.day)
                    .put("y", b.year)
                    .put("from", if (b.fromFamTm) FAMTM else HERE)
            )
        }
        return JSONObject()
            .put("app", "ujournal")
            .put("kind", "birthdays")
            .put("v", 1)
            .put("page", page)
            .put("made", made)
            .put("from", if (famTm.isEmpty()) "" else FAMTM + " " + famTm)
            .put("birthdays", arr)
            .toString(2)
    }

    /**
     * Any file that holds birthdays: one this journal wrote, a FamTM backup, or the bare array both
     * apps publish. Null when it is none of those - a journal backup, a photo, anything else - so the
     * page can say what it was given instead of quietly adding nothing.
     */
    fun read(text: String): Read? {
        val body = text.trim().removePrefix("\uFEFF").trim()
        if (body.isEmpty()) return null
        val parsed = runCatching { JSONTokener(body).nextValue() }.getOrNull() ?: return null
        return when (parsed) {
            is JSONArray -> provider(parsed)
            is JSONObject ->
                if (parsed.optJSONArray("birthdays") != null) journalFile(parsed)
                else if (parsed.optJSONArray("people") != null) famTmBackup(parsed)
                else null
            else -> null
        }
    }

    /** A file this journal wrote: `{"app":"ujournal","kind":"birthdays","birthdays":[...]}`. */
    private fun journalFile(o: JSONObject): Read {
        val arr = o.optJSONArray("birthdays") ?: JSONArray()
        val whole = o.optString("from").startsWith(FAMTM, true)
        val list = (0 until arr.length()).mapNotNull { i ->
            val b = arr.optJSONObject(i) ?: return@mapNotNull null
            val name = b.optString("n").ifBlank { b.optString("name") }.trim().take(80)
            val m = b.optInt("m")
            val d = b.optInt("d")
            if (name.isEmpty() || m !in 1..12 || d !in 1..31) null
            else Birthday(name, m, d, b.optInt("y"), whole || b.optString("from").equals(FAMTM, true))
        }
        return Read(list, if (whole) FAMTM else "")
    }

    /**
     * A FamTM backup: `{"app":"family-tree","people":[{"name":..,"birth":"1950-07-04",..}]}`. Only
     * the ones who are alive and whose born date has a day and a month - the same list FamTM's own
     * Birthdays page keeps, which is the list its provider publishes.
     */
    private fun famTmBackup(o: JSONObject): Read {
        val arr = o.optJSONArray("people") ?: JSONArray()
        val list = (0 until arr.length()).mapNotNull { i ->
            val p = arr.optJSONObject(i) ?: return@mapNotNull null
            if (p.optString("death").isNotBlank()) return@mapNotNull null
            val name = p.optString("name").ifBlank { p.optString("nick") }.trim().take(80)
            val at = date(p.optString("birth")) ?: return@mapNotNull null
            if (name.isEmpty()) null else Birthday(name, at[1], at[2], at[0], true)
        }
        return Read(list, FAMTM)
    }

    /** The bare array both providers publish: `[{"n":name,"m":month,"d":day,"y":year}]`. */
    private fun provider(arr: JSONArray): Read {
        val list = (0 until arr.length()).mapNotNull { i ->
            val b = arr.optJSONObject(i) ?: return@mapNotNull null
            val name = b.optString("n").trim().take(80)
            val m = b.optInt("m")
            val d = b.optInt("d")
            if (name.isEmpty() || m !in 1..12 || d !in 1..31) null
            else Birthday(name, m, d, b.optInt("y"), false)
        }
        return Read(list, "")
    }

    /**
     * A born date however FamTM writes one - 1950-07-04, --07-04 for a date with no year, 7/4,
     * 4 Jul 1950, Jul 4, 1950 - as [year, month, day], with the year 0 when there is none. Null for
     * a year on its own or a month with no day: neither has a day to keep.
     */
    private fun date(raw: String): IntArray? {
        val s = raw.trim()
        if (s.isEmpty()) return null
        Regex("^(\\d{4})-(\\d{1,2})-(\\d{1,2})$").find(s)?.let { m ->
            return at(m.groupValues[1].toInt(), m.groupValues[2].toInt(), m.groupValues[3].toInt())
        }
        Regex("^--(\\d{1,2})-(\\d{1,2})$").find(s)?.let { m ->
            return at(0, m.groupValues[1].toInt(), m.groupValues[2].toInt())
        }
        Regex("^(\\d{1,2})[/-](\\d{1,2})(?:[/-](\\d{4}))?$").find(s)?.let { m ->
            return at(m.groupValues[3].toIntOrNull() ?: 0, m.groupValues[1].toInt(), m.groupValues[2].toInt())
        }
        Regex("^(\\d{1,2})\\s+([A-Za-z]{3,9})\\.?,?\\s*(\\d{4})?$").find(s)?.let { m ->
            return at(m.groupValues[3].toIntOrNull() ?: 0, month(m.groupValues[2]), m.groupValues[1].toInt())
        }
        Regex("^([A-Za-z]{3,9})\\.?\\s+(\\d{1,2}),?\\s*(\\d{4})?$").find(s)?.let { m ->
            return at(m.groupValues[3].toIntOrNull() ?: 0, month(m.groupValues[1]), m.groupValues[2].toInt())
        }
        return null
    }

    /** A month by its name, or by the first three letters of one; 0 when it is not a month. */
    private fun month(word: String): Int =
        MONTHS.indexOf(word.lowercase().take(3)) + 1

    private fun at(year: Int, month: Int, day: Int): IntArray? =
        if (month !in 1..12 || day !in 1..31) null else intArrayOf(year, month, day)

    private fun pad(n: Int): String = (if (n < 10) "0" else "") + n

    private val MONTHS = listOf("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")

    private const val FAMTM = "FamTM"
    private const val HERE = "here"
}
