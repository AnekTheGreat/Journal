package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import android.widget.Toast
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

data class Update(val version: String, val url: String, val notes: String)

/** OTA updates: checks the latest GitHub Release, downloads the APK, hands it to the installer. */
object Updater {
    suspend fun check(): Update? = withContext(Dispatchers.IO) {
        try {
            val c = URL("https://api.github.com/repos/${BuildConfig.GITHUB_REPO}/releases/latest")
                .openConnection() as HttpURLConnection
            c.setRequestProperty("Accept", "application/vnd.github+json")
            c.connectTimeout = 8000; c.readTimeout = 8000
            val j = JSONObject(c.inputStream.bufferedReader().readText())
            val tag = j.getString("tag_name").removePrefix("v")
            val assets = j.getJSONArray("assets")
            var url: String? = null
            for (i in 0 until assets.length()) {
                val a = assets.getJSONObject(i)
                if (a.getString("name").endsWith(".apk")) url = a.getString("browser_download_url")
            }
            if (url != null && newer(tag, BuildConfig.VERSION_NAME)) Update(tag, url, j.optString("body")) else null
        } catch (e: Exception) { null }
    }

    private fun newer(a: String, b: String): Boolean {
        val x = a.split(".").map { it.toIntOrNull() ?: 0 }
        val y = b.split(".").map { it.toIntOrNull() ?: 0 }
        for (i in 0 until maxOf(x.size, y.size)) {
            val p = x.getOrElse(i) { 0 }; val q = y.getOrElse(i) { 0 }
            if (p != q) return p > q
        }
        return false
    }

    /** Returns false (and opens the settings page) if the user hasn't allowed installs yet. */
    fun ensurePermission(ctx: Context): Boolean {
        if (ctx.packageManager.canRequestPackageInstalls()) return true
        ctx.startActivity(
            Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:${ctx.packageName}"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
        Toast.makeText(ctx, "Allow installs for UJournal, then tap Update again", Toast.LENGTH_LONG).show()
        return false
    }

    suspend fun download(ctx: Context, u: Update): Boolean = withContext(Dispatchers.IO) {
        runCatching {
            val dir = File(ctx.cacheDir, "updates").apply { mkdirs() }
            val f = File(dir, "UJournal.apk")
            val c = URL(u.url).openConnection() as HttpURLConnection
            c.inputStream.use { i -> f.outputStream().use { o -> i.copyTo(o) } }
            true
        }.getOrDefault(false)
    }

    fun install(ctx: Context) {
        val f = File(File(ctx.cacheDir, "updates"), "UJournal.apk")
        val uri = FileProvider.getUriForFile(ctx, "${ctx.packageName}.files", f)
        ctx.startActivity(
            Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive")
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }
}
