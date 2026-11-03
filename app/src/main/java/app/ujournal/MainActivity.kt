package app.ujournal

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.os.Build
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import coil.Coil
import coil.ImageLoader
import coil.compose.AsyncImage
import coil.decode.VideoFrameDecoder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.time.format.TextStyle as JTextStyle
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Coil.setImageLoader(ImageLoader.Builder(this).components { add(VideoFrameDecoder.Factory()) }.build())
        val store = Store(applicationContext)
        setContent { UTheme { App(store) } }
    }
}

@Composable
fun App(store: Store) {
    var open by remember { mutableStateOf<LocalDate?>(null) }
    var tab by remember { mutableIntStateOf(0) }
    var rev by remember { mutableIntStateOf(0) }
    var update by remember { mutableStateOf<Update?>(null) }
    LaunchedEffect(Unit) { update = Updater.check() }

    val day = open
    if (day != null) {
        DayScreen(store, day) { open = null; rev++ }
    } else {
        val entries = remember(rev) { store.all() }
        val nc = NavigationBarItemDefaults.colors(indicatorColor = Sand)
        Scaffold(
            containerColor = Bg,
            bottomBar = {
                NavigationBar(containerColor = CardC) {
                    NavigationBarItem(tab == 0, { tab = 0 }, { Text("📖") }, label = { Text("Journal") }, colors = nc)
                    NavigationBarItem(tab == 1, { tab = 1 }, { Text("📅") }, label = { Text("Calendar") }, colors = nc)
                }
            },
            floatingActionButton = {
                FloatingActionButton({ open = LocalDate.now() }, containerColor = Tan, contentColor = Color.White) {
                    Text("＋", fontSize = 26.sp)
                }
            }
        ) { pad ->
            Box(Modifier.padding(pad)) {
                if (tab == 0) Timeline(entries, store) { open = it }
                else CalendarView(entries.map { it.date }.toSet()) { open = it }
            }
        }
    }
    update?.let { u -> UpdateDialog(u) { update = null } }
}

@Composable
fun UpdateDialog(u: Update, onDismiss: () -> Unit) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var busy by remember { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = { if (!busy) onDismiss() },
        containerColor = CardC,
        title = { Text("Update available", fontFamily = FontFamily.Serif) },
        text = { Text("UJournal ${u.version} is ready." + if (u.notes.isNotBlank()) "\n\n" + u.notes.take(300) else "") },
        confirmButton = {
            TextButton(enabled = !busy, onClick = {
                if (!Updater.ensurePermission(ctx)) return@TextButton
                busy = true
                scope.launch {
                    val ok = Updater.download(ctx, u)
                    busy = false
                    if (ok) Updater.install(ctx)
                    else Toast.makeText(ctx, "Download failed", Toast.LENGTH_SHORT).show()
                }
            }) { Text(if (busy) "Downloading…" else "Update", color = Ink) }
        },
        dismissButton = { TextButton(enabled = !busy, onClick = onDismiss) { Text("Later", color = Muted) } }
    )
}

@Composable
fun Timeline(entries: List<Entry>, store: Store, onOpen: (LocalDate) -> Unit) {
    if (entries.isEmpty()) {
        Column(
            Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("Your journal is waiting.\nTap ＋ to write today.", textAlign = TextAlign.Center,
                color = Muted, fontFamily = FontFamily.Serif, fontSize = 18.sp)
            Spacer(Modifier.height(26.dp))
            SupportCard()
        }
        return
    }
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        entries.groupBy { it.date.year }.forEach { (y, ye) ->
            item(key = "y$y") {
                Text("$y", fontSize = 34.sp, fontFamily = FontFamily.Serif, color = Ink, modifier = Modifier.padding(top = 12.dp))
            }
            ye.groupBy { it.date.month }.forEach { (m, me) ->
                item(key = "m$y-$m") {
                    Text(m.getDisplayName(JTextStyle.FULL, Locale.getDefault()).uppercase(),
                        color = Muted, fontSize = 13.sp, letterSpacing = 2.sp)
                }
                items(me, key = { it.date.toString() }) { e -> EntryCard(e, store, onOpen) }
            }
        }
        item(key = "support") { SupportCard() }
    }
}

/**
 * The tip jar, as one quiet card: what SideCut does with Stripe Payment Links, minus the tab. It
 * sits under the last entry so it is found after the journal has been read, and it opens a page
 * Stripe hosts rather than asking the app for anything.
 */
