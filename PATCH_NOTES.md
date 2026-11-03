# Patch notes

What changed, newest first. Every release ships as a signed APK for a phone and the same build as
an AAB for Play Console, made by
[release.yml](.github/workflows/release.yml) on a `v*` tag. The app's own updater reads those
releases, so a release is also the update every installed copy is offered.

## 2026-11-03 — updates that install

### Fixed
- **A release could not be installed over a build.** `versionCode` came from the workflow's run
  number, so a build from a later run carried a higher code than the release cut before it, and
  Android rejects a lower code as a downgrade: the download finished, the installer opened, and
  nothing changed. The code is now computed from the version in `build.gradle.kts` — 1.2.0 is
  10200 — so every release installs over what came before it.
- **A check could fail without saying anything.** The request to `api.github.com` carried no
  `User-Agent`, which GitHub answers with 403, and the anonymous allowance is per address — a phone
  on a carrier shares one with everything behind that gateway. Requests now identify the app, and
  when the API refuses, the newest tag is read from the repository's releases feed instead, with the
  APK URL built from it.
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
