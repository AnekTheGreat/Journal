# Patch notes

What changed, newest first. Every release ships as a signed APK for a phone and the same build as
an AAB for Play Console, made by
[release.yml](.github/workflows/release.yml) on a `v*` tag. The app's own updater reads those
releases, so a release is also the update every installed copy is offered.



## 1.9.11 — November 7, 2026

**The update that kept coming back.**

- A screen that does not arrive in one piece is no longer fetched again on every launch and every
  return. It is tried once, and again only on a check you asked for, or after six hours.
- The welcome, the tour and What's New are kept by the app as well as by the screen, so a cleared
  cache cannot bring the same popup back on every launch.
- No version here ends in ten: 1.9.11 follows 1.9.9, and the build number the phone compares has
  room for any part, so an update always installs over the one before it.

## 1.9.10 — November 6, 2026

**My Hub is off the Other apps list.**

- Other apps, and the card in Support that leads to it, list the three apps beside this one
  that a tap can install: FamTM, SideCut and MeasureT. My Hub has no store page, so a tap on
  it went somewhere that could not install anything.
- The Guide's line for Other apps says the same three.
- This one is in the page: it arrives the next time the app opens, with nothing to install.

## 1.9.9 — November 6, 2026

**A welcome, a tour, and a Guide under the gear.**

- A first launch opens on a welcome: three lines on what the journal is for, and two buttons,
  Show me around and Skip. Shown once, marked seen when it appears rather than when it closes.
- The tour is five steps - writing a day, the three tabs, the gear, backups and updates - with
  Next, Back and Skip. It draws in the settings sheet, so it uses the same card as the rest of
  the app and closes without leaving the journal anywhere else.
- Settings gains a Guide tab: the same tour, the welcome, and every feature in one list.
- What's New waits behind the welcome, so a new phone is not met by two popups at once.

## 1.9.8 — November 6, 2026

**One gear, and the whole family in it**

### Changed

- Settings is one sheet, behind a gear in the top bar, cut into tabs: Journal, Transfer, Updates,
  Support and Other apps. The row of tabs scrolls sideways, and keeps the place you scrolled it to
  instead of snapping back to its first tab.
- Other apps is the whole family in one list: FamTM, My Hub, SideCut and MeasureT.
- The ... , heart and arrow in the top bar still work; the gear is the one place that holds
  everything.

Page only, so it arrives over the air.


## 1.9.7 — November 6, 2026

**The birthdays arrive together**

### Fixed
- **A family's birthdays arrived as one.** Importing from FamTM gave each birthday an id made from
  the clock, and the whole list is saved in one loop inside the same millisecond: every birthday
  after the first was given an id the one before it already had, so each save replaced the last.
  Eight birthdays in FamTM arrived as one, and the next open did exactly the same again. A new plan
  now takes an id no other plan has, so the list arrives whole.
- **They are drawn in the calendar.** Every imported birthday is a birthday plan on its month and
  day in every year, in rose beside the tan of a day with an entry.

### Unchanged
- Still on the phone only: FamTM's living family, a name and a day each, read through its read-only
  provider, with this journal's own birthdays published back the same way.


## 1.9.6 — November 6, 2026

**The other-apps card leaves the journal list and stays in Plans**

### Changed
- **No other-apps card under the entries.** The journal's own list drew the card for SideCut, FamTM
  and the rest after the last entry, so every list ended with a shelf of other apps. The list now
  ends with the journal itself.
- **Plans keeps it.** The same card is still at the bottom of Plans, where the plans and the
  birthdays are, so nothing became unreachable.

### Unchanged
- The birthdays still add themselves, the rose colour in the calendar and the provider back to FamTM
  are as they were in 1.9.5.


## 1.9.5 — November 6, 2026

**The birthdays card reports what FamTM actually holds**

### Fixed
- **Three different things all read as "nothing new".** No FamTM, FamTM that cannot be read, and a
  FamTM that was read and has nobody in it were indistinguishable on the card. The shell now answers
  with the FamTM version, the number of birthdays it offers and the number already kept, and the card
  draws that: an empty list is reported as an empty list rather than as a failed exchange.