@Composable
fun SupportCard() {
    val ctx = LocalContext.current
    var ask by remember { mutableStateOf(false) }
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(CardC)
            .clickable { ask = true }.padding(horizontal = 18.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text("Support UJournal", fontFamily = FontFamily.Serif, fontSize = 16.sp, color = Ink)
            Text("A tip is paid through Stripe, on a card page of its own.",
                color = Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 3.dp))
        }
        Text("♥", color = Tan, fontSize = 20.sp)
    }
    if (ask) {
        AlertDialog(
            onDismissRequest = { ask = false },
            containerColor = CardC,
            title = { Text("Support UJournal", fontFamily = FontFamily.Serif) },
            text = {
                Column {
                    Text(
                        "UJournal is free and has no ads. Stripe takes the payment on its own page; " +
                            "nothing unlocks, because this is a thank you.",
                        color = Muted, fontSize = 13.sp, lineHeight = 19.sp
                    )
                    Spacer(Modifier.height(8.dp))
                    Support.LINKS.forEach { (dollars, url) ->
                        TextButton(
                            onClick = { ask = false; Support.open(ctx, url) },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(Support.label(dollars), color = Ink, fontSize = 15.sp) }
                    }
                }
            },
            confirmButton = { TextButton({ ask = false }) { Text("Later", color = Muted) } }
        )
    }
}

