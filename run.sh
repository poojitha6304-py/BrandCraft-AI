#!/bin/sh
cd "$(dirname "$0")"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
$PY -m pip install --disable-pip-version-check -q -r requirements.txt
$PY launch.py