- **The counts are visible.** The card reads N in FamTM and M here, so the difference between an
  exchange that works and one with nothing to carry is on the screen.
- **The tap says it in a sentence.** Up to date, nobody with a birthday in FamTM yet, or the versions
  of both apps when the list could not be read.

### Unchanged
- Birthdays still add themselves on open and when Plans is opened, nothing is uploaded, and the rose
  colour in the calendar, the provider back to FamTM and the plan sheet are as they were in 1.9.4.


## 1.9.4 — November 6, 2026

**Birthdays add themselves, and a birthday is rose rather than tan**

### Changed
- **The birthdays arrive without a tap.** The page reads FamTM when the journal opens and whenever
  Plans is opened, and adds every name and day that is not in the journal yet. It is the same call
  the card made, so an existing birthday is still never added twice, and the read is bounded to once
  every thirty seconds so a tab change cannot repeat it.
- **The card in Plans is a status line now.** It reads Following FamTM with the number of birthdays
  held, and keeps the three-way answer - not installed, installed but unreadable, or N new - when the
  list cannot be read.
- **A birthday has its own colour in the calendar.** Days with a journal entry keep the tan fill; a
  birthday is filled rose, and a day with both stays rose with the dot that means a plan. A key under
  the grid names the two colours.

### Unchanged
- Only living people are in FamTM's list, so only living people arrive. Nothing is uploaded, the
  provider here still publishes this journal's birthdays back to FamTM, and the plan sheet, the
  durations and the tip heart are as they were in 1.9.3.


## 1.9.3 — November 6, 2026

**The birthdays card now says which of the three things happened**

### Fixed
- **"FamTM is not installed" was said for two other problems as well.** The card had one failure
  message and three ways to reach it: no FamTM on the phone, FamTM on the phone whose list this app
  could not read, and a list it read that was empty. The app now looks the FamTM package up first,
  reads its version, and only then asks for the list - so the sentence on the card matches what
  actually happened.
- **The journal's own version is named when the read fails.** The screen arrives over the air while
  the asking lives in the app, so an older app with the newest screen behaves exactly like a broken
  one. The message now names both versions, which is the difference between "update the app" and
  "something is wrong with the list".
- **An empty list is no longer treated as a refusal.** A FamTM that answers with an empty list is a
  FamTM with nothing in it, and the card says that instead of blaming the install.

### Unchanged
- The provider here still publishes this journal's birthdays back to FamTM, names and days only, and
  the plan durations, the tip heart and the screen are as they were in 1.9.2.


## 1.9.2 — November 6, 2026

**The birthdays arrive: the journal now asks Android for FamTM's list**

### Fixed
- **Sync birthdays did nothing on a phone that has FamTM.** Android 11 and later hide one app from
  another unless the first names it, and UJournal never named FamTM: the query to
  content://com.FamTM.app.birthdays/list was refused and the card in Plans said FamTM was not
  installed. The app now declares FamTM - the package and the one provider it reads - so the same
  tap brings the birthdays across.
- **A screen written before this one still works.** The page only changes its own notes and its
  version; the import, the plans and the calendar are untouched by it.

### Unchanged
- The provider here still publishes this journal's birthdays back to FamTM, names and days only, and
  the plan durations and the tip heart are exactly as they were in 1.9.1.


## 1.9.1 — November 6, 2026

**Birthdays both ways, a plan that asks how long, and a quieter tip jar**

