# Install SSYTDLP

Get packages from [GitHub Releases](https://github.com/Slulisee/SSYTDLP/releases).
Choose your OS and CPU. Source archives also work with the instructions below.

## Windows x64

Recommended: run **SSYTDLP-Windows-AMD64-Setup.exe** from
[Releases](https://github.com/Slulisee/SSYTDLP/releases/latest). Open SSYTDLP from
the Start menu. Setup installs for your Windows user under
`%LOCALAPPDATA%/Programs/SSYTDLP` by default. Re-running setup upgrades that folder.
Use Windows **Installed apps → SSYTDLP → Uninstall** to remove the program.
Uninstall keeps your separate settings, queue, wallpaper and downloaded media.

The portable ZIP remains available:

1. Download the `SSYTDLP-Windows-AMD64.zip` release asset.
2. Right-click the ZIP → **Extract all** into a folder you can keep.
3. Open the extracted folder and double-click **SSYTDLP.exe**.
4. Choose your download folder in the app.

No Python install is needed. Keep the entire `_internal` and `tools` folders alongside the EXE;
the Windows release includes nightly, Deno, FFmpeg and ffprobe.
The application is unsigned. Only use packages from this repository or build the
source yourself. Do not run the EXE from inside the ZIP.

## macOS

Source route:

1. Install Python **3.12** from [python.org](https://www.python.org/downloads/macos/).
2. Install FFmpeg, for example `brew install ffmpeg` with Homebrew.
3. Download and extract the release source ZIP.
4. In Terminal, change to the extracted folder and run:

```sh
bash Run.command
```

The launcher creates `.venv`, installs the pinned requirements and provisions
checksum-verified yt-dlp nightly plus Deno. With multiple Python installs, ensure
`python3 --version` selects Python 3.12. The pinned Qt wheel requires macOS 14 or newer.

If a native archive is available, select the CPU in its filename, extract it and
open `SSYTDLP.app`. Install FFmpeg first. These community builds are unsigned and
not notarized. Local builds on your Mac are documented in [BUILD.md](BUILD.md).

## Linux

Install Python 3.12, venv support, FFmpeg and Qt platform libraries. For example on Ubuntu 24.04:

```sh
sudo apt update
sudo apt install python3 python3-venv ffmpeg libegl1 libxcb-cursor0 libxkbcommon-x11-0
```

Extract the source archive, open a terminal in that folder, then:

```sh
bash Run.sh
```

A graphical X11/Wayland desktop is required. The launcher installs PySide6/Qt. A native Linux
archive, when provided, contains the `SSYTDLP` folder with its executable, `_internal/` and `tools/`; keep them
together, and run `./SSYTDLP`. Install FFmpeg separately. Builds made on Ubuntu
22.04 target glibc 2.35 or newer; not every Linux distribution is verified.

## Updates and saved data

Open **Settings → App updates** to check the latest stable SSYTDLP version and
download a package with SHA256 verification. On Windows, **Install update…** saves
your queue, closes the app, and opens setup at the existing app folder. Finish
the wizard to reopen the app. A smaller Update installer keeps existing engines.
On macOS/Linux, open the downloaded archive's folder, close the app, and replace
the program using the instructions above. Keep your downloaded media.
Settings and queue are stored outside the program:

| OS | Settings folder |
| --- | --- |
| Windows | `%LOCALAPPDATA%/SSYTDLP` |
| macOS | `~/Library/Application Support/SSYTDLP` |
| Linux | `$XDG_CONFIG_HOME/SSYTDLP` or `~/.config/SSYTDLP` |

**Update nightly** updates the bundled engine from the official nightly channel,
checks its SHA256, and keeps one previous engine. It does not update the GUI.
The **App updates** page updates the GUI separately. SHA256 files are included
with release assets. See [UPDATES.md](UPDATES.md) for older portable installations.

## Troubleshooting

- **Missing tool:** extract the entire archive; on macOS/Linux install FFmpeg.
- **Missing Qt platform library:** install the Linux packages above; keep `_internal` with the executable. A native XCB platform error may name an additional missing system library.
- **Site failure:** update nightly, retry, then include a redacted log in an issue.
- **Lyrics/subtitles missing:** the source or provider may not have a matching item;
  review Settings → Lyrics & subtitles and the download log.
- **Catalog subset:** public embeds may expose fewer entries than the original playlist.

Windows interactive behavior was tested. Native macOS/Linux compilation and CI
smoke results are separate from interactive desktop download testing.
