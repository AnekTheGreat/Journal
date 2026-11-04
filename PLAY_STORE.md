# Putting UJournal on Google Play

Every release already attaches the bundle Play takes: `UJournal-<version>.aab`, signed with the
upload key. This file is the part that cannot be automated — the Console fields, the graphics, and
the declarations Play asks for before it reviews anything.

## 1. The upload

| | |
| --- | --- |
| File | `UJournal-1.3.0.aab` from the [latest release](../../releases/latest) |
| Application id | `app.ujournal` |
| Version name / code | `1.3.0` / `10300` — the code is computed from the name, so it only ever climbs |
| Min SDK | 26 (Android 8.0) |
| Target SDK | 36 — Play has refused an upload below API 36 since 31 August 2026 |
| Signing | upload key from the `KEYSTORE_BASE64` secret; Play App Signing re-signs what is delivered |

`release.yml` stops a release before publishing unless the bundle is API 36, the manifest asks for
no `REQUEST_INSTALL_PACKAGES`, `versionName`, the tag and the page's own `JOURNAL_PAGE` all agree,
and the page is inside the bundle.

**The screen updates outside Play, on purpose.** The UI is `assets/index.html`, and a release that
only changes it is fetched and swapped in place by the installed journal — the same thing SideCut,
MeasureT, My Hub and FamTM do. Play ships the shell (the bridge, the pickers, the recorder, the
update); the page is web content, not executable code, and it arrives with the release's own notes.

Turn on **Play App Signing**: Google then holds the app signing key and this repository only the
upload key, which is what makes a lost keystore survivable.

**A sideloaded copy cannot be upgraded through Play.** Play signs the delivered APK with its own
key, so a phone carrying `UJournal-1.3.0.apk` from the releases page has to uninstall it once before
installing from the store — and the journal's entries live in the app's own storage, so copy them
out first if they matter. A copy on 1.2.x also needs this one installed by hand once: it has no page
support, so it cannot receive the new screen over the air.

## 2. Store listing

- **App name** (30 characters): `UJournal`
- **Short description** (80): `A quiet paper-toned journal. One entry a day, kept as files on your phone.`
- **Category**: Lifestyle
- **Contact email**: the address on the developer account
- **Privacy policy URL**: required — the journal records audio and declares the microphone

Full description:

```
A quiet journal, one day at a time.

UJournal keeps one entry per day as plain files in the app's own storage: the text,
the photos, the video and the audio you add to it. No account, no sync, no server of
ours, nothing to sign up for.

A TIMELINE AND A CALENDAR
Entries are grouped by year and month, with a thumbnail of the first photo or video
beside each one; days that have an entry are filled in on the calendar. Tap a day to
write, or tap ＋ to write today.

WHAT CAN GO IN AN ENTRY
A title and as much text as you like, photos and video from the system picker, the
camera, video capture, a microphone recorder, and any other file you want to attach.
Everything is stored beside the entry, so the journal is yours in a folder you can
copy.

PAPER, NOT A DASHBOARD
Warm paper tones, a serif face for what you wrote, and no counters, streaks or
reminders.

WHAT LEAVES THE PHONE
Nothing you write. No analytics, no ads, no account. The only connection the journal
makes is to its own public GitHub releases, for the screen updates described below;
installed from Google Play it does not ask for a build, because Play updates it. The
microphone is used only while you are recording, and the recording is saved into the
entry it belongs to.

The screen updates itself over the air: a new version of the journal's own page is
fetched and swapped in place, with nothing installed and no installer prompt. The app
itself comes from Google Play when the journal is installed here. Installed by hand
instead, a new build opens its release page in your browser and your phone's own
installer takes the file from there — the journal never installs a package itself.
```

## 3. Graphics

| Asset | Size | Where |
| --- | --- | --- |
| App icon | 512 × 512 PNG, 32-bit, no alpha | [play/icon-512.png](play/icon-512.png) |
| Feature graphic | 1024 × 500 PNG/JPG | [play/feature-graphic.png](play/feature-graphic.png) |
| Phone screenshots | 2–8, at least 1080 px on the long edge | **still to take**: timeline, calendar, a day with a photo, the editor, the recorder |

The icon is the launcher icon redrawn at store size from the same 108-unit vector the app ships;
the feature graphic is that icon on the journal's own paper background.

## 4. App content

| Section | Answer |
| --- | --- |
| Ads | No ads |
| Data safety | **No data collected, no data shared.** Entries, photos and audio stay in the app's storage and are never transmitted |
| Microphone | Used for a recorded attachment only, on a button you press, and the file stays on the phone. This is the declaration Play asks for when an app declares `RECORD_AUDIO` |
| Photos and video | Chosen with the system picker or the camera; stored in the app's own folder, never uploaded |
| Content rating | Everyone, or Teen with user-generated content declared — the journal holds whatever the owner writes, and nothing is published from it |
| Target audience | 13+ |
| News app | No |
| In-app purchases | No — the tip jar opens Stripe in a browser and unlocks nothing |

## 5. Entries and uninstalling

The journal is files, not a database: `journal/YYYY-MM-DD/entry.json` plus attachments, in the
app's private storage. Android removes that folder when the app is uninstalled, and Play has no
cloud backup of it. Anyone moving from the sideloaded build to the store build should copy that
folder out first — Play App Signing means the two cannot be installed over each other.
