# SSYTDLP

**Slulisee's Simple yt-dlp Downloader** · made by Slulisee

A small, practical desktop GUI for **yt-dlp nightly**. Preview playlists, choose
what you want, queue several links, and download when you're ready.

[Download](https://github.com/Slulisee/SSYTDLP/releases/latest) ·
[Install](docs/INSTALL.md) · [How to use](docs/USAGE.md) ·
[Changelog](CHANGELOG.md) · [Contribute](CONTRIBUTING.md)

![SSYTDLP in dark mode](docs/screenshots/dark.png)

## What it does

- Video presets: 1080p MP4, 720p MP4 and best-quality MKV.
- Audio presets: MP3, M4A, Opus and FLAC.
- Select individual playlist entries, then stage multiple videos or playlists.
- Choose your download folder, embed metadata and covers, and sort Artist / Album folders.
- Optional lyrics: timed LRC, plain text and supported embedded lyric tags.
- Optional subtitles: language selection, automatic captions and video embedding.
- Light and dark themes, custom wallpaper, and English / German / Spanish / French UI.
- Saved queues, cancellation, resume and duplicate skipping.
- Official nightly engine updates with SHA256 verification.

## Install

**Windows x64:** download the Windows ZIP from [Releases](https://github.com/Slulisee/SSYTDLP/releases/latest),
extract the **whole archive**, and run `SSYTDLP.exe`. Keep `tools` beside it.
Windows release builds include FFmpeg, ffprobe, Deno and yt-dlp nightly.

**macOS / Linux:** see the [platform installation guide](docs/INSTALL.md).
You can run the source or build on your target OS. FFmpeg is installed separately.
Native CI archives are unsigned; see the workflow results attached to each release.
Interactive download testing was performed on Windows; macOS/Linux desktop behavior
still needs community testing even when the native build passes CI.

## Use it

1. Paste a link and choose **Preview / Add**.
2. Select entries in the preview, then **Add to queue**. Repeat for more links.
3. Choose a preset, destination and optional metadata, lyrics or subtitles.
4. Press **Download queue**.

Open **Settings** for language, appearance, wallpaper and subtitle languages.
The [usage guide](docs/USAGE.md) explains selections, service imports and retries.

## Music services

YouTube, YouTube Music, SoundCloud and supported public media pages use yt-dlp.
Spotify, Deezer and Apple Music links import **public catalog metadata** and find
a matching recording on YouTube. The preview and log identify that route.
Spotify/Deezer public playlists are supported; Apple Music playlists are not.
Spotify embeds may expose only a subset. Lyrics are supplied by LRCLIB through
the community `syncedlyrics` library and depend on a confident match.

See [research, credits and tested examples](RESEARCH.md) and the
[personal-use notice](DISCLAIMER.md). Only download material you have permission
to save. Personal use does not itself grant copying rights.

## More previews

| Light theme | Playlist selection |
| --- | --- |
| ![Light theme](docs/screenshots/light.png) | ![Playlist selection](docs/screenshots/playlist.png) |

![Lyrics and subtitle settings](docs/screenshots/media-settings.png)

Screenshots show the real Windows UI with example queue entries; no media is
downloaded to create them. Layout and window decoration vary by platform.

## Source and development

The complete application source, tests and build scripts are public in `source/`.
Python 3.12 and Tkinter are required. See [BUILD.md](docs/BUILD.md) for the commands.
No API key or account login is required for the implemented public-source routes.

SSYTDLP's own source is [MIT licensed](LICENSE). Dependencies retain their own
open-source licenses, including GPL components in packaged builds; see
[THIRD_PARTY.md](THIRD_PARTY.md) and `licenses/` for notices and source links.

Updates go into [CHANGELOG.md](CHANGELOG.md), with release notes and checksums
published on [GitHub Releases](https://github.com/Slulisee/SSYTDLP/releases).
Please include your OS, app version, nightly version and a redacted log when
[reporting a bug](https://github.com/Slulisee/SSYTDLP/issues).
