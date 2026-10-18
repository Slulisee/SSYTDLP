# Run and build from source

Use Python 3.12; the requirements install PySide6/Qt. Clone this repository or extract its source ZIP.
Build on the operating system and CPU you intend to support.

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r source/requirements-build.txt
.\.venv\Scripts\python.exe source/prepare_release.py
.\.venv\Scripts\python.exe source/app.py
```

## macOS / Linux

Install FFmpeg, then use `bash Run.command` on macOS or `bash Run.sh` on Linux.
For a build environment instead:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r source/requirements-build.txt
python source/prepare_release.py
python source/app.py
```

## Verify and package

Using the environment's Python:

```sh
python -m unittest discover -s source -p 'test_*.py' -v
python source/verify_update_native.py
python source/build.py
python source/package_native.py
```

Output: Windows `dist/SSMD/SSMD.exe`, macOS `dist/SSMD.app`, or Linux
`dist/SSMD/SSMD`. Archives and SHA256 files go into `native-artifacts/`.
Keep packaged `_internal`, `tools` and `plugin_bundle` with the program. The bundled SSMD metadata processor runs before filenames and embedded tags are written. macOS/Linux use externally installed FFmpeg.
Windows provisioning downloads and checksum-verifies the Gyan essentials FFmpeg build.

`prepare_tools.py` provisions official nightly and Deno; `prepare_release.py`
adds Windows FFmpeg and dependency notices. The original source license is MIT;
packaged dependencies retain their licenses. See [THIRD_PARTY.md](../THIRD_PARTY.md).

## GitHub Actions and releases

`build.yml` tests and builds on Windows, macOS and Linux. Windows/Linux also run
a minimal frozen-GUI startup check; macOS packaging is distinct from interactive
verification. CI artifacts are downloadable from a completed Actions run.

Before a release, fill `CHANGELOG.md`, add a dated version section, and update
screenshots when the UI changes. Create a GitHub release using a matching `vX.Y.Z`
tag and that changelog section as its notes. The published-release event builds
and attaches native archives and checksums. Release uploads require the workflow's
`contents: write` permission. A manually dispatched run produces CI artifacts by default. Supplying a draft release tag and enabling publish attaches verified assets and then publishes that draft.

## Source map

| File | Purpose |
| --- | --- |
| `source/desktop.py`, `qt_dialogs.py`, `ui_widgets.py`, `themes.py` | Qt GUI, previews, settings and themes |
| `source/engine.py` | yt-dlp arguments, download processes and nightly updater |
| `source/queue_model.py` | Persistent selections and sequential batch runner |
| `source/lyrics.py` | LRCLIB matching, sidecars and Mutagen tags |
| `source/services.py` | Catalog metadata and YouTube recording matching |
| `source/platform_support.py` | Host paths, executable names and folder opening |
| `source/i18n.py` | English, German, Spanish and French strings |

Native archives are unsigned. Signing/notarization is not configured.

## Windows installers

Install NSIS 3.x or point `NSIS_MAKENSIS` at a portable compiler's `makensis.exe`.
After `build.py`, run `python source/build_installer.py`. It creates the full
`SSMD-Windows-AMD64-Setup.exe` and smaller `SSMD-Windows-AMD64-Update.exe`,
with individual SHA256 files, under `native-artifacts/`.
`python source/verify_installer.py` exercises fresh installation, update, engine
retention, incomplete-folder rejection, running-app guard and uninstall in a
fresh `build/installer-verification` folder. It restores the previous product
registry entries and Start menu shortcut. Do not run it with SSMD open.

`source/version.py` is the GUI version. Update it with the release tag and dated
changelog. `app_updates.py` checks only this repository's stable releases and
fixed matching assets; `update_page.py` handles the Settings controls. `installer.nsi`
owns per-user setup. The workflow runs installer verification before publication.

Tests use `QT_QPA_PLATFORM=offscreen` in CI. macOS requires macOS 14+ for the pinned Qt wheel. Linux needs the system Qt/XCB/EGL dependencies listed in the workflow.

`automatic_updates.py` stages verified Windows updates in the user cache without locking media jobs; the app hands them to the silent installer on normal close. The same update preference disables checks and handoff. Pending files and checksums are revalidated before execution.
