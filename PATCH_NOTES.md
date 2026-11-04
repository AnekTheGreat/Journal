# Patch notes

What changed, newest first. Every release ships as a signed APK for a phone and the same build as
an AAB for Play Console, made by
[release.yml](.github/workflows/release.yml) on a `v*` tag. The app's own updater reads those
releases, so a release is also the update every installed copy is offered.

## 1.5.0 — it opens on your journals, and the timeline shows them again

### Added
- **A shelf to open on.** UJournal used to open straight into the timeline of one book. It opens on
  your journals now: a **Start a new journal** card at the top, then the three you were last in —
  each with how many entries it holds and the day it was last written in — and **All N journals**
  when there are more than three. A book opens on its own name in the top bar, with ‹ beside it to
  come back to the shelf.
- **More than one journal.** A journal is a book: its own name, its own timeline, its own calendar,
  its own entries and attachments. They live as `journals/<id>/` with a small `journal.json` for the
  name, so nothing is locked in a database and a folder copy is still a copy of everything.
- **Your existing journal becomes the first book.** The folder 1.3 wrote — `filesDir/journal` — is
  moved into that shape once, on the first launch after this update, named *My Journal*. No entry
  moves to a different day and nothing is left behind.

### Fixed
- **The timeline drew NaN over its cards.** `Bridge.entries()` was putting the JSON *text* of each
  entry into the array instead of the object, so the page received an array of strings: `date` was
  undefined, the year and month headings read **NaN** and **UNDEFINED**, and every entry became an
  *Untitled* card with no body. It hands over the objects now, which is what those cards were
  always meant to be given.
- **The shelf keeps the journal's own controls to itself.** The ＋ button and the Journal / Calendar
  tabs belong to a book, not to the list of them, so they are not on the shelf.

### Changed
- **A backup carries the whole shelf.** The one file from 1.4 now holds every journal: each book's
  `journal.json`, then every day and every attachment in it. Restoring it puts the whole shelf back
  on the new phone.

## 1.4.0 — the journal travels in one file

### Added
- **Every entry and attachment in one file, for a new phone.** A new ⋯ button in the top bar opens
  **Move to a new device**: *Save a backup* writes one `.zip` holding every day's `entry.json` and
  everything attached to it, and *Restore a backup* reads one back on the other phone. The file is
  written through the phone's own Save dialog, so it goes wherever you point it — Downloads, a
  memory card, a cloud folder that syncs — and nothing is uploaded anywhere.
- **The file says what it is.** `ujournal-backup.json` sits at the top of the archive with the app's
  name, the version that wrote it, the date, and how many days and files it holds, so a zip that is
  not a UJournal backup is refused instead of half-restored.

### Changed
- **Restore replaces, and says so.** The sheet warns that restoring replaces every entry in this
  journal, and the button arms on the first tap (*Replace this journal?*) before it opens the
  picker. When the restore finishes the page reloads from disk, so the timeline shows what arrived
  and the calendar fills in the days that came with it.
- **A restore is all-or-nothing.** The archive is unpacked into a folder of its own and only swapped
  in once every file is out and named for a real date; an archive that fails partway leaves the
  journal exactly as it was. A name that would land outside the journal's folder — a path of its
  own, or `..` — is refused, and the whole read is capped, so a wrong file cannot fill the phone.

### Fixed
- **Closing the journal no longer relies on the page being quick.** `onPause` asks the page to flush
  what was typed, and the page now answers: `window.journalFlush` is the same save the half-second
  timer and the blur already call, so a note typed in the last moment before the screen goes away
  is on disk either way.

## 1.3.0 — the journal is a page now, so it updates without an installer

### Changed
- **UJournal draws a page instead of building its screen in Compose.** The timeline, the calendar,
  the day editor, the attachment tiles, the tip jar and the update sheet are `assets/index.html`,
  the same shape SideCut, MeasureT, My Hub and FamTM have. What stays native is the part a page
  cannot do on Android: reading and writing the entries, the pickers and both cameras, the
  microphone recorder, opening an attachment, the tip links, and the update itself. The page
  reaches them through one bridge, which exposes nothing else.
- **A screen update now arrives over the air.** On launch the journal reads `updates.json` from the
  newest release; when it names a newer page, that page is fetched, checked, written into the app's
  own storage and loaded in place. No APK, no browser, no installer prompt — and **Update now** is
  one tap, which is what an update should have felt like all along.
