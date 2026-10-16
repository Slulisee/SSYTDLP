# Validation record

Local Windows checks on 2026-10-16 before publication:

- 26 unit tests cover argument construction, metadata options, nightly checksums,
  playlist subsets, queue recovery/cancellation, translations, matching, catalog parsing
  and CI authentication host isolation.
- Frozen Windows GUI startup, six metadata/lyric/subtitle controls, settings apply,
  persistence, light/dark themes, wallpaper and selectable playlist preview passed.
- YouTube MP3 with LRC and embedded USLT; public SoundCloud HLS-to-MP3;
  Spotify/Deezer catalog-to-YouTube MP3 matching; real YouTube SRT subtitle sidecar passed.
- Spotify album/playlist and Deezer album previews returned expected visible entries.
- Apple Music track preview passed; a separate Apple-origin download was not run.
- Synthetic audio/video fixtures verified tag preservation and five lyric-tag formats.
- The earlier Windows build was restored on a separate copy and its original hash verified.

These describe the Windows development checks, not a promise for every site.
The [verified native CI run](https://github.com/Slulisee/SSYTDLP/actions/runs/38905530820)
passed all 26 unit tests and native packaging on Windows x64, Linux x86_64 and
macOS arm64. Frozen GUI startup passed on Windows and Linux under Xvfb. The macOS
job built and packaged the app; it did not exercise a graphical desktop session.
CI results for this published source are visible under [Actions](https://github.com/Slulisee/SSYTDLP/actions).
Windows/Linux frozen startup checks in CI are distinct from full interactive use.
macOS/Linux real desktop downloads have not been verified locally.

Tests use synthetic lyrics. No downloaded media or real lyric text is stored in Git.
