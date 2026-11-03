package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import android.util.Log
import android.widget.Toast
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

data class Update(val version: String, val url: String, val notes: String)

/**
 * OTA updates: checks the latest GitHub Release, downloads the APK, hands it to the installer.
 *
 * Two things a phone does that a laptop never shows: it may be behind a carrier gateway that shares
 * one address with thousands of other people, so api.github.com's anonymous allowance is used up by
 * strangers, and its HTTP stack's default headers are not guaranteed. Both are handled here - the
 * request says who it is, and a refused API call falls back to the repository's releases feed, which
 * has no limit and needs no credentials.
 */
object Updater {

    private const val TAG = "UJournalUpdater"

    private fun apiUrl() = "https://api.github.com/repos/${BuildConfig.GITHUB_REPO}/releases/latest"
    private fun feedUrl() = "https://github.com/${BuildConfig.GITHUB_REPO}/releases.atom"

    /** GitHub answers 403 to a request with no User-Agent, so one is always sent. */
    private fun open(url: String): HttpURLConnection =
        (URL(url).openConnection() as HttpURLConnection).apply {
            setRequestProperty("User-Agent", "UJournal/" + BuildConfig.VERSION_NAME)
            connectTimeout = 12000
            readTimeout = 25000
            instanceFollowRedirects = true
        }

    suspend fun check(): Update? = withContext(Dispatchers.IO) {
        val json = apiJson()
        if (json != null) fromJson(json) else fromFeed()
    }

    private fun apiJson(): String? = try {
        val c = open(apiUrl())
        c.setRequestProperty("Accept", "application/vnd.github+json")
        val code = c.responseCode
        if (code == 200) c.inputStream.bufferedReader().use { it.readText() } else {
            Log.w(TAG, "api answered $code, reading the feed instead")
            null
        }
    } catch (e: Exception) {
        Log.w(TAG, "api unreachable: ${e.javaClass.simpleName}")
        null
    }

    private fun fromJson(text: String): Update? = try {
        val j = JSONObject(text)
        val tag = j.getString("tag_name").removePrefix("v")
        val url = apkOf(j.getJSONArray("assets"))
        when {
            url == null -> {
                Log.w(TAG, "release $tag has no APK attached")
                null
            }
            !newer(tag, BuildConfig.VERSION_NAME) -> null
            else -> Update(tag, url, j.optString("body"))
        }
    } catch (e: Exception) {
        Log.w(TAG, "unreadable release: ${e.javaClass.simpleName}")
        null
    }

    /** The release APK rather than the debug one, which would install over a release build. */
    private fun apkOf(assets: JSONArray): String? {
        var debug: String? = null
        for (i in 0 until assets.length()) {
            val a = assets.optJSONObject(i) ?: continue
            val name = a.optString("name")
            if (!name.endsWith(".apk")) continue
            val url = a.optString("browser_download_url")
            if (url.isEmpty()) continue
            if (name.contains("debug", ignoreCase = true)) debug = url else return url
        }
        return debug
    }

    /** The newest tag from the releases feed, plus the URL release.yml names after that tag. */
    private fun fromFeed(): Update? = try {
        val c = open(feedUrl())
        if (c.responseCode != 200) {
            Log.w(TAG, "feed answered ${c.responseCode}")
            null
        } else {
            val xml = c.inputStream.bufferedReader().use { it.readText() }
            val tag = Regex("/releases/tag/([^\"]+)").find(xml)?.groupValues?.get(1)
            if (tag == null) {
                Log.w(TAG, "the feed lists no release")
                null
            } else {
                val v = tag.removePrefix("v")
                if (!newer(v, BuildConfig.VERSION_NAME)) null
                else Update(
                    v,
                    "https://github.com/${BuildConfig.GITHUB_REPO}/releases/download/$tag/UJournal-$v.apk",
                    "Published on GitHub."
                )
            }
        }
    } catch (e: Exception) {
        Log.w(TAG, "feed unreadable: ${e.javaClass.simpleName}")
        null
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
        val dir = File(ctx.cacheDir, "updates").apply { mkdirs() }
        val f = File(dir, "UJournal.apk")
        var ok = false
        try {
            val c = open(u.url)
            val code = c.responseCode
            if (code != 200) {
                Log.w(TAG, "download answered $code")
            } else {
                c.inputStream.use { i -> f.outputStream().use { o -> i.copyTo(o) } }
                // An error page saved as an APK reaches Android as "there was a problem parsing
                // the package", so the file has to look like one: a zip, and not tiny.
                ok = f.length() > 20_000L &&
                    f.inputStream().use { it.read() == 0x50 && it.read() == 0x4B }
                if (!ok) Log.w(TAG, "${f.length()} bytes arrived that are not an APK")
            }
        } catch (e: Exception) {
            Log.w(TAG, "download failed: ${e.javaClass.simpleName}")
        }
        // A half file handed to the installer next time fails there, with no way to tell why.
        if (!ok) f.delete()
        ok
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
