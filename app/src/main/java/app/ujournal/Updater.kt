package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** One published release: the version, where it can be read about and fetched, and what changed. */
data class Update(val version: String, val url: String, val notes: String)

/**
 * OTA updates: read what the newest release is, compare it with the version this build carries,
 * and - only when that release is newer - take the owner to it.
 *
 * The answer comes from a manifest published WITH the release — the same shape SideCut's
 * ota/updates.json, MeasureT's updates.json and FamTM's published page use: a version, the file,
 * its size and the notes for it. One fixed URL, so there is no API to rate-limit and no release tag
 * to parse, and the changelog travels with the build instead of being reconstructed on the phone.
 * The GitHub API and the releases feed stay behind it as fallbacks.
 *
 * WHAT IT NO LONGER DOES: download the update and install it. That needed
 * REQUEST_INSTALL_PACKAGES, and a sideloaded app that fetches code over the network and then asks
 * Android to install it is the shape Play Protect blocks — with the microphone a journal also
 * needs, it read the app as harmful. [browse] opens the release page in the browser instead; the
 * APK downloads there and the phone's own installer takes it from outside the app.
 */
object Updater {

    private const val TAG = "UJournalUpdater"

    private val repo get() = BuildConfig.GITHUB_REPO
    private fun manifestUrl() =
        "https://github.com/$repo/releases/latest/download/updates.json"
    private fun downloads() = "https://github.com/$repo/releases/download"
    private fun apiUrl() = "https://api.github.com/repos/$repo/releases/latest"
    private fun feedUrl() = "https://github.com/$repo/releases.atom"

    /** GitHub answers 403 to a request with no User-Agent, so one is always sent. */
    private fun open(url: String): HttpURLConnection =
        (URL(url).openConnection() as HttpURLConnection).apply {
            setRequestProperty("User-Agent", "UJournal/" + BuildConfig.VERSION_NAME)
            connectTimeout = 12000
            readTimeout = 25000
            instanceFollowRedirects = true
        }

    suspend fun check(): Update? = withContext(Dispatchers.IO) {
        val manifest = manifestJson()
        if (manifest != null) return@withContext fromManifest(manifest)
        val json = apiJson()
        if (json != null) fromJson(json) else fromFeed()
    }

    private fun manifestJson(): String? = try {
        val c = open(manifestUrl())
        val code = c.responseCode
        if (code == 200) c.inputStream.bufferedReader().use { it.readText() } else {
            Log.w(TAG, "no manifest at the newest release ($code)")
            null
        }
    } catch (e: Exception) {
        Log.w(TAG, "manifest unreachable: ${e.javaClass.simpleName}")
        null
    }

    /** {"version","apk","size","notes","date"} — the manifest every app here publishes. */
    private fun fromManifest(text: String): Update? = try {
        val j = JSONObject(text)
        val v = j.optString("version").removePrefix("v")
        val apk = j.optString("apk")
        when {
            v.isEmpty() || apk.isEmpty() -> {
                Log.w(TAG, "the manifest names no version or no APK")
                null
            }
            !newer(v, BuildConfig.VERSION_NAME) -> null
            else -> {
                val notes = j.optJSONArray("notes")?.let { a ->
                    (0 until a.length()).joinToString("\n") { a.optString(it) }
                } ?: ""
                Update(v, "${downloads()}/v$v/$apk", notes)
            }
        }
    } catch (e: Exception) {
        Log.w(TAG, "unreadable manifest: ${e.javaClass.simpleName}")
        null
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
                    "${downloads()}/$tag/UJournal-$v.apk",
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

    /**
     * Where the update is actually taken from: the release page, opened in the browser.
     *
     * The app used to download the APK into its cache and hand it to Android's installer through a
     * FileProvider. That hand-off is what REQUEST_INSTALL_PACKAGES is for, and it is what made Play
     * Protect read the journal as harmful: fetching code and asking to install it is the dropper
     * signature. Now the browser downloads the file and the phone's own installer, a different app
     * with its own consent screen, installs it.
     */
    fun browse(ctx: Context, u: Update) {
        try {
            ctx.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(page(u)))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (e: Exception) {
            Log.w(TAG, "no browser for ${u.url}: ${e.javaClass.simpleName}")
            Toast.makeText(ctx, "No browser on this phone to open the release", Toast.LENGTH_LONG)
                .show()
        }
    }

    /** The release page, which carries the APK and the notes beside it. */
    private fun page(u: Update) = "https://github.com/$repo/releases/tag/v${u.version}"
}
