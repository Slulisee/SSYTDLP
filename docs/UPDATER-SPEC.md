# Installer and app updates

Version 1.3.0 adds a manual **Settings → App updates** page. It shows the GUI
version, checks this repository's latest stable GitHub release without freezing
the interface, and downloads the matching native package after SHA256 validation.
The existing **Update nightly** action remains independent.

Windows gets a per-user setup executable, Start menu entry and uninstaller.
Setup upgrades the selected program folder; settings, queue, wallpaper and media
stay in their existing locations. Existing engine files are retained. A smaller
app-only update installer omits engines and requires an existing complete app.
The app can download that installer, close, and open setup at its current folder.
Setup waits for running app instances to close before replacing program files.
The finish page can reopen the app. Downloads and updates cannot overlap.

macOS and Linux get the same checker and verified native archive download, then
open the download folder for the platform's existing manual replacement process.
No automatic installation on startup, privileged service or new media features.

Checks: existing suite, release/version/URL/checksum/error/cancellation tests,
translated button and busy states, actual Windows fresh install, in-place upgrade,
engine/data retention, running-app guard, uninstall, frozen startup, and isolated
rollback. CI builds native archives on all three supported operating systems.
