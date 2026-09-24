#!/data/data/com.termux/files/usr/bin/bash

set -Eeuo pipefail

cd "$(dirname "$0")"

command -v python >/dev/null 2>&1 || {
  printf 'Python is not installed. Run: pkg install python\n' >&2
  exit 1
}

command -v ffmpeg >/dev/null 2>&1 || {
  printf 'FFmpeg is not installed. Run: pkg install ffmpeg\n' >&2
  exit 1
}

if command -v termux-open-url >/dev/null 2>&1; then
  (sleep 1; termux-open-url "http://127.0.0.1:8765") &
fi

python server.py
