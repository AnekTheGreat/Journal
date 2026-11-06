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
