# Validation record

Local Windows checks on 2026-10-16 before publication:

- 25 unit tests cover argument construction, metadata options, nightly checksums,
  playlist subsets, queue recovery/cancellation, translations, matching and catalog parsing.
- Frozen Windows GUI startup, six metadata/lyric/subtitle controls, settings apply,
  persistence, light/dark themes, wallpaper and selectable playlist preview passed.
- YouTube MP3 with LRC and embedded USLT; public SoundCloud HLS-to-MP3;
  Spotify/Deezer catalog-to-YouTube MP3 matching; real YouTube SRT subtitle sidecar passed.
- Spotify album/playlist and Deezer album previews returned expected visible entries.
- Apple Music track preview passed; a separate Apple-origin download was not run.
- Synthetic audio/video fixtures verified tag preservation and five lyric-tag formats.
- The earlier Windows build was restored on a separate copy and its original hash verified.

These describe the Windows development checks, not a promise for every site.
CI results for this published source are visible under [Actions](https://github.com/Slulisee/SSYTDLP/actions).
Windows/Linux frozen startup checks in CI are distinct from full interactive use.
macOS/Linux real desktop downloads have not been verified locally.

Tests use synthetic lyrics. No downloaded media or real lyric text is stored in Git.