- **The APK is the shell, and only changes when the shell does.** A release that only touched the
  screen costs nothing to install, because there is nothing to install; a release that changed the
  bridge still offers the APK, and only to a copy that was not installed by Play.
- **A copy installed from Google Play keeps the screen updates.** 1.2.5 made a Play copy skip the
  check entirely; it now skips only the APK, so Play handles the build while the screen keeps
  arriving on its own.
- **Nothing about your entries moved.** They are the same `journal/YYYY-MM-DD/entry.json` files with
  their attachments beside them, read and written by the same code — the page only asks it
  questions. A backup is still a folder copy, and uninstalling still deletes it.
- **The build lost four libraries.** Compose, activity-compose, the Material3 and foundation
  artifacts, and Coil are all gone: what is left is the Android framework plus core-ktx, for the
  FileProvider that hands an attachment to the app that opens it.

### Fixed
- **A bad page cannot leave you with a blank journal.** A download without the `ujournal-page`
  marker or without the version the release promised is refused; a page that loads but never
  reports that it drew is deleted and the bundled copy is loaded; a newly installed APK deletes any
  page stored before it; and the file is replaced by a rename, so a half-written download is never
  served. The worst an update can do is put back the screen the APK shipped with.
- **The editor, the timeline and the calendar still sit clear of the status bar and the keyboard.**
  Targeting API 36 means edge-to-edge with no opt-out, so the WebView itself is padded by the
  system bars and the IME rather than being drawn under them.
- **Text you type is saved by the page itself**, half a second after you stop typing and when you
  leave the day, so closing the journal no longer depends on an editor being disposed.

### Added
- **The release manifest carries the screen.** `updates.json` now has `page`, `page_size`,
  `page_sha256` and a `page_url` pinned to the release tag, so an update is always the page that
  release shipped rather than whatever the branch says later.
- **`release.yml` checks the page before publishing**: the tag, `versionName` and `JOURNAL_PAGE` all
  have to agree, the marker has to be present, and the bundle has to contain the page.

## 1.2.5 — target Android 16, and a Play copy updates through Play

### Changed
- **The journal now targets Android 16 (API 36).** Google Play has refused an upload that targets
  less since 31 August 2026, so `compileSdk` and `targetSdk` are both 36. That needs a newer Android
  Gradle Plugin — 8.10.1, with Gradle 8.11.1, both pinned in CI.
- **A copy installed from Google Play updates through Play.** `Updater.fromPlay()` asks the phone
  which app installed this copy; when the answer is the Play Store, the journal does not ask GitHub
  at all and never offers an APK — Play is what installs that copy's updates. A sideloaded copy
  keeps the GitHub check exactly as it was.

### Added
- **A Play-ready step in `release.yml`.** A release now stops before publishing unless `targetSdk`
  is 36, `compileSdk` is 36, and the manifest asks for no `REQUEST_INSTALL_PACKAGES`.
- **`PLAY_STORE.md`** — what to upload, the listing copy, the graphics still to supply by hand, and
  the store declarations the journal needs for the microphone.

### Fixed
- **The day editor no longer runs under the status bar or the keyboard on Android 15 and 16.**
  Target 36 means edge-to-edge is enforced; the editor pads itself for the system bars and the
  keyboard, and the timeline and calendar already sit inside a `Scaffold` that does the same.

## 1.2.4 — the update no longer installs itself, so Play Protect stops calling it harmful

### Fixed
- **Play Protect read UJournal as harmful, because the journal was behaving the way a dropper
  does.** It downloaded the release APK into its own cache and handed it to Android's installer,
  which is what `REQUEST_INSTALL_PACKAGES` is for. A sideloaded app that fetches code over the
  network and then asks to install it is precisely the shape Play Protect blocks, and a journal
  that also asks for the microphone looked worse. The permission, the download and the hand-off are
  all gone: tapping Update opens the release page in the browser, the APK downloads there, and the
  phone's own installer installs it from outside the app.
- The dialog no longer promises an install the app does not perform — it says where the file goes.

### Changed
- The check itself is unchanged. It still reads the manifest published with the release, compares
  the version with the build on the phone and shows the notes before anything downloads.

## 1.2.3 — an update that says what changed

