# Faster queues and cleaner music folders

## Collect links first

- Paste a link and press **Quick add** (or Enter). It is saved immediately; no preview or download starts.
- Use **Add multiple links** to paste one link per line. Whitespace-separated links also work. The whole input is checked before adding anything. Duplicate staged sources are skipped, including common YouTube tracking variants.
- Open **Queue → Fetch queued links** when ready. Titles, thumbnails and playlist contents load together. Every available entry starts selected; **Edit selection** changes a source’s choices.
- Filter by source or search across the queue. Select a source row and choose **Remove** to discard a failed or unwanted source. Fetch again to retry failures. Cancellation leaves unfinished links saved for later.
- Choose your format, metadata options and destination under **Download options**, then **Download queue**. If links remain unresolved, SSYTDLP fetches them first. It starts downloading only when that fetch completes without errors or cancellation. Fix or remove failed links before starting again.

**Preview / Add** is still available for inspecting a single link before adding it. It is optional.

## Artist / Album organization

New organized downloads use **album artist / album**, or the **primary artist / album** when no separate album artist is supplied. The full unique collaboration credit stays in the artist tag.

For example, both `s0rrow, s0rrow, s0rrow` and `s0rrow, Friend, s0rrow` use the `s0rrow` folder. Their artist tags become `s0rrow` and `s0rrow, Friend`. Structured artist lists preserve band names containing commas. Flat artist strings use comma, semicolon and featuring separators. Matching ignores Unicode presentation, case and repeated whitespace; it does not guess whether differently spelled stage names represent the same person. Existing matching primary folders are reused, including their capitalization.

This fixes naming for future downloads. It does not move existing folders or rewrite their tags. Download archives remain intact, so previously completed items continue to be skipped. You can organize older files separately after reviewing them.

## Lyrics

The lyrics toggle still saves LRC when available, a plain-text sidecar, provider provenance and optional embedded lyrics. The finder cleans presentation text such as “Official Audio,” deduplicates credits, tries primary-artist searches and then a combined LRCLIB query. Short songs can match when title, primary artist and duration agree. Live/remix/tempo variants and mismatched runtimes are rejected.

This improves discovery of community records, including indie music. Lyrics still depend on the provider’s coverage and the source’s metadata. Missing or uncertain lyrics leave the completed media intact. No lyrics are invented, and an unrelated search result is not accepted just because it is first.

The downloader queue now expands vertically with the window. The separate **Queue** page remains the best view for browsing every track in very large playlists.
