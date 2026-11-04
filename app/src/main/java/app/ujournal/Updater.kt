package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.util.Log
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * One published release: the version, where it can be read about, what changed, and the page that
 * release published - the screen itself, which this shell can take without Play and without an
 * installer.
 */
data class Update(val version: String, val url: String, val notes: String, val page: String?)

/**
 * OTA updates, in two halves now.
 *
 * The first half is the screen. A release publishes `page_url`, and a copy that finds it newer than
 * the page it is drawing fetches it and swaps it in place - the same thing SideCut, MeasureT, My Hub
 * and FamTM do. Nothing is installed, so Play Protect has nothing to read as a dropper, and a
 * wording change no longer costs an install.
 *
 * The second half is the app itself, for a release that changed the shell. That is still taken from
 * the release page in the browser, because downloading an APK and handing it to Android's installer
 * is what REQUEST_INSTALL_PACKAGES exists for and what made Play Protect flag a journal that also
 * asks for the microphone. A copy Play delivered is offered neither: Play updates that one.
 *
 * The answer comes from a manifest published WITH the release - the same shape SideCut's
 * ota/updates.json, MeasureT's updates.json and FamTM's published page use: a version, the file,
 * its size and the notes for it. One fixed URL, so there is no API to rate-limit and no release tag
 * to parse, and the changelog travels with the build instead of being reconstructed on the phone.
 * The GitHub API and the releases feed stay behind it as fallbacks.
 */
object Updater {

    private const val TAG = "UJournalUpdater"

    /** The page is about 20 KB, so a download anywhere near this is a wrong URL, not an update. */
    private const val MAX_PAGE = 4 * 1024 * 1024

    private val repo get() = BuildConfig.GITHUB_REPO
    private fun manifestUrl() =
        "https://github.com/$repo/releases/latest/download/updates.json"
    private fun downloads() = "https://github.com/$repo/releases/download"
    private fun apiUrl() = "https://api.github.com/repos/$repo/releases/latest"
    private fun feedUrl() = "https://github.com/$repo/releases.atom"

    /**
     * GitHub answers 403 to a request with no User-Agent, so one is always sent.
     *
     * The timeouts are short on purpose. Every URL here redirects - `releases/latest/download` to a
     * signed asset host, an asset to its own CDN - and a phone on a weak signal would sit on a
     * stalled connection for the old 12s/25s while the journal looked like it was doing nothing.
     * Four and eight seconds are still generous for a 1 KB manifest and a 42 KB page on a working
     * connection, and if they do run out the check simply says nothing and tries again later.
     */
    private fun open(url: String): HttpURLConnection =
        (URL(url).openConnection() as HttpURLConnection).apply {
            setRequestProperty("User-Agent", "UJournal/" + BuildConfig.VERSION_NAME)
            setRequestProperty("Accept-Encoding", "identity")
            connectTimeout = 4000
            readTimeout = 8000
            instanceFollowRedirects = true
        }

    /** The check, off the main thread: the bridge and the launch both run it inside a Thread. */
    fun checkAsync(done: (Update?) -> Unit) {
        Thread { done(check()) }.start()
    }

    private fun check(): Update? {
        val manifest = manifestJson()
        if (manifest != null) return fromManifest(manifest)
        val json = apiJson()
        if (json != null) return fromJson(json)
        return fromFeed()
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

    /** {"version","apk","size","notes","page_url"} - the manifest every app here publishes. */
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
                // The screen a release published, pinned to its tag, so a page is always the page
                // that shipped with the version it claims - not whatever is on the branch today.
                val page = j.optString("page_url").takeIf { it.startsWith("https://") }
                Update(v, "${downloads()}/v$v/$apk", notes, page)
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
            else -> Update(tag, url, j.optString("body"), null)
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
                    "Published on GitHub.",
                    null
                )
            }
        }
    } catch (e: Exception) {
        Log.w(TAG, "feed unreadable: ${e.javaClass.simpleName}")
        null
    }

    /** A new screen: the page a release published, read to the cap and no further. */
    fun download(url: String): ByteArray? = try {
        val c = open(url)
        val code = c.responseCode
        if (code != 200) {
            Log.w(TAG, "page download answered $code")
            null
        } else {
            c.inputStream.use { input ->
                val out = ByteArrayOutputStream()
                val buf = ByteArray(16 * 1024)
                var total = 0
                while (true) {
                    val n = input.read(buf)
                    if (n < 0) break
                    total += n
                    if (total > MAX_PAGE) break
                    out.write(buf, 0, n)
                }
                if (total > MAX_PAGE) {
                    Log.w(TAG, "the page is larger than any page this app publishes")
                    null
                } else {
                    out.toByteArray()
                }
            }
        }
    } catch (e: Exception) {
        Log.w(TAG, "page unusable: ${e.javaClass.simpleName}")
        null
    }

    fun newer(a: String, b: String): Boolean {
        val x = a.split(".").map { it.toIntOrNull() ?: 0 }
        val y = b.split(".").map { it.toIntOrNull() ?: 0 }
        for (i in 0 until maxOf(x.size, y.size)) {
            val p = x.getOrElse(i) { 0 }
            val q = y.getOrElse(i) { 0 }
            if (p != q) return p > q
        }
        return false
    }

    /**
     * True when this copy was installed by the Play Store.
     *
     * A Play copy is updated by Play, so the journal must not offer it a download: store policy is
     * that a Play-distributed app does not send its users to an APK, and the APK on the release
     * page is signed with the upload key rather than the key Play delivers under - so it could not
     * install over the store build anyway.
     */
    fun fromPlay(ctx: Context): Boolean = try {
        val pm = ctx.packageManager
        val installer = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            pm.getInstallSourceInfo(ctx.packageName).installingPackageName
        } else {
            @Suppress("DEPRECATION")
            pm.getInstallerPackageName(ctx.packageName)
        }
        installer == "com.android.vending"
    } catch (e: Exception) {
        Log.w(TAG, "installer unknown: ${e.javaClass.simpleName}")
        false
    }

    /** The Play listing for this build. Play performs the update; the journal only opens it. */
    fun openStore(ctx: Context) {
        val id = ctx.packageName
        val flags = Intent.FLAG_ACTIVITY_NEW_TASK
        try {
            ctx.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$id")).addFlags(flags)
            )
        } catch (e: Exception) {
            try {
                ctx.startActivity(
                    Intent(
                        Intent.ACTION_VIEW,
                        Uri.parse("https://play.google.com/store/apps/details?id=$id")
                    ).addFlags(flags)
                )
            } catch (e2: Exception) {
                Log.w(TAG, "no Play Store for $id: ${e2.javaClass.simpleName}")
                Toast.makeText(ctx, "No Play Store on this phone", Toast.LENGTH_LONG).show()
            }
        }
    }

    /** The release page, which carries the notes and the APK beside them. */
    fun releasePage(u: Update) = "https://github.com/$repo/releases/tag/v${u.version}"
}