@Composable
fun EntryCard(e: Entry, store: Store, onOpen: (LocalDate) -> Unit) {
    val thumb = e.atts.firstOrNull { it.mime.startsWith("image") || it.mime.startsWith("video") }
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(CardC)
            .clickable { onOpen(e.date) }.padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.width(48.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text("${e.date.dayOfMonth}", fontSize = 26.sp, fontFamily = FontFamily.Serif, color = Ink)
            Text(e.date.dayOfWeek.getDisplayName(JTextStyle.SHORT, Locale.getDefault()).uppercase(),
                fontSize = 11.sp, color = Muted)
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(e.title.ifBlank { "Untitled" }, fontFamily = FontFamily.Serif, fontSize = 17.sp,
                color = Ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (e.body.isNotBlank())
                Text(e.body, color = Muted, fontSize = 14.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (e.atts.isNotEmpty()) Text("📎 ${e.atts.size}", color = Tan, fontSize = 12.sp)
        }
        if (thumb != null) {
            Spacer(Modifier.width(8.dp))
            AsyncImage(store.file(e.date, thumb), null,
                Modifier.size(64.dp).clip(RoundedCornerShape(12.dp)), contentScale = ContentScale.Crop)
        }
    }
}

@Composable
fun CalendarView(days: Set<LocalDate>, onOpen: (LocalDate) -> Unit) {
    var ym by remember { mutableStateOf(YearMonth.now()) }
    val today = LocalDate.now()
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton({ ym = ym.minusYears(1) }) { Text("«", color = Ink) }
            TextButton({ ym = ym.minusMonths(1) }) { Text("‹", color = Ink) }
            Text("${ym.month.getDisplayName(JTextStyle.FULL, Locale.getDefault())} ${ym.year}",
                Modifier.weight(1f), textAlign = TextAlign.Center, fontFamily = FontFamily.Serif,
                fontSize = 22.sp, color = Ink)
            TextButton({ ym = ym.plusMonths(1) }) { Text("›", color = Ink) }
            TextButton({ ym = ym.plusYears(1) }) { Text("»", color = Ink) }
        }
        Row {
            listOf("S", "M", "T", "W", "T", "F", "S").forEach {
                Text(it, Modifier.weight(1f), textAlign = TextAlign.Center, color = Muted, fontSize = 12.sp)
            }
        }
        val off = ym.atDay(1).dayOfWeek.value % 7
        val len = ym.lengthOfMonth()
        repeat((off + len + 6) / 7) { r ->
            Row {
                repeat(7) { c ->
                    val n = r * 7 + c - off + 1
                    Box(Modifier.weight(1f).aspectRatio(1f).padding(3.dp), Alignment.Center) {
                        if (n in 1..len) {
                            val d = ym.atDay(n)
                            val has = d in days
                            Box(
                                Modifier.fillMaxSize().clip(CircleShape)
                                    .background(if (has) Tan else if (d == today) Sand else Color.Transparent)
                                    .clickable { onOpen(d) },
                                Alignment.Center
                            ) { Text("$n", color = if (has) Color.White else Ink) }
                        }
                    }
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        TextButton({ ym = YearMonth.now() }) { Text("Today", color = Muted) }
    }
}

@Composable
fun tfColors() = TextFieldDefaults.colors(
    focusedContainerColor = Color.Transparent, unfocusedContainerColor = Color.Transparent,
    focusedIndicatorColor = Color.Transparent, unfocusedIndicatorColor = Color.Transparent,
    cursorColor = Tan, focusedPlaceholderColor = Muted, unfocusedPlaceholderColor = Muted
)

@Composable
fun DayScreen(store: Store, date: LocalDate, onBack: () -> Unit) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var e by remember { mutableStateOf(store.load(date)) }
    val latest by rememberUpdatedState(e)
    var del by remember { mutableStateOf<Att?>(null) }

    DisposableEffect(Unit) { onDispose { store.save(latest) } }
    LaunchedEffect(e) { delay(500); store.save(e) }
    fun back() { store.save(e); onBack() }
    BackHandler { back() }

    val onPicked: (List<Uri>) -> Unit = { uris ->
        if (uris.isNotEmpty()) scope.launch {
            val n = withContext(Dispatchers.IO) { store.attach(e, uris) }
            e = n; store.save(n)
        }
    }
    val mediaPicker = rememberLauncherForActivityResult(ActivityResultContracts.PickMultipleVisualMedia(), onPicked)
    val audioPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetMultipleContents(), onPicked)
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetMultipleContents(), onPicked)
    var menu by remember { mutableStateOf(false) }
    var recording by remember { mutableStateOf(false) }
    var pending by remember { mutableStateOf<Uri?>(null) }
    fun captureUri(name: String): Uri {
        val f = File(File(ctx.cacheDir, "capture").apply { mkdirs() }, name)
        return FileProvider.getUriForFile(ctx, "${ctx.packageName}.files", f).also { pending = it }
    }
    val photoCam = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        if (ok) pending?.let { onPicked(listOf(it)) }
    }
    val videoCam = rememberLauncherForActivityResult(ActivityResultContracts.CaptureVideo()) { ok ->
        if (ok) pending?.let { onPicked(listOf(it)) }
    }

    Column(Modifier.fillMaxSize().background(Bg).verticalScroll(rememberScrollState())
        .padding(horizontal = 20.dp, vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton({ back() }) { Text("‹ Back", color = Muted) }
            Spacer(Modifier.weight(1f))
            Box {
                TextButton({ menu = true }) { Text("＋ Attach", color = Ink) }
                DropdownMenu(menu, { menu = false }, containerColor = CardC) {
                    DropdownMenuItem({ Text("🖼  Photos & videos") },
                        { menu = false; mediaPicker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageAndVideo)) })
                    DropdownMenuItem({ Text("🎵  Audio") }, { menu = false; audioPicker.launch("audio/*") })
                    DropdownMenuItem({ Text("📄  Any file") }, { menu = false; filePicker.launch("*/*") })
                    HorizontalDivider(color = Sand)
                    DropdownMenuItem({ Text("📷  Take photo") },
                        { menu = false; photoCam.launch(captureUri("Photo_${System.currentTimeMillis()}.jpg")) })
                    DropdownMenuItem({ Text("🎥  Record video") },
                        { menu = false; videoCam.launch(captureUri("Video_${System.currentTimeMillis()}.mp4")) })
                    DropdownMenuItem({ Text("🎙  Record audio") }, { menu = false; recording = true })
                }
            }
        }
        Text(date.format(DateTimeFormatter.ofPattern("EEEE, MMMM d, yyyy", Locale.getDefault())),
            color = Muted, fontSize = 14.sp, modifier = Modifier.padding(horizontal = 16.dp))
        TextField(e.title, { e = e.copy(title = it) }, Modifier.fillMaxWidth(),
            placeholder = { Text("Title", fontFamily = FontFamily.Serif, fontSize = 28.sp) },
            textStyle = TextStyle(fontFamily = FontFamily.Serif, fontSize = 28.sp, color = Ink), colors = tfColors())
        TextField(e.body, { e = e.copy(body = it) }, Modifier.fillMaxWidth().heightIn(min = 200.dp),
            placeholder = { Text("What's on your mind?") },
            textStyle = TextStyle(fontSize = 17.sp, lineHeight = 26.sp, color = Ink), colors = tfColors())
        Spacer(Modifier.height(12.dp))
        e.atts.chunked(3).forEach { row ->
            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { a ->
                    AttTile(store, e.date, a, Modifier.weight(1f).aspectRatio(1f),
                        { openAtt(ctx, store, e.date, a) }, { del = a })
                }
                repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
        Spacer(Modifier.height(80.dp))
    }

    if (recording) RecorderDialog { uri -> recording = false; if (uri != null) onPicked(listOf(uri)) }

    del?.let { a ->
        AlertDialog(
            onDismissRequest = { del = null }, containerColor = CardC,
            title = { Text("Remove attachment?", fontFamily = FontFamily.Serif) },
            text = { Text(a.name) },
            confirmButton = {
                TextButton({ e = store.remove(e, a); store.save(e); del = null }) { Text("Remove", color = Ink) }
            },
            dismissButton = { TextButton({ del = null }) { Text("Cancel", color = Muted) } }
        )
    }
}