- **The birthdays sync both ways.** The exchange used to be one-sided: FamTM published a list and the journal could only read it. The app now publishes its own birthdays at `content://app.ujournal.birthdays/list`, in exactly the shape FamTM publishes, so FamTM reads what is typed here the same way this app reads what FamTM keeps. The card in Plans is now **Sync birthdays**, and one tap does both halves: FamTM's get added and the journal's get shared back.
- **Only names and days travel, on the phone.** No upload, no account, no second thing to type. FamTM's own side of the exchange is its app; the journal now holds up its end of the same contract.
- **A plan asks how long, not when it ends.** The second clock that asked for an end time is gone: a plan picks **30 min, 1 hour, 2 hours, 3 hours, 5 hours or All day** from tan chips and the end time is worked out from the start. A plan running past midnight stops at 23:59 rather than reading as one that ends before it began.
- **The tip jar is one heart.** The Support card is gone from the journal list; supporting the app is the ♥ at the top right, beside the menu, with the same five amounts behind it.
- **Tan and native throughout.** Fields are the app's own card colour with no browser chrome, the duration chips are tan when chosen, and the sheets line up with the rest of the app.

## 1.9.0 — November 5, 2026

**Birthdays from FamTM are one button, and a new screen says what changed**

- **One button, not a card.** The Plans tab used to end with a card *about* the birthdays FamTM was holding; it is now a single button under **New plan** — *Add N birthdays from FamTM* — and that button is the whole of the feature.
- **What's New, in the screen's own words.** The first time a new screen runs, a popup lists what changed in it, with the version marked read when the popup is closed — its own button, the backdrop, or the phone's back — and not when it is built. It appears once per screen version.
- **The notes travel inside the screen.** Nothing is fetched to read them: a screen that arrives over the air brings its own account of what changed.
- **Nothing else changed.** The button and the popup are both in the page, so this release is taken over the air: a copy on 1.8.1 installs nothing to get either.

## 1.8.1 — November 5, 2026

**MeasureT, called by its name**

- **The app list no longer says Compass EDC.** The fourth app there is **MeasureT** — elevation, location, the level, the converter and currency — and tapping it still opens the same listing, because the package keeps its original name.
- Nothing else changed: the birthdays from FamTM, the Plans tab without the Support card and the over-the-air updates are exactly as they were in 1.8.0.

## 1.8.0 — November 5, 2026

**Birthdays from FamTM, marked every year on the calendar**

- **The birthdays come across from FamTM.** When FamTM is installed and has birthdays, the Plans tab offers them: one tap brings over the name and the day for everyone alive, and from then on each one is marked on the calendar every year without being entered again.
- **They arrive as ordinary birthday plans**, so one can be renamed, moved or deleted like any other, and a birthday already in the journal is never added twice.
- **Only the name and the day travel.** FamTM hands over the same short list its own reminders keep — no photos, no notes — and the journal only ever reads it, so nothing in FamTM can be changed from here.
- **The Support card is gone from Plans.** That tab is about what is coming up: the new-plan button, the days ahead, and the birthdays. The tip jar is still on the journal screen.
- **Updates arrive on their own.** A new screen is now compared with the screen this copy is drawing rather than with the app's version number, so a release that only changes wording installs itself the next time the journal is opened — even when the app number has not moved at all.
- **An app update is offered once.** Tapping Later is no longer undone by the next launch; ⟳ asks again whenever it is pressed.

## 1.7.0 - one journal, opened straight away

### Removed
- **The shelf.** "Your journals", "Start a new journal", "All journals" and the back arrow that led
  to them are gone. UJournal is one journal now: the app opens on the timeline and the ＋ button is
  the first thing to press. Books already on a phone are folded into one on the first launch after
  this update - every day, every attachment and every calendar plan is kept, a day that appeared in
  two books is put aside rather than overwritten, and a backup made before this version still
  restores.
## 1.6.3 - updates take themselves, and they take a moment instead of a minute

### Changed
- **A new screen installs itself.** A page update used to be *offered*: the journal found it and
  then stood still behind a sheet until someone tapped **Update now**. It is taken as soon as it is
  found now - the screen is one file and installing nothing, so there was never anything to
  consent to. The one exception is a day being written in: an update arriving mid-sentence waits,
  and the next time the journal comes back it goes in.
- **It checks more than once.** The check ran once per launch, so a journal left open on a desk
  could sit on yesterday's screen for days. It now also runs when the journal comes back to the
  front, at most once every ten minutes, so a new release lands on the next glance rather than the
  next relaunch.
