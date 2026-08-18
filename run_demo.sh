#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/site"
python -m http.server 8000
