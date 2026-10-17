# Browser and YouTube cookies

Cookies are optional. They let the nightly engine use a signed-in session when a source asks you to log in or complete a CAPTCHA. They do not guarantee that a service will accept a request.

## Use a browser

1. Open **Settings → Cookies**.
2. Select your browser and click **Use this browser**.
3. Fetch your queued links again, then download as usual.

SSYTDLP remembers the browser choice. yt-dlp reads its default profile when a preview, fetch or download starts. SSYTDLP does not copy browser cookies into its settings. Close the browser if its database is locked. Browser encryption, OS permissions and newer Chromium protections can prevent extraction; use a Netscape export if that happens. Safari can require additional macOS file access. A browser missing on this device will produce an engine error; select an installed browser instead.

## Import a YouTube export

1. Use an exporter linked from the [official yt-dlp cookie FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp). Export in **Netscape cookies.txt** format, not JSON. YouTube-only exports avoid including unrelated sites.
2. For YouTube, follow the upstream private-window method: sign in in a new private window; in that same tab open `https://www.youtube.com/robots.txt`; export YouTube cookies; close the private window. See [yt-dlp’s YouTube export instructions](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies) for the maintained procedure and account/request-rate guidance.
3. In **Settings → Cookies**, choose **Import cookies.txt…**. The active-source message confirms the import.
4. Fetch or retry the affected links. Import again after restarting SSYTDLP.

The first line must be `# Netscape HTTP Cookie File` or `# HTTP Cookie File`. The importer accepts files up to 10 MB and validates their cookie records. The original file is never modified. Imported contents remain in memory for this session. Each engine process receives a temporary private copy, removed after normal completion, failure or cancellation. As with other applications, a forced OS shutdown can interrupt cleanup of temporary files.

Treat cookie exports like passwords. Keep them private and never attach them to issues or screenshots. **Disable / clear** stops using cookies and discards SSYTDLP’s imported reference. Delete your original export separately when you no longer need it. Cookies go only to the yt-dlp engine for media extraction; lyrics and catalog API clients do not receive them.

SSYTDLP intentionally does not export your whole browser profile. Its browser option uses the default profile; a custom-profile or private-window session should be exported to a file using the upstream guide.
