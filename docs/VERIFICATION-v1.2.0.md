# SSYTDLP 1.2.0 verification

Windows x64, 17 October 2026. Baseline: published 1.1.0 commit `f1a0f468ea5074f930ce5b419bbc580e3c5940b5`.

## Automated behavior

Baseline: **55 tests passed**. Updated suite: **66 tests passed**. Both run with Python 3.12, the pinned GUI dependencies and `QT_QPA_PLATFORM=offscreen`. The local HTTP-thumbnail test requires loopback access.

New coverage includes session-only cookie persistence, temporary jar cleanup on success/interruption, unchanged original exports, browser argument selection, invalid exports, atomic bulk insertion, YouTube tracking deduplication, pending queue restart/order, legacy resolved-queue compatibility, fetch failure/cancellation, no repeated preview dialogs, no partial automatic download after a failed fetch, repeated artist credits, explicit album artists, structured band names, short indie lyrics and wrong artist/live/duration rejection. Existing large-queue, preset, updater, SSMP, theme and selection tests remain in the suite.

All four UI languages fit compact windows. The downloader queue grows with window height. The checkbox body/focus outline is inset into a wider widget. Native Windows screenshots show the real updated controls with a public SoundCloud preview and explicitly labeled generated layout entries; generated entries are not music-service results.

## Real nightly integration

`python source/verify_update_native.py` passed using the actual checksum-verified nightly executable and FFmpeg. It generated two short audio fixtures and downloaded them through a loopback HTTP server with a synthetic imported cookie. Both converted to MP3 in `s0rrow/Fixture Album`; tags retained distinct collaborators and removed repeated credits. The original cookie export’s SHA256 stayed unchanged. No real browser cookies or accounts were read.

The official nightly updater verified the current upstream release as **2026.10.10.233141** (SHA256 `e7cafc44db8aa433da8dd78303b9157f2c1dd509c4cbfcd8418081b7e1d26a7a`). The bundled plugin flags and execution stage were checked against that executable’s help and actual behavior.

The portable Windows build passed `python source/ci_smoke.py`: the GUI mapped, existing controls/providers/branding loaded, cookie and staged-link modules loaded, and the packaged nightly successfully ran the shipped metadata plugin on a simulated fixture.

## Public examples

- **SoundCloud — Forss / Flickermood:** real Quick Add → batch fetch → MP3 download through the app passed. The 8,591,938-byte test file had embedded cover art, artist and album artist `Forss`, and folder `Forss/Singles`. Test media and temporary settings were kept out of the source/release payload.
- **Rebzyyx — all i want is you:** repeated collaboration input found LRCLIB record `9602793`, including timed lyrics.
- **Rebzyyx — i deserve this:** found timed record `9156206`.
- **Cavetown — Home:** found timed record `1155305`.
- **YouTube:** the public test connection returned its sign-in / bot-confirmation challenge. The preview now retains that actionable engine error. A signed-in YouTube account/browser extraction was not tested. Synthetic cookie delivery and cleanup were tested independently; they do not establish that a particular browser profile will decrypt or that YouTube will accept a session.

Lyric availability, source metadata and service restrictions remain external conditions. Native macOS/Linux builds and integration results are reported by GitHub Actions for the release; they are distinct from interactive desktop/download verification, which was performed on Windows.

## Reproduce

```sh
python -m unittest discover -s source -p 'test_*.py' -q
python source/prepare_release.py
python source/verify_update_native.py
python source/build.py
python source/ci_smoke.py
python source/package_native.py
```

On Linux, launch GUI tests with the Qt dependencies and offscreen/Xvfb setup documented in the workflow. macOS packaging/startup requirements are documented in the platform guide. Never include a personal cookie export or queue in a bug report.
