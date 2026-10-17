# SSMD appearance

The downloader now follows the supplied Ocean-blue and Carbon-monochrome design
references, with a left sidebar, rounded cards, scalable native controls, consistent
icons, gradients and a useful empty queue. Its download engine and media features
remain the same. History presents the existing session activity log.

![Ocean reference theme](docs/screenshots/bulk-downloader.png)

![Visual theme selection](docs/screenshots/themes.png)

## Themes and your colors

Open **Settings → Appearance**. Choose a miniature interface preview to apply and
save its theme immediately:

Ocean, Carbon, Midnight, Aurora, Forest, Sunset, Sakura, Lavender, Frost, Sand,
Nord, Dracula, Espresso, Ruby, Lagoon and Contrast.

Under **Your colors**, click a swatch for the color picker or type `#RRGGBB`.
Customize accent/buttons, glow/highlights, background, card surfaces, main text,
secondary text and borders. Related control colors are derived automatically.
Use **Reset theme colors** to return to the selected theme's palette. Selecting
a different theme clears color overrides. The active preview reflects your colors.

Wallpaper is softly tinted behind the cards. The app copies the selected image;
your original is preserved. Old `light` settings become Frost and `dark` becomes
Ocean. Existing folders, presets, queue selections and SSMP preferences are retained.

## Navigation and settings

- **Downloader** shows the link, queue, options and destination.
- **Queue** opens a full-height table with every video inside the staged sources.
  Filter by playlist or search titles, artists and playlists. The selection marks
  include unselected and unavailable entries; source status identifies the state
  of each playlist. Select a row and use **Edit selection** (or double-click it)
  to change that playlist's existing selection. Download progress and cancellation
  remain available while browsing. Image loading is lazy and the table is virtualized.
- **History** shows this session's activity and engine diagnostics.
- **Settings** groups Appearance, Lyrics & subtitles, SSMP, and Services & personal use.
- **About** shows the app branding and existing service/privacy information.

Appearance and language changes save immediately. The **Apply** button saves media
and SSMP settings. The same six metadata/lyric/subtitle toggles and seven download
presets remain available. No additional downloading functions are introduced.

The downloader, full queue and playlist preview use the actual thumbnail URLs
returned in metadata. Images load in the background into a shared bounded cache;
missing or failed artwork retains an image/music icon. A playlist's compact row
uses the first selected video's available artwork, falling back to another entry.

**Ctrl+L** focuses/selects the link; **Ctrl+,** opens settings. Space toggles a
focused checkbox or playlist table selection. Delete removes queue entries only
while the queue table has focus. At smaller sizes the view scrolls and reflows;
playlist choices, presets and destination keep their existing behavior.

## Run and build

The redesigned GUI uses PySide6/Qt. Install `source/requirements.txt` in a Python
3.12 environment and run `python source/app.py`, or install the build requirements
and run `python source/build.py`. Tkinter is no longer the application view.
The Windows build helper isolates dependency scanning from unrelated tools on
PATH so their ICU/Qt libraries do not leak into the portable runtime.

On Windows, extract the entire **SSMD-Windows-AMD64.zip** and run
`SSMD.exe`. Keep `_internal` and `tools` with it. Replacing only the EXE is
insufficient. Earlier releases remain available from GitHub Releases.
Native macOS/Linux execution of this redesign is not verified on this Windows host.
Qt's pinned macOS wheel requires macOS 14 or newer.
