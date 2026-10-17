# SSMD rename

Rename the current app to **Slulisee's simple media downloader / SSMD** in the
window, sidebar, About, translated help, build targets, packages, installer,
Start menu, uninstaller and current guides. Preserve **made by Slulisee**.

Version 1.4.0 keeps the existing release repository URL so v1.3.0's strict
updater still works. Publish legacy-named update/download aliases alongside
the new SSMD assets. New SSMD checks prefer SSMD packages. Keep private yt-dlp
plugin and SSMP handoff protocol identifiers compatible.

The first normal SSMD launch copies settings, queue and wallpaper from the old
SSYTDLP data folder into the new SSMD folder if no SSMD data exists. Keep the old
folder intact, update a copied internal wallpaper path, and never merge over
existing SSMD settings. Windows setup can upgrade a folder containing either
executable, retain tools, replace the old executable and update registration.

Validate legacy updater selection and checksums, translated branding, data
migration, real old-to-new Windows setup, new frozen startup, uninstall and
rollback. Refresh real UI screenshots. No media features change.
