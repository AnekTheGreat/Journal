package app.ujournal

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.view.WindowInsets
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.Toast
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate

// The paper tone the page paints, shown while it loads and behind the system bars.
private val BG = Color.parseColor("#F4EBDD")
private val BG_BAR = Color.parseColor("#FBF6EC")

/**
 * The shell: one WebView, one bridge, and the update that keeps the screen current.
 *
 * The screen itself is `assets/index.html` - the same shape SideCut, MeasureT, My Hub and FamTM have
 * - so a wording change, a new sheet or a different calendar ships by replacing that file over the
 * air. The APK only changes when this file does: it holds the bridge that reads and writes the
 * entries, opens the pickers, runs the recorder and performs the update.
 *
 * Three things guard the phone, because the one failure that matters is a journal that opens to a
 * blank screen and cannot reach the entries behind it:
 *
 *  - [PageStore] refuses a download without the marker or without the promised version.
 *  - A page has to call back `ready()` after drawing. If it does not within [WATCHDOG] ms the stored
 *    copy is deleted and the bundled one is loaded, so the worst an update can do is put the
 *    shipped screen back on the phone.
 *  - A newly installed APK deletes an older stored page before anything is drawn.
 */
class MainActivity : Activity() {

    private lateinit var frame: FrameLayout
    private lateinit var web: WebView
    private lateinit var bridge: Bridge
    private lateinit var store: Store
    private val main = Handler(Looper.getMainLooper())

    /** Set by the page's `ready()`, cleared on every load. */
    private var ready = false

    /** True once the bundled page has been tried, so a broken build cannot reload for ever. */
    private var fellBack = false
    private var watchdog: Runnable? = null

    /** The day a picker was opened for, and the file a camera was told to write. */
    private var pickDate: String? = null
    private var captureUri: Uri? = null

    private var recorder: MediaRecorder? = null
    private var recordFile: File? = null
    private var recordDate: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = Store(applicationContext)
        // A page stored by an older install is dropped: the APK on the phone is the newer thing.
        PageStore.dropStale(this)

