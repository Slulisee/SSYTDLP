# Changelog

User-visible changes are recorded here. Versions follow `MAJOR.MINOR.PATCH`.
Unreleased entries move into a dated version before its GitHub release.

## [Unreleased]

## [1.1.0] - 2026-10-16

### Changed
- Redesign the interface with a sidebar, rounded cards, responsive controls and Ocean/Carbon reference themes.
- Add sixteen visual theme previews and seven custom color controls, while preserving wallpaper and all four languages.
- Make Queue open a full-height, virtualized view of every playlist entry, including unselected/unavailable videos, with source/search filters and the existing selection editor.
- Show existing download progress and controls while browsing the detailed queue.
- Use PySide6/Qt for the desktop view; preserve queue/settings compatibility and the nightly download engine.
- Include optional completed-download handoff to SSMP.

### Fixed
- Replace the malformed settings icon with a centered, symmetric gear.
- Load actual metadata thumbnails in the downloader, queue and preview using a shared bounded background cache.
- Preserve fallback artwork for missing/broken images; avoid fetching every image in a large playlist at once.
- Keep keyboard shortcuts scoped to their controls and prevent closed previews from breaking theme changes.
- Isolate Windows dependency scanning from unrelated ICU libraries on PATH.

### Validation and limits
- 55 tests passed in the publication checkout, including the existing GitHub-auth regression test.
- A 5,000-entry queue, all four UI languages, HTTP image loading/failures, packaged Windows startup and isolated rollback passed.
- Real YouTube metadata/artwork and the existing local-media download/SSMP handoff were verified on Windows.
- Native CI build/smoke results are reported separately in Actions. macOS/Linux interactive downloads remain untested.

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
- Native CI provisioning uses scoped GitHub API authentication to avoid shared-runner rate limits.

### Validation and limits
- 26 tests and native packaging passed on Windows, macOS and Linux in GitHub Actions.
- Frozen Windows/Linux GUI startup passed; macOS/Linux interactive downloads still need testing.
- Windows GUI and real download checks are documented in `docs/VERIFICATION.md`.
- Catalog imports are metadata-to-YouTube matches, not protected service audio.

[Unreleased]: https://github.com/Slulisee/SSYTDLP/compare/v1.1.0...HEAD
[1.0.0]: https://github.com/Slulisee/SSYTDLP/releases/tag/v1.0.0

[1.1.0]: https://github.com/Slulisee/SSYTDLP/releases/tag/v1.1.0
