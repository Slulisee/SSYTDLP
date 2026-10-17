# Contributing

Keep SSMD small and practical. Open an issue for larger changes and use a pull
request for fixes. Describe the trigger, resulting behavior and actual checks.

1. Follow [BUILD.md](docs/BUILD.md) and run the unit suite.
2. Add a short user-facing entry under **Unreleased** in `CHANGELOG.md`.
3. Update the installation/usage guide if behavior or dependencies change.
4. Update real screenshots for visible UI changes; use example entries and a generic path.
5. Keep EN/DE/ES/FR translation keys and placeholders aligned.
6. Distinguish automated checks, real downloads and untested platform behavior.

Do not commit media, credentials, personal settings, queue files, virtual
environments or engine binaries. Release binaries belong in GitHub Releases.
Preserve the nightly engine channel, hash checks and direct subprocess arguments.
Preserve dependency notices and source attribution. Tests should verify behavior.

For releases: date a changelog version, use a matching `vX.Y.Z` tag, copy that
section into release notes, and verify all attached assets/checksums after CI.
