# UJournal

A quiet, paper-toned journal for Android. One entry per day, kept as plain files in the
app's own storage: `journal/YYYY-MM-DD/entry.json` plus any attachments beside it.

- **Timeline** — entries grouped by year and month, with a thumbnail of the first photo or video.
- **Calendar** — month grid, days that have an entry are filled in.
- **Attachments** — photos and video via the photo picker, audio, any file, plus camera, video
  capture and a microphone recorder.
- **OTA updates** — the app checks the latest GitHub Release on this repo and offers to install it.

## Layout

```
app/src/main/java/app/ujournal/
  MainActivity.kt   screens: timeline, calendar, day editor, recorder, update dialog
  Store.kt          reading and writing entries and attachments
  Updater.kt        GitHub Release check, APK download, install intent
  Theme.kt          colours and the Material3 theme
app/src/main/res/   manifest resources (theme, strings, icon, file paths)
ujournal.jks        release signing keystore (used by the release workflow)
```

## Build

Needs JDK 17 and the Android SDK with platform 34.

```sh
gradle :app:assembleDebug        # app/build/outputs/apk/debug/app-debug.apk
gradle :app:assembleRelease      # signed with ujournal.jks
```

`VERSION_NAME` (default `1.0.0`) and `GITHUB_RUN_NUMBER` (used as `versionCode`) are read from
the environment, so CI decides the version and local builds stay at `1`.

## Actions

- **Build APK** (`.github/workflows/build.yml`) — runs on every push to `main`, on pull requests
  and on demand. Assembles the debug and release APK and uploads both as one artifact.
- **Release APK** (`.github/workflows/release.yml`) — runs on a `v*` tag, or on demand with a
  version input. Builds the signed APK and publishes it as a GitHub Release, which is what the
  in-app updater reads.

```sh
git tag v1.0.1 && git push origin v1.0.1
```

## Signing

The release keystore is committed as `ujournal.jks`. To use a different key, set
`SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS` and `SIGNING_KEY_PASSWORD` in the environment
(locally) or as repository secrets and pass them to the build step.
