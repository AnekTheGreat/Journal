# UJournal

A quiet, paper-toned journal for Android. One entry per day, kept as plain files in the
app's own storage: `journal/YYYY-MM-DD/entry.json` plus any attachments beside it.

- **Timeline** — entries grouped by year and month, with a thumbnail of the first photo or video.
- **Calendar** — month grid, days that have an entry are filled in.
- **Attachments** — photos and video via the photo picker, audio, any file, plus camera, video
  capture and a microphone recorder.
- **OTA updates** — a sideloaded copy checks the latest GitHub Release on this repo and opens the
  release page when one is newer; a copy installed from Google Play takes its updates from Play and
  never asks GitHub at all.

## Layout

```
app/src/main/java/app/ujournal/
  MainActivity.kt   screens: timeline, calendar, day editor, recorder, update dialog
  Store.kt          reading and writing entries and attachments
  Updater.kt        GitHub Release check, and the page (or Play listing) it opens
  Theme.kt          colours and the Material3 theme
app/src/main/res/   manifest resources (theme, strings, icon, file paths)
```

## Build

Needs JDK 17 and the Android SDK with platform 36 — Google Play has required API 36 for an upload
since 31 August 2026, so `compileSdk`/`targetSdk` are 36 and the build uses Android Gradle Plugin
8.10.1 with Gradle 8.11.1.

```sh
gradle :app:assembleDebug        # app/build/outputs/apk/debug/app-debug.apk
gradle :app:assembleRelease      # signed only when the signing variables below are set
```

The version is in `app/build.gradle.kts` — `versionName = "1.2.5"`, with `versionCode` computed from
it (10205) — so CI and a local build always carry the same numbers, and every release installs over
the one before it.

## Actions

- **Build APK** (`.github/workflows/build.yml`) — runs on every push to `main`, on pull requests
  and on demand. Assembles the debug and the signed release APK and uploads both as one artifact.
- **Release APK** (`.github/workflows/release.yml`) — runs on a `v*` tag, or on demand with a
  version input. Builds the signed APK and publishes it as a GitHub Release, which is what the
  in-app updater reads. It stops before publishing unless the bundle targets API 36 and asks for no
  `REQUEST_INSTALL_PACKAGES`, because Play would reject it otherwise.

```sh
git tag v1.0.1 && git push origin v1.0.1
```

For Play Console — what to upload, the listing copy, the graphics and the declarations — see
[PLAY_STORE.md](PLAY_STORE.md).

## Signing

There is no keystore and no password in this repository. The release key is base64-encoded in the
repository's Actions secrets, and both workflows rebuild it in `$RUNNER_TEMP` for the length of the
job:

| Secret | What it holds |
| --- | --- |
| `KEYSTORE_BASE64` | the keystore, base64-encoded: `base64 -w0 ujournal.jks` |
| `KEYSTORE_PASSWORD` | the keystore password |
| `KEY_PASSWORD` | the key password (alias is `ujournal`) |

Without them nothing breaks locally: `assembleDebug` works and `assembleRelease` produces an
unsigned APK that Android will refuse to install. To sign a release by hand:

```sh
export SIGNING_STORE_FILE=/absolute/path/ujournal.jks
export SIGNING_STORE_PASSWORD=...
export SIGNING_KEY_PASSWORD=...
export SIGNING_KEY_ALIAS=ujournal
gradle :app:assembleRelease
```

Keep that keystore somewhere safe: Android only installs an update signed with the same key, so
losing it means every installed copy has to be uninstalled and replaced. Installing from Google Play
is the one exception, and it works the other way round: Play signs what it delivers with its own key,
so a sideloaded copy has to be uninstalled before the store build can be installed.
