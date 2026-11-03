# UJournal

A calm, tan-pastel native Android journal (Kotlin + Jetpack Compose), inspired by iOS Journal.

- **Journal tab** – entries grouped by year → month, newest first
- **Calendar tab** – tap any day to open its entry; days with entries are filled in
- **Attachments** – upload photos, videos, audio or any file, or capture a photo / video / voice recording in-app (stored privately on-device)
- **OTA updates** – on launch the app checks your latest GitHub Release and offers to install it

## Setup (once)
1. Edit `GITHUB_REPO` in `app/build.gradle.kts` -> `"yourname/UJournal"` (repo must be **public**).
2. That's it. No secrets needed: the signing key (`ujournal.jks`) is included so every build is signed the same and updates install over the old version. (It's a personal-use key; don't reuse it for anything important.)

## Ship a version / push an OTA update
```
git tag v1.0.1 && git push origin v1.0.1
```
GitHub Actions builds and attaches `UJournal.apk` to a Release. Installed apps see the newer tag and prompt to update.
First install: download that APK from Releases onto your phone.

## Local build
Open in Android Studio and run (debug), or `gradle assembleDebug`.
