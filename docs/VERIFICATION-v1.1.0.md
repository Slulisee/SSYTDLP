# SSYTDLP 1.1.0 verification

Windows x64 publication checkout, 2026-10-16:

```text
QT_QPA_PLATFORM=offscreen python -m unittest discover -s source -p 'test_*.py' -q
Ran 55 tests in 12.909s
OK
```

The working app passed 54 tests; the standalone publication also retains the
existing regression test restricting CI authorization to the HTTPS GitHub API.
Coverage includes 5,000 playlist entries, source/search filters, editing the
correct playlist, unavailable/unselected entries, download-state controls, four
languages at compact sizes, actual local HTTP thumbnails, failed-image caching,
bounded image storage and symmetric settings icons at the rendered UI sizes.

Real public YouTube metadata and thumbnail artwork loaded successfully for
`https://www.youtube.com/watch?v=jNQXAC9IVRw`. Native screenshots combine that
metadata example with a clearly labeled generated layout playlist.

The local redesigned Windows folder package started successfully, including the
detailed queue model and shared thumbnail cache. An isolated rollback restored
the previous executable/runtime/source and launched successfully. The installed
fixed build remained modified. Original nightly tools and download backend
checksums were preserved during those UI-fix checks.

Earlier in this update, a generated local media file passed through the real
nightly preview, staged queue, MP3/FFmpeg download and SSMP inbox handoff.

GitHub Actions builds the release source independently for each OS. Consult its
run for native packaging/startup results; these are separate from the local
interactive verification above. Interactive macOS/Linux downloads remain untested.

Final layout follow-up: the Linux DejaVu Sans reproduction initially exposed 14 pixels of French queue-toolbar overflow at 900 x 680. The compact toolbar now uses two rows; overflow is zero. The complete 55-test suite passed again on Windows and on a Linux Python 3.13 reproduction (27.824 seconds). GitHub CI uses Python 3.12 and reports its own final native results separately.
