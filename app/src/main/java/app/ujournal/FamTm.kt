package app.ujournal

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
 * Everything here fails quietly. FamTM may not be installed, may be an older copy with no provider,
 * or may have nobody with a birthday recorded; in each case the journal simply has no birthdays to
 * offer, which is the same thing the reader sees.
 */
internal object FamTm {

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

    private val URI: Uri = Uri.parse("content://com.FamTM.app.birthdays/list")

    /** Whether FamTM answers at all, so a caller can tell "none" from "not here". */
    fun installed(ctx: Context): Boolean = try {
        ctx.contentResolver.query(URI, null, null, null, null)?.use { true } ?: false
    } catch (e: Exception) {
        false
    }

    /** The list FamTM publishes, or null when it is not installed, has no provider, or has none. */
    fun birthdays(ctx: Context): List<Birthday>? = try {
        val c = ctx.contentResolver.query(URI, null, null, null, null) ?: return null
        c.use { cur ->
            if (!cur.moveToFirst()) return null
            val i = cur.getColumnIndex("json")
            if (i < 0) return null
            val arr = JSONArray(cur.getString(i))
            (0 until arr.length()).mapNotNull { k ->
                val o = arr.optJSONObject(k) ?: return@mapNotNull null
                val name = o.optString("n").trim().take(80)
                val m = o.optInt("m")
                val d = o.optInt("d")
                if (name.isEmpty() || m !in 1..12 || d !in 1..31) null
                else Birthday(name, m, d, o.optInt("y"))
            }
        }
    } catch (e: Exception) {
        null
    }
}
