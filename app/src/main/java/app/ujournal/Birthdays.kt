package app.ujournal

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject

/**
 * UJournal's birthdays, published the same way FamTM publishes its own.
 *
 * FamTM hands its list over at `content://com.FamTM.app.birthdays/list`, which made the exchange one
 * way: the journal could read the family's birthdays and FamTM could never see the ones typed here.
 * This is the other half of the same contract - `content://app.ujournal.birthdays/list`, one row
 * whose `json` column is `[{"n":name,"m":month,"d":day,"y":year}]` - so either app can be the one
 * that knows a birthday.
 *
 * Read-only on purpose: a query answers, and insert, update and delete do nothing. Only a name and a
 * day of the year are published, which is exactly what FamTM publishes and all a birthday reminder
 * needs; nothing else in the journal is reachable through here.
 */
class Birthdays : ContentProvider() {

    override fun onCreate(): Boolean = true

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?
    ): Cursor {
        val cursor = MatrixCursor(arrayOf("json"))
        cursor.addRow(arrayOf(list().toString()))
        return cursor
    }

    /** Every birthday in this journal, in the shape FamTM already reads from its own provider. */
    private fun list(): JSONArray {
        val arr = JSONArray()
        val ctx = context ?: return arr
        runCatching {
            Store(ctx).plans()
                .filter { it.kind == "birthday" && it.title.isNotBlank() }
                .forEach { p ->
                    val md = p.start.takeLast(5)
                    arr.put(
                        JSONObject()
                            .put("n", p.title)
                            .put("m", md.take(2).toIntOrNull() ?: 0)
                            .put("d", md.takeLast(2).toIntOrNull() ?: 0)
                            .put("y", p.start.take(4).toIntOrNull() ?: 0)
                    )
                }
        }
        return arr
    }

    override fun getType(uri: Uri): String = "vnd.android.cursor.dir/vnd.ujournal.birthdays"

    override fun insert(uri: Uri, values: ContentValues?): Uri? = null

    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = 0

    override fun update(
        uri: Uri,
        values: ContentValues?,
        selection: String?,
        selectionArgs: Array<out String>?
    ): Int = 0
}