- **The check can no longer hang.** Every address it reads redirects - the newest-release manifest
  to a signed asset host, the asset to its own CDN - and the old 12-second connect and 25-second
  read timeouts meant one stalled redirect looked like an update that never arrives. They are four
  and eight seconds now: still generous for a 1 KB manifest and a 42 KB page, and a check that does
  run out simply says nothing and tries again later, instead of holding a connection open.
- **The app itself still asks.** A release that changed the shell cannot install itself without the
  permission that got UJournal flagged as a dropper, so that one still opens the release page - and
a copy Play delivered is still offered neither.

## 1.6.2 - the other apps open their Play listings

### Changed
- **"Check out the other apps" goes to the Play Store.** Each row used to open that app's GitHub
  releases page, which is where the APKs are kept for sideloading, not where anyone installs an
  app. Every row now opens the app's own Play listing, addressed by the package name it is
  published under - the one address that survives a renamed repository. The addresses still live
  in the app rather than the page, so an over-the-air screen can list the apps without choosing
  where a tap goes.
- **A listing that is not up yet says so, in Play's own words.** FamTM is published
  (`com.familytree.app`); the journal, My Hub, SideCut and Compass EDC answer with Play's "not
  found" page until they are published, which is a truer answer than a download link.

## 1.6.1 - your journal, and the tabs that are always there

### Fixed
- **The book is yours, not the app's.** The journal the app starts for you was called "My Journal",
  which read as though it belonged to UJournal instead of to the person writing in it. It is now
  called "Your Journal", and a book still carrying the old default is renamed once on the next
  launch - the entries, the attachments and the plans in it are untouched, and a name you chose
  yourself is never changed.
- **The tabs never disappear.** They used to vanish on the shelf, so the app opened on a screen with
  no Journal, Calendar or Plans under it. They stay now: Journal is the shelf itself, and picking
  Calendar or Plans there opens them in the journal you were last in.
- **The shelf can write.** The + that sits above the tabs is on the shelf too, opening today's entry
  in that same journal - starting a book is still the card at the top, but writing is never hidden
  behind it.

## 1.6.0 — plans: a time, a few days away, or every year

### Added
- **Plans live beside the entries.** A journal keeps what is coming as well as what happened: a
  dinner with a time on it, a trip that runs from one day into the next, and a birthday that comes
  round every year. A **Plans** tab sits beside Journal and Calendar, and the top of the timeline
  shows what is on today as soon as the book opens.
- **A plan is a day with things in it, not a slot.** *New plan* asks for a title and then **Event**
  or **Birthday**. An event takes a day, optional **From** and **To** times, a **Last day** when it
  runs over several days, and a note. A birthday takes the day it falls on and repeats every year:
  it is drawn with a cake and ordered by when it next comes round.
- **The day sheet plans too.** Open any day and the plans for it sit under the date, with
  **＋ Plan something for this day** right there, so a plan can be added without leaving the entry
  being written. Tapping a plan opens it to change or delete, and Delete asks once before it goes.
- **The calendar marks planned days.** A day with an entry is still filled in; a day with a plan now
  carries a dot — in the tan of the app on an empty day, in white inside a filled one.
- **Plans travel with the book.** They are kept in the journal's own `journal.json`, beside the name,
  so the backup and **Move to a new device** already carry every plan and a restore puts the calendar
  back on the new phone with nothing else to do. A plan whose date is unreadable is skipped instead
  of drawn as a broken row, so a hand-edited file cannot stop the book from opening.
- **Check out the other apps.** The bottom of the shelf lists FamTM, My Hub, SideCut and Compass EDC,
  one line each, and a tap opens that app's page. The addresses live in the app rather than in the
  page, for the same reason the tip links do: a screen that arrives over the air can list the other
  apps, but should not be able to choose where a tap goes.

### Changed
- **The ✚ button belongs to writing, not planning.** It is hidden on the Plans tab, which has its
  own **New plan** card, and stays hidden inside a day as before.

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
