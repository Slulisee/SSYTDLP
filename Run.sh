#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if ! test -f .venv/bin/python; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check -r source/requirements.txt
if ! test -f tools/yt-dlp; then
    .venv/bin/python source/prepare_tools.py
fi
exec .venv/bin/python source/app.py
