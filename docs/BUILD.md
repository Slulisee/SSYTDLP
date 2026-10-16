# Run and build from source

Use Python 3.12 with Tkinter. Clone this repository or extract its source ZIP.
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
python source/build.py
python source/package_native.py
```

Output: Windows `dist/SSYTDLP.exe`, macOS `dist/SSYTDLP.app`, or Linux
`dist/SSYTDLP`. Archives and SHA256 files go into `native-artifacts/`.
Keep packaged `tools` with the program. macOS/Linux use externally installed FFmpeg.
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
`contents: write` permission. A manually dispatched run only produces CI artifacts.

## Source map

| File | Purpose |
| --- | --- |
| `source/ui.py`, `dialogs.py`, `appearance.py` | GUI, previews, settings and themes |
| `source/engine.py` | yt-dlp arguments, download processes and nightly updater |
| `source/queue_model.py` | Persistent selections and sequential batch runner |
| `source/lyrics.py` | LRCLIB matching, sidecars and Mutagen tags |
| `source/services.py` | Catalog metadata and YouTube recording matching |
| `source/platform_support.py` | Host paths, executable names and folder opening |
| `source/i18n.py` | English, German, Spanish and French strings |

Native archives are unsigned. Signing/notarization is not configured.
