# SSYTDLP 1.2.1 verification

17 October 2026. This patch adds the existing **Fetch queued links** action to the Downloader page's queue toolbar. It uses the existing translations and batch-fetch workflow, including opening the detailed Queue page. The toolbar fits its four actions into two columns.

- Existing suite: **66 tests passed** on Windows (`python -m unittest discover -q`, from `source`, 16.193 seconds).
- Click verification: stage a URL without fetching; click the new Downloader button; verify that its title/selection resolve and the detailed Queue page opens.
- State verification: button disabled for an empty queue, during an operation and after all links resolve; enabled for unfetched links.
- Layout verification: English, German, Spanish and French fit without horizontal scrolling at widths 900, 1120, 1320 and 1800 pixels.
- The updated screenshot captures the actual Windows GUI, using the same public SoundCloud metadata and labeled generated layout playlists as 1.2.0.

The release workflow runs the existing native tests, nightly integration, package builds and Windows/Linux frozen startup checks. Those results remain distinct from interactive macOS/Linux download testing. See [1.2.0 verification](VERIFICATION-v1.2.0.md) for the underlying cookie, lyrics, metadata and real download checks; this patch changes only the shortcut and toolbar layout.
