# Install once, update in place

## SSYTDLP → SSMD

Version 1.4.0 renames the app to **Slulisee's simple media downloader / SSMD**.
Use **Settings → App updates** in version 1.3.0 as usual. Its legacy-named
download contains the new SSMD installer. New downloads are named `SSMD-*`.
The GitHub repository URL remains stable for old updaters.

Setup accepts an existing `SSYTDLP.exe` folder, replaces it with `SSMD.exe`,
retains engines, and updates its Start menu and Installed apps entry. New
installations use `%LOCALAPPDATA%/Programs/SSMD` by default. An upgraded program
folder may retain its old directory name so existing tools and paths stay valid.

On the first normal SSMD launch, the app copies `settings.json`, `queue.json`,
`queue.bak` and `wallpaper.png` from the old SSYTDLP data folder to the new SSMD
folder if no SSMD folder exists. Internal wallpaper references follow the copy.
Existing SSMD data wins. The old folder, media and duplicate-download archive
stay intact. Cookie exports and old update downloads are not copied. SSMP and
the metadata plugin keep their private protocol identifiers for compatibility.
A private legacy registry location pointer also stays compatible; the visible
Start menu shortcut and Installed apps entry use SSMD.

## Windows

For a new installation, run **SSMD-Windows-AMD64-Setup.exe** from the
[latest release](https://github.com/Slulisee/SSYTDLP/releases/latest). The wizard
installs for your Windows user and adds a Start menu shortcut. Python is not required.

In version 1.3.0 and later:

1. Open **Settings → App updates** and click **Check for app updates**.
2. If a new version is available, click **Download update**. You can cancel the
   download. The current app stays intact until you choose to install.
3. After SHA256 verification, click **Install update…**. SSMD saves its queue,
   closes, and opens setup with the current app folder selected.
4. Complete setup and leave **Open SSMD** selected on the finish page.

The smaller **SSMD-Windows-AMD64-Update.exe** contains the app and its libraries,
without downloading FFmpeg, Deno and yt-dlp again. It requires a complete existing
Windows app folder. If engines are missing, the checker offers the full Setup
package instead. Both packages retain existing files in `tools`; use **Update
nightly** on Downloader to update yt-dlp independently.

For version 1.2.1 or older, close SSMD, download the Update installer once,
and choose the folder containing your existing `SSMD.exe`, `_internal` and
`tools`. Or use full Setup to install at the default location. The next version
will have the in-app update page. The portable ZIP is still supported.

Setup waits for all SSMD windows to close. A cancelled check, download or
setup does not remove your current app. Keep other copies closed during updates.
The installer is currently unsigned, like the portable executable.

## macOS and Linux

The same Settings page checks releases and downloads the correct native archive
with SHA256 verification. **Open download folder** shows that archive. Close
SSMD and replace its program files following [INSTALL.md](INSTALL.md).
The checker does not automatically extract or replace the app on these systems.
If your CPU/OS has no published matching package, the page links to the release.

## What stays

Settings, queue, wallpaper and the download archive live outside the program in
the [platform settings folder](INSTALL.md#updates-and-saved-data). Downloaded
media stays in your chosen destination. Setup and uninstall never delete those
folders. Files you placed in the program folder yourself are not recursively
deleted by uninstall; it removes its explicit app-file list and empty folders.

Version 1.5.0 enables optional daily background checks on Windows. A verified update installs silently after all app windows close. Disable **Download updates and install after closing** in Settings → App updates to keep updates manual. Checks and downloads do not block media jobs.

Manual controls remain available. They contact this project's public GitHub releases API; no
cookies, account data, queue or media URLs are sent. Only stable, newer releases
are offered. If assets are still uploading or a check fails, retry later.
Downloads are stored under the settings folder's `updates/<version>` subfolder.

Before a manual rollback, close the app and unpack a previous portable release
into a separate folder. Run it with the same external settings, or restore your
own settings backup if a future release documents a data format migration.
Version 1.3.0 does not change the settings or queue format.
