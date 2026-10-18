# SSMD 1.5.0 verification

This update adds optional daily background app checks, SHA-256-verified staging and silent installation after closing. Existing manual controls, nightly-engine updates, settings, queue, media and branding are preserved.

The local full test suite includes background staging, checksum tampering, cache/repository boundaries, opt-out, silent handoff and existing downloader regressions. The packaged Windows installer is checked with fresh installation, upgrade, engine retention, running-app protection, frozen data migration and explicit-list uninstall. These checks use generated fixtures and restore pre-test app registration and shortcuts.

GitHub Actions builds/tests the declared Windows, Linux and macOS targets before publishing assets to the draft release. Consult the release's workflow run for those results; local Windows checks alone do not establish other operating systems. The installer remains unsigned.