        frame = FrameLayout(this).apply { setBackgroundColor(BG) }
        web = WebView(this).apply {
            setBackgroundColor(BG)
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            // The page is served from the app's own storage and draws thumbnails straight from the
            // day's folder, so file access is the point. content:// from other apps stays off.
            settings.allowFileAccess = true
            settings.allowFileAccessFromFileURLs = true
            settings.allowContentAccess = false
            webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView?, url: String?) = watch()

                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: WebResourceError?
                ) {
                    // A stored page that will not even load is the same case as one that never
                    // draws: the next load uses the bundled copy.
                    if (request?.isForMainFrame == true) watch()
                }
            }
        }
        bridge = Bridge(this)
        web.addJavascriptInterface(bridge, "Journal")
        frame.addView(
            web,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        )
        setContentView(frame)
        bars()
        loadPage()
        // One quiet check per launch. It only speaks when something newer exists, so a journal that
        // is current - or offline - opens exactly as it did before updates existed.
        checkUpdates(silent = true)
    }

    /** Coming back is when an attachment may have landed, so the page redraws the list. */
    override fun onResume() {
        super.onResume()
        eval("window.journalResume&&window.journalResume()")
    }

    /** Whatever was typed belongs on disk even if the page never blurs the field. */
    override fun onPause() {
        eval("window.journalFlush&&window.journalFlush()")
        super.onPause()
    }

    override fun onDestroy() {
        recorder?.let { r -> runCatching { r.stop() }; runCatching { r.release() } }
        recorder = null
        super.onDestroy()
    }

    /**
     * The page decides first: an open sheet, an open day or the other tab all close before the
     * journal does. Only when it says it did not handle the press does the activity finish.
     */
    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (!::web.isInitialized) {
            super.onBackPressed()
            return
        }
        web.evaluateJavascript("(window.journalBack&&journalBack())?'yes':'no'") { r ->
            if (r == null || !r.contains("yes")) finish()
        }
    }

    // ---- the page ----

    /** Load the stored page when there is one, the bundled page otherwise. */
    fun loadPage() {
        ready = false
        val url = if (PageStore.stored(this)) "file://" + PageStore.path(this)
        else "file:///android_asset/index.html"
        web.loadUrl(url)
    }

    /** Start, or restart, the wait for the page to say it has drawn. */
    private fun watch() {
        ready = false
        watchdog?.let { main.removeCallbacks(it) }
        val check = Runnable { if (!ready) fallback() }
        watchdog = check
        main.postDelayed(check, WATCHDOG)
    }

    /** The page called `ready()`: it is a working screen, and the wait is over. */
    fun pageReady() {
        ready = true
        watchdog?.let { main.removeCallbacks(it) }
    }

    /**
     * The page loaded but never drew - a script error in a downloaded copy, most likely. The stored
     * copy is thrown away and the bundled one is loaded, which is the whole reason an over-the-air
     * page is safe to keep: it can always be taken back.
     */
    private fun fallback() {
        if (fellBack) return
        fellBack = true
        if (PageStore.stored(this)) {
            PageStore.clear(this)
            eval("JR&&JR.toast('UJournal went back to the screen it ships with')")
            loadPage()
        } else {
            toast("UJournal could not draw its screen")
        }
    }

    /** Run a statement in the page. Safe to call from any thread, and before the page exists. */
    fun eval(js: String) = runOnUiThread {
        if (::web.isInitialized) web.evaluateJavascript(js, null)
    }

    fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_SHORT).show()

    // ---- attaching ----

    /**
     * A picker for one day: the photo picker, audio, any file, or one of the two cameras. The answer
     * comes back in [onActivityResult], because this is a plain Activity and the bridge calls in
     * from the WebView's own thread.
     */
    fun pick(date: String, kind: String) {
        pickDate = date
        captureUri = null
        val i = when (kind) {
            "photo" -> capture(MediaStore.ACTION_IMAGE_CAPTURE, "Photo_", ".jpg")
            "video" -> capture(MediaStore.ACTION_VIDEO_CAPTURE, "Video_", ".mp4")
            "audio" -> document("audio/*")
            "file" -> document("*/*")
            else -> document("*/*").putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("image/*", "video/*"))
        }
        try {
            startActivityForResult(i, REQ_PICK)
        } catch (e: Exception) {
            pickDate = null
            eval("JR&&JR.toast('Nothing on this phone can pick that')")
        }
    }

    private fun document(type: String) = Intent(Intent.ACTION_OPEN_DOCUMENT)
        .addCategory(Intent.CATEGORY_OPENABLE)
        .setType(type)
        .putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)

    /** A camera writes into the app's cache and hands the file back through the provider. */
    private fun capture(action: String, prefix: String, ext: String): Intent {
        val f = File(File(cacheDir, "capture").apply { mkdirs() }, prefix + System.currentTimeMillis() + ext)
        val uri = FileProvider.getUriForFile(this, "$packageName.files", f)
        captureUri = uri
        return Intent(action)
            .putExtra(MediaStore.EXTRA_OUTPUT, uri)
            .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQ_PICK) return
        val date = pickDate ?: return
        val uris = ArrayList<Uri>()
        val clip = data?.clipData
        if (clip != null) {
            for (i in 0 until clip.itemCount) clip.getItemAt(i)?.uri?.let { uris.add(it) }
        }
        data?.data?.let { if (!uris.contains(it)) uris.add(it) }
        if (uris.isEmpty() && resultCode == RESULT_OK) captureUri?.let { uris.add(it) }
        pickDate = null
        captureUri = null
        attachFrom(date, uris)
    }

    /** Copy whatever was picked into the day's own folder, then ask the page to draw it again. */
    private fun attachFrom(date: String, uris: List<Uri>) {
        if (uris.isEmpty()) return
        Thread {
            runCatching {
                val d = LocalDate.parse(date)
                val e = store.load(d)
                store.save(store.attach(e, uris))
            }
            eval("window.JR&&JR.attach(" + JSONObject.quote(date) + ")")
        }.start()
    }

    // ---- recording ----

    /**
     * The microphone is a runtime permission, so the first tap asks for it and says why nothing
     * started: the page tells the owner to tap again once it is allowed.
     */
    fun startRecording(date: String): Boolean {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQ_MIC)
            return false
        }
        val f = File(File(cacheDir, "capture").apply { mkdirs() }, "Audio_${System.currentTimeMillis()}.m4a")
        val r = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) MediaRecorder(this)
        else @Suppress("DEPRECATION") MediaRecorder()
        return try {
            r.setAudioSource(MediaRecorder.AudioSource.MIC)
            r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            r.setOutputFile(f.absolutePath)
            r.prepare()
            r.start()
            recorder = r
            recordFile = f
            recordDate = date
            true
        } catch (e: Exception) {
            runCatching { r.release() }
            eval("JR&&JR.toast('Could not start recording')")
            false
        }
    }

    /** Stop the recorder; [save] keeps what was captured and attaches it to [date] ([null] = cancel). */
    fun stopRecording(date: String?, save: Boolean) {
        val r = recorder ?: return
        recorder = null
        runCatching { r.stop() }
        runCatching { r.release() }
        val f = recordFile
        val d = date ?: recordDate
        recordFile = null
        recordDate = null
        if (save && f != null && f.length() > 0L && d != null) {
            attachFrom(d, listOf(FileProvider.getUriForFile(this, "$packageName.files", f)))
        }
    }

    /** Hand an attachment to whatever app can open it, through the provider, read-only. */
    fun openAttachment(date: String, name: String) {
        val d = runCatching { LocalDate.parse(date) }.getOrNull() ?: return
        val a = store.load(d).atts.firstOrNull { it.name == name } ?: return
        val uri = runCatching {
            FileProvider.getUriForFile(this, "$packageName.files", store.file(d, a))
        }.getOrNull() ?: return
        val i = Intent(Intent.ACTION_VIEW)
            .setDataAndType(uri, a.mime)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        try {
            startActivity(i)
        } catch (e: Exception) {
            eval("JR&&JR.toast('No app can open this file')")
        }
    }

    // ---- updates ----

    /**
     * Ask GitHub what is newest and offer it. A page update is the ordinary kind: the screen is a
     * web page, so it is fetched and swapped in place with nothing installed. The APK is offered
     * only when the shell itself changed, and never to a copy Play delivered.
     */
    fun checkUpdates(silent: Boolean) {
        if (!silent) eval("JR&&JR.toast('Checking for updates\u2026')")
        Updater.checkAsync { update -> runOnUiThread { offered(update, silent) } }
    }

    private fun offered(update: Update?, silent: Boolean) {
        val page = PageStore.running(this)
        if (update != null && update.page != null && Updater.newer(update.version, page)) {
            eval("JR&&JR.update(" + offer(update, "page") + ")")
            return
        }
        if (update != null && !Updater.fromPlay(this) &&
            Updater.newer(update.version, BuildConfig.VERSION_NAME)
        ) {
            eval("JR&&JR.update(" + offer(update, "app") + ")")
            return
        }
        if (!silent) eval("JR&&JR.toast(" + JSONObject.quote("UJournal $page is the newest there is") + ")")
    }

    /** What the update sheet is given: what changed, and where the new page or release comes from. */
    private fun offer(update: Update, kind: String): String {
        val notes = JSONArray()
        update.notes.lines()
            .map { it.trim().removePrefix("-").trim() }
            .filter { it.isNotEmpty() }
            .take(8)
            .forEach { notes.put(it) }
        return JSONObject()
            .put("kind", kind)
            .put("version", update.version)
            .put("notes", notes)
            .put("url", if (kind == "page") update.page ?: "" else Updater.releasePage(update))
            .toString()
    }

    /**
     * Fetch the page a release published and put it in place. Nothing is installed and no package is
     * touched: this writes one file into the app's own storage and loads it.
     */
    fun applyPage(url: String, version: String) {
        Thread {
            val bytes = Updater.download(url)
            val saved = bytes != null && PageStore.save(this, bytes, version)
            runOnUiThread {
                if (saved) {
                    loadPage()
                    main.postDelayed({ eval("JR&&JR.toast('Updated to $version')") }, 1500)
                } else {
                    eval("JR&&JR.toast('That update did not arrive in one piece')")
                }
            }
        }.start()
    }

    /** Where a build that changed the shell is fetched from: the browser, or the Play listing. */
    fun openRelease(version: String) {
        if (Updater.fromPlay(this)) {
            Updater.openStore(this)
            return
        }
        try {
            startActivity(
                Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse("https://github.com/${BuildConfig.GITHUB_REPO}/releases/tag/v$version")
                )
            )
        } catch (e: Exception) {
            eval("JR&&JR.toast('No browser on this phone to open the release')")
        }
    }

    // ---- the bars ----

    /**
     * From Android 15 the system draws every app edge to edge and there is no opt-out at API 36, so
     * the page is padded by the bars and the keyboard instead of being drawn under them. Below API
     * 30 nothing forces it, and the layout keeps the insets itself.
     */
    private fun bars() {
        window.statusBarColor = BG
        window.navigationBarColor = BG_BAR
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
            frame.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(
                    WindowInsets.Type.systemBars() or WindowInsets.Type.ime()
                )
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
    }

    private companion object {
        /** How long a page gets to draw before the bundled copy is put back. */
        const val WATCHDOG = 9000L
        const val REQ_PICK = 41
        const val REQ_MIC = 42
    }
}
