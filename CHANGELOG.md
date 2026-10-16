# Changelog

User-visible changes are recorded here. Versions follow `MAJOR.MINOR.PATCH`.
Unreleased entries move into a dated version before its GitHub release.

## [Unreleased]

## [1.0.0] - 2026-10-16

First public open-source release. Earlier development builds were distributed locally.

### Added
- Simple nightly-based downloader with video and audio presets and folder selection.
- Playlist preview with per-entry selection and a persistent queue for multiple links.
- Optional metadata, cover artwork, Artist / Album sorting and duplicate skipping.
- Lyrics via LRCLIB / syncedlyrics: LRC, text, attribution and supported embedded tags.
- Subtitles with language filters, optional automatic captions and video embedding.
- Public Spotify, Deezer and Apple Music catalog imports with YouTube matching.
- Four UI languages, light/dark themes, custom wallpaper and Slulisee branding.
- Cross-platform paths, source launchers, native build workflow and platform tutorials.
- Open-source notices, real preview screenshots, contributor instructions and release notes.

### Fixed
- Dark-theme checkboxes now visibly distinguish checked and unchecked states.
- Missing metadata fields no longer break the lyric JSON handoff.
- Optional lyric lookup handles transient provider failures and rejects weak matches.
- Lyrics/subtitle settings use distinct archive profiles to allow media enrichment.
- Catalog queue details remain readable across the earlier local-build rollback.
- Release notice collection preserves multiline package metadata without email-header parsing errors.

### Validation and limits
- Windows unit, GUI and real download checks are documented in `docs/VERIFICATION.md`.
- Native macOS/Linux build results appear in Actions; interactive use needs testing.
- Catalog imports are metadata-to-YouTube matches, not protected service audio.

[Unreleased]: https://github.com/Slulisee/SSYTDLP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Slulisee/SSYTDLP/releases/tag/v1.0.0

