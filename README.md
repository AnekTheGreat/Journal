# UJournal

A quiet, paper-toned journal for Android. One entry per day, kept as plain files in the
app's own storage: `journal/YYYY-MM-DD/entry.json` plus any attachments beside it.

- **Timeline** — entries grouped by year and month, with a thumbnail of the first photo or video.
- **Calendar** — month grid, days that have an entry are filled in.
- **Attachments** — photos and video via the system picker, audio, any file, plus camera, video
  capture and a microphone recorder.
- **OTA updates** — a release can change the screen, and the installed journal takes it without an
  installer. A release that changes the shell still offers its APK; a copy installed from Google
  Play takes its build from Play and never asks GitHub for one.

## The screen is a page

The screen is `app/src/main/assets/index.html`: the timeline, the calendar, the day editor, the
attachment tiles, the tip jar and the update sheet. That is how SideCut, MeasureT, My Hub and FamTM
are built, and it is what makes an update cost nothing — replacing one file is not installing an
app.

The APK is the shell around it. It holds the part a page cannot do on Android — reading and writing
the entries, the pickers and both cameras, the recorder, opening an attachment, the tip links, and
the update — and reaches it all through one bridge that exposes nothing else.

A page that arrives over the air is checked before it is used: it must carry the `ujournal-page`
marker and name the version the release promised, it must report that it drew within nine seconds
or the stored copy is deleted, and a newly installed APK always deletes a page stored before it.
The worst an update can do is put back the screen the APK shipped with.

## Layout

```
app/src/main/assets/index.html       the screen: timeline, calendar, day editor, sheets
dev/                                 (none yet - the page is checked by node --check in CI)
app/src/main/java/app/ujournal/
  MainActivity.kt   the shell: one WebView, the bars, the pickers, the recorder, the update
  Bridge.kt         what the page may ask the phone: entries, pickers, recorder, tips, updates
  PageStore.kt      the bundled page, the over-the-air copy, and the rules that make it safe
  Store.kt          reading and writing entries and attachments, as plain files
  Updater.kt        the release check, the page download, and the fallbacks behind it
  Support.kt        the tip jar: five Stripe Payment Links
app/src/main/res/   manifest resources (theme, strings, icon, file paths)
```

## Build

Needs JDK 17 and the Android SDK with platform 36 (build-tools 36.0.0).

```sh
gradle :app:assembleDebug        # app/build/outputs/apk/debug/app-debug.apk
gradle :app:assembleRelease      # signed only when the signing environment is present
```

The version comes from `versionName` in `app/build.gradle.kts` — `1.6.3` today — and `versionCode`
is computed from it (`10603`), so it only ever climbs. The page names the same version in
`JOURNAL_PAGE`, and both jobs refuse a build where they disagree.

## Updates

Two things can change, and only one of them is an install:

- **The screen.** The release publishes `page_url` in `updates.json`, pinned to its own tag. A copy
  that finds it newer than the page it is drawing fetches it, checks the marker and the version,
  writes it into the app's own storage and loads it — as soon as it is found, without a tap. Nothing
  is downloaded that Android installs, so Play Protect sees nothing, and a Play copy gets this
  exactly like a sideloaded one.
- **The shell.** A release that changed the bridge is offered as an APK, through the release page
  in the browser — a copy from Play is offered the Play listing instead, because Play is what
  installs that copy.

A silent check runs on launch and again whenever the journal comes back to the front, at most once
every ten minutes, and only speaks when something newer exists, so being current, being offline and
a failed request all open the journal exactly as before. The ⟳ in the header asks on demand.

## Actions

- **Build APK + AAB** (`.github/workflows/build.yml`) — runs on every push to `main`, on pull
  requests and on demand. Assembles the debug and the signed release APK plus both bundles, checks
  the page is inside the APK and names the build's version, and uploads everything as one artifact.
- **Release APK + AAB** (`.github/workflows/release.yml`) — runs on a `v*` tag, or on demand with a
  version input. Checks the tag, `versionName` and the page agree, writes `updates.json` with the
  page beside it, and publishes the signed APK, the AAB and the manifest.

```sh
git tag v1.6.3 && git push origin v1.6.3
```

## Signing

There is no keystore and no password in this repository. The release key is held in the
repository's Actions secrets, and both workflows rebuild it on the runner for the length of the
job, so a checkout carries no key material and a plain `assembleDebug` works without one.

Android only installs an update signed with the same key, so that key is the app's identity rather
than a build detail: losing it means every installed copy has to be uninstalled and replaced.

## Licence

UJournal is proprietary. Copyright (c) 2026 AnekTheGreat, all rights reserved — no part of it may
be copied, reused, modified or redistributed without written permission. See [LICENSE](LICENSE).
