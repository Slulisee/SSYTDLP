# Open-source dependencies and credits

SSYTDLP's own application source is MIT licensed; this does not replace the
licenses of linked or bundled dependencies. Packaged executables include GPL
components and their distribution must also meet those licenses. Complete app
source and build scripts are published here. Notices are in `licenses/` and
release packages. Versioned source links are listed below or recorded during build.

| Component | Role / license | Source |
| --- | --- | --- |
| yt-dlp nightly | Download engine; Unlicense source, bundled dependencies have additional licenses | [Repository](https://github.com/yt-dlp/yt-dlp), [nightly releases](https://github.com/yt-dlp/yt-dlp-nightly-builds/releases) |
| FFmpeg / ffprobe | Media conversion; bundled Windows Gyan essentials build is GPLv3 | [Source](https://github.com/FFmpeg/FFmpeg), [Gyan build/configuration](https://www.gyan.dev/ffmpeg/builds/) |
| Deno | JavaScript runtime; MIT | [Source and releases](https://github.com/denoland/deno) |
| Mutagen 1.48.1 | Lyrics/media tags; GPL-2.0-or-later | [Source](https://github.com/quodlibet/mutagen), [source distributions](https://pypi.org/project/mutagen/1.48.1/#files) |
| syncedlyrics 1.0.1 | LRCLIB provider client; MIT | [Source](https://github.com/moehmeni/syncedlyrics), [source distributions](https://pypi.org/project/syncedlyrics/1.0.1/#files) |
| LRCLIB | Community lyrics service | [Source](https://github.com/tranxuanthang/lrclib), [API](https://lrclib.net/docs) |
| Pillow 12.3.0 | Images; HPND and included component notices | [Source](https://github.com/python-pillow/Pillow) |
| Python / Tcl/Tk | Runtime and GUI; PSF / Tcl licenses | [Python](https://www.python.org/), [Tcl/Tk](https://www.tcl.tk/) |
| PyInstaller | Freezing; GPL with bootloader exception | [Source](https://github.com/pyinstaller/pyinstaller) |

Other Python dependencies and embedded image/runtime components retain their
notices. `prepare_release.py` collects installed package metadata and licenses.
`tools/engines.json` in each release records the actual engine versions, source
URLs and hashes. The FFmpeg notice includes its configuration and source revision.

[SongSync](https://github.com/Lambada10/SongSync) and
[spotDL](https://github.com/spotDL/spotify-downloader) informed the approach;
their source code is not copied into this project. See [RESEARCH.md](RESEARCH.md).
Lyrics and downloaded media have their own rights, separate from the app license.

## Qt desktop view

PySide6-Essentials and Shiboken6 use their upstream LGPL/GPL/commercial terms; Qt module terms also apply. The application code remains MIT. Official license texts, installed package notices and corresponding upstream source links are in `licenses/qt/`. Qt libraries are dynamically bundled in `_internal` and can be replaced.
