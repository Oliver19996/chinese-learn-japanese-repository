#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

rm -f sharing_url
cloudflared tunnel --url "http://127.0.0.1:${PORT:-8000}" 2>&1 | while IFS= read -r line; do
  printf '%s\n' "$line"
  url=$(printf '%s\n' "$line" | sed -n 's#.*https://\([a-z0-9-]*\.trycloudflare\.com\).*#https://\1#p')
  if [ -n "$url" ]; then
    printf 'SHARING_URL="%s"\n' "$url" > sharing_url
  fi
done