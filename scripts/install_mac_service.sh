#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

case "$PROJECT_DIR" in
  "$HOME/Desktop"/*|"$HOME/Documents"/*|"$HOME/Downloads"/*)
    echo "Move this project outside Desktop, Documents, or Downloads before installing the background service."
    exit 1
    ;;
esac

mkdir -p "$LAUNCH_AGENTS" "$PROJECT_DIR/logs"

cat > "$LAUNCH_AGENTS/com.hanashi.app.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.hanashi.app</string>
  <key>ProgramArguments</key><array><string>$PROJECT_DIR/scripts/launchd_app.sh</string></array>
  <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PROJECT_DIR/logs/app.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/logs/app.error.log</string>
</dict></plist>
EOF

launchctl bootout "gui/$(id -u)" "$LAUNCH_AGENTS/com.hanashi.app.plist" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENTS/com.hanashi.app.plist"

if command -v cloudflared >/dev/null 2>&1; then
  cat > "$LAUNCH_AGENTS/com.hanashi.tunnel.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.hanashi.tunnel</string>
  <key>ProgramArguments</key><array><string>$PROJECT_DIR/scripts/launchd_tunnel.sh</string></array>
  <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PROJECT_DIR/logs/tunnel.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/logs/tunnel.error.log</string>
</dict></plist>
EOF
  launchctl bootout "gui/$(id -u)" "$LAUNCH_AGENTS/com.hanashi.tunnel.plist" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENTS/com.hanashi.tunnel.plist"
fi

echo "Hanashi is running at http://127.0.0.1:${PORT:-8000}"
if command -v cloudflared >/dev/null 2>&1 && [ -f "$PROJECT_DIR/sharing_url" ]; then
  cat "$PROJECT_DIR/sharing_url"
elif ! command -v cloudflared >/dev/null 2>&1; then
  echo "Install cloudflared to enable a public HTTPS URL: brew install cloudflared"
fi