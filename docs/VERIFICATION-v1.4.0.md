# SSMD 1.4.0 verification

17 October 2026. This release renames the app and preserves the existing media
workflow. Product name: **Slulisee's simple media downloader / SSMD**.

- Unchanged v1.3.0 baseline: 75 Windows tests passed.
- Renamed source: 79 Windows tests passed, including translated branding,
  legacy-data copying, wallpaper paths, existing-data precedence, failed-copy
  recovery and renamed updater asset selection.
- Eight real Qt screenshots were refreshed. They show public SoundCloud metadata
  alongside explicitly labeled generated layout playlists, without user data.
- `verify_installer.py` checks actual fresh installation, upgrade, new branding,
  queue/preferences/tool retention, running-app protection and uninstall. Its
  optional pinned v1.3.0 ZIP exercises a real old-to-new executable upgrade.
  Its frozen-app test redirects LOCALAPPDATA into a generated profile to check
  the normal first-launch migration without accessing personal app data.
- The release workflow builds each native platform, verifies Windows setup and
  runs frozen Windows/Linux startup checks before publishing. Public Setup and
  Update packages are independently downloaded, checksum-checked and exercised
  after publication; the delivery verification report records those results.

The repository URL and legacy-named release aliases remain compatible with the
v1.3.0 updater. New checks use `SSMD-*` assets. Original user data stays intact
for rollback. Private yt-dlp metadata-plugin and SSMP protocol identifiers are
unchanged. New Windows installations use SSMD names; an upgraded program folder
may retain its old directory name to preserve paths and tools.

Packages remain unsigned. Interactive macOS/Linux desktop installation and a
clean Windows VM are not covered by local Windows verification.