### Fixed
- 1.2.2 shipped a manifest with no notes in it at all: the extractor treated the `### Fixed`
  subheading as the end of the entry, so it never reached a bullet. Subheadings are skipped now and
  a wrapped line joins the bullet it belongs to, so the manifest carries whole sentences — six of
  them for this release.
- A release **fails** if it finds no note for its version, instead of publishing an update that
  announces nothing.

## 1.2.2 — the notes that arrive with the update are whole sentences

### Fixed
- A note here wraps over several lines, and the manifest kept only the first of them, so the update
  would have announced itself with half a sentence. The continuation lines are joined back onto the
  bullet they belong to, and the markdown emphasis is dropped.

## 1.2.1 — the update is published the way the other apps publish it

### Changed
- **A manifest travels with the release.** `updates.json` — version, file name, size, notes — is
  written by the release job and attached beside the APK and AAB, exactly as SideCut publishes
  `ota/updates.json`, MeasureT publishes `updates.json` and FamTM publishes its page. The app reads
  that one fixed address (`releases/latest/download/updates.json`) and takes both the version to
  compare and the notes to show from it, so the changelog comes with the build instead of being
  reconstructed from an API response. The API and the releases feed remain as fallbacks for a
  release that predates the manifest.

### Fixed
- `versionName` is read by the release job for its tag check, so the manifest can no longer
  advertise a version the APK does not carry.

## 2026-11-03 — updates that install

### Fixed
- **A release could not be installed over a build.** `versionCode` came from the workflow's run
  number, so a build from a later run carried a higher code than the release cut before it, and
  Android rejects a lower code as a downgrade: the download finished, the installer opened, and
  nothing changed. The code is now computed from the version in `build.gradle.kts` — 1.2.4 is
  10204 — so every release installs over what came before it.
- **A check could fail without saying anything.** The request to `api.github.com` carried no
  `User-Agent`, which GitHub answers with 403, and the anonymous allowance is per address — a phone
  on a carrier shares one with everything behind that gateway. Requests now identify the app.
- A download is checked to be a zip, of a plausible size, before the installer is handed it; an
  error page saved as `.apk` used to surface as "there was a problem parsing the package". The
  connection has timeouts now instead of hanging, and a failed check leaves a line in logcat.
- The debug APK is no longer as eligible as the release one: it is only a fallback, so a debug
  asset can never install over a release build.

### Changed
- `build.yml` and `release.yml` take the version from `build.gradle.kts` rather than from the run
  number, and a release fails if its tag disagrees with the version the APK carries.
- Build artifacts are named `UJournal-<version>.apk` and `.aab`, flat in one folder, beside the same
  two debug files instead of inside Gradle's `apk/debug` and `bundle/release` tree.

## 2026-11-03 — a way to say thank you, and an AAB beside the APK

### Added
- **Support UJournal.** A quiet card under the last entry (and under the empty state of a new
  journal) opens five amounts — $2, $5, $10, $25, $50 — paid through the same Stripe Payment Links
  SideCut's Donate tab uses. Stripe takes the payment on its own page; nothing unlocks, because the
  journal is the same either way. There is no key in the app: a Payment Link is a public URL.
- Every build now publishes an **`.aab`** as well as the APK — debug and release both — and a
  release attaches both, so Play Console gets exactly the build a phone installs by hand.

### Changed
- `build.yml` and `release.yml` now fail if `bundleRelease` produced no `app-release.aab`, not only
  if the APK came out unsigned. AGP writes an unsigned artifact without complaining, and Play only
  says so later.

## 2026-10-30 — one entry per day, kept as plain files

### Added
- **Attachments**: photos and video from the photo picker, audio from the microphone, any file, and
  the camera for a photo or a clip — each stored beside the entry that owns it.
- **Calendar**: a month grid where a day with an entry is filled in.
- **OTA updates**: the app checks the newest GitHub Release on this repository, offers what changed,
  downloads the APK and hands it to the installer.

### Changed
- The timeline groups entries by year and month, and a card shows the first photo or video as a
  thumbnail instead of a row of file names.

## 2026-10-29 — the first UJournal

### Added
- One entry per day, written in a paper-toned editor: a title, a body, and the date it belongs to.
- Entries live in the app's own storage as `journal/YYYY-MM-DD/entry.json`, so a backup is a folder
  copy and nothing is locked in a database.
