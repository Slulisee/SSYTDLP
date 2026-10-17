# SSYTDLP 1.3.0 verification

17 October 2026. This release adds app updates and Windows installation without
changing the settings/queue format or media-download features.

- Baseline v1.2.1: **66 tests passed** before changes.
- Updated suite: **75 tests passed** on Windows, including stable version ordering,
  fixed release URLs, platform selection, incomplete uploads, checksum validation,
  corrupted/truncated/oversized downloads, cancellation, native installer command
  handling, translated controls and the verified-download-to-install UI handoff.
- A live request to this repository's release API succeeded. Existing v1.2.1
  releases without installers correctly show no ready installer asset.
- Actual Windows Setup: fresh installation and GUI startup passed in an isolated
  folder containing spaces. Real v1.2.1 release files were then put in that folder
  and upgraded with the smaller Update installer; the upgraded GUI opened.
- Queue, theme, language and destination survived the upgrade. Existing engine
  binaries and a deliberately changed engine manifest were retained.
- Update-only installation into an incomplete folder stopped with exit 3.
  The running-app mutex blocked replacement with exit 2. Silent install, upgrade
  and uninstall returned 0. Uninstall retained a user-created file and external
  app settings. Previous registry entries and Start menu shortcut were restored
  after the isolated tests.
- Two real generated-audio MP3 conversions with the bundled nightly, FFmpeg and
  synthetic cookies passed; artist/tag behavior still works.
- The new screenshot captures the actual Windows Qt Settings page.

The release workflow separately runs native builds on Windows, Linux and macOS;
Windows/Linux have frozen GUI startup checks, and Windows tests its actual
installer before publishing assets. Those CI results are visible on the release
commit. Interactive macOS/Linux update/install testing and a clean Windows VM
are not covered by the local Windows tests. Packages remain unsigned.