@Composable
fun AttTile(store: Store, d: LocalDate, a: Att, mod: Modifier, onOpen: () -> Unit, onDelete: () -> Unit) {
    Box(mod.clip(RoundedCornerShape(14.dp)).background(Sand).clickable { onOpen() }) {
        val visual = a.mime.startsWith("image") || a.mime.startsWith("video")
        if (visual) {
            AsyncImage(store.file(d, a), null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        } else {
            Column(Modifier.fillMaxSize().padding(8.dp), Arrangement.Center, Alignment.CenterHorizontally) {
                Text(if (a.mime.startsWith("audio")) "🎵" else "📄", fontSize = 28.sp)
                Text(a.name, fontSize = 11.sp, color = Ink, maxLines = 2,
                    overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center)
            }
        }
        if (a.mime.startsWith("video"))
            Text("▶", color = Color.White, fontSize = 24.sp, modifier = Modifier.align(Alignment.Center))
        Text("✕", color = Color.White, fontSize = 12.sp,
            modifier = Modifier.align(Alignment.TopEnd).padding(4.dp).clip(CircleShape)
                .background(Color(0x66000000)).clickable { onDelete() }.padding(horizontal = 6.dp, vertical = 2.dp))
    }
}

fun openAtt(ctx: Context, store: Store, d: LocalDate, a: Att) {
    val uri = FileProvider.getUriForFile(ctx, "${ctx.packageName}.files", store.file(d, a))
    val i = Intent(Intent.ACTION_VIEW).setDataAndType(uri, a.mime).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    try { ctx.startActivity(i) } catch (_: Exception) {
        Toast.makeText(ctx, "No app can open this file", Toast.LENGTH_SHORT).show()
    }
}

@Composable
fun RecorderDialog(onDone: (Uri?) -> Unit) {
    val ctx = LocalContext.current
    var rec by remember { mutableStateOf<MediaRecorder?>(null) }
    var file by remember { mutableStateOf<File?>(null) }
    var secs by remember { mutableIntStateOf(0) }
    val liveRec by rememberUpdatedState(rec)

    fun start() {
        val f = File(File(ctx.cacheDir, "capture").apply { mkdirs() }, "Audio_${System.currentTimeMillis()}.m4a")
        val r = if (Build.VERSION.SDK_INT >= 31) MediaRecorder(ctx) else @Suppress("DEPRECATION") MediaRecorder()
        try {
            r.setAudioSource(MediaRecorder.AudioSource.MIC)
            r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            r.setOutputFile(f.absolutePath)
            r.prepare(); r.start()
            file = f; rec = r
        } catch (e: Exception) {
            r.release()
            Toast.makeText(ctx, "Couldn't start recording", Toast.LENGTH_SHORT).show()
        }
    }

    fun stop(save: Boolean) {
        rec?.let { runCatching { it.stop() }; it.release() }
        rec = null
        val uri = if (save) file?.let { FileProvider.getUriForFile(ctx, "${ctx.packageName}.files", it) } else null
        onDone(uri)
    }

    val perm = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) start() else Toast.makeText(ctx, "Microphone permission needed", Toast.LENGTH_SHORT).show()
    }
    LaunchedEffect(rec) { secs = 0; while (rec != null) { delay(1000); secs++ } }
    DisposableEffect(Unit) { onDispose { liveRec?.let { runCatching { it.stop() }; it.release() } } }

    AlertDialog(
        onDismissRequest = { if (rec == null) onDone(null) },
        containerColor = CardC,
        title = { Text("Record audio", fontFamily = FontFamily.Serif) },
        text = { Text(if (rec != null) "●  %d:%02d".format(secs / 60, secs % 60) else "Tap Record to start") },
        confirmButton = {
            TextButton({
                if (rec != null) stop(true)
                else if (ContextCompat.checkSelfPermission(ctx, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) start()
                else perm.launch(Manifest.permission.RECORD_AUDIO)
            }) { Text(if (rec != null) "Stop & save" else "Record", color = Ink) }
        },
        dismissButton = { TextButton({ stop(false) }) { Text("Cancel", color = Muted) } }
    )
}
