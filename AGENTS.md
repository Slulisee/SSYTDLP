# SSMD maintenance

- Preserve the product name SSMD and watermark made by Slulisee.
- Keep the interface simple and use official yt-dlp nightly with checksum verification.
- Add user-visible changes/fixes to CHANGELOG.md under Unreleased for every update.
- Update guides when behavior changes and real screenshots when the UI changes.
- Before release, move Unreleased entries into a dated version and write release notes.
- Run meaningful checks and clearly distinguish native builds from interactive testing.
- Keep all four translations aligned; preserve source and dependency license notices.
- Never publish local credentials, queue/settings files, logs containing secrets or downloaded media.
- Keep large binaries out of Git; attach them to Releases through the build workflow.
