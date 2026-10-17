# SSYTDLP 1.2 update specification

Baseline: published SSYTDLP 1.1.0, commit f1a0f468ea5074f930ce5b419bbc580e3c5940b5. Preserve existing presets, themes, translations, playlist selection, nightly verification and SSMP handoff.

## Requested behavior

- Settings offers browser cookies or an imported Netscape cookies.txt. Imported contents stay in memory for the current session; per-process temporary jars are removed after completion, error or cancellation. Browser selection can be remembered. Include hover help and an export/import guide. Never persist cookie contents in settings, queue or diagnostics.
- Quick Add stages a URL immediately without network access. A multiline bulk dialog stages many URLs at once. Resolve staged links in the detailed Queue page, selecting available tracks by default, without repeated preview dialogs. Persist unresolved links, support cancellation, retry and removal. Downloads resolve pending links first and do not silently skip unresolved failures.
- Normalize repeated artist credits, preserve distinct collaborators in tags, and organize new media under the primary artist (or explicit album artist), then album. Do not move or rewrite previously downloaded media. Preserve download archives.
- Improve lyrics identity cleanup and bounded LRCLIB search fallbacks, including primary artist queries and short songs. Keep conservative identity/duration checks and provenance; missing lyrics never fail a download.
- Give surplus window height to the downloader queue. Draw checkbox focus/checked states within widget bounds. Keep compact layouts and all four languages usable.

## Verification and delivery

Run the existing suite before changes, add meaningful regressions for these behaviors, verify actual bundled nightly flags and metadata processing with synthetic media, test public metadata/lyrics examples, and build/test the portable Windows application. Record separately what was verified on Windows and what still needs native macOS/Linux testing. Provide updated guides, changelog, real screenshots and a verification report. Preserve the original checkout; verify rollback on a separate copy.
