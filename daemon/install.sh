#!/usr/bin/env bash
# Install the Claude usage daemon as a systemd user service on the UNO Q Linux side.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAEMON_DIR="$REPO_DIR/daemon"
CONFIG_DIR="$HOME/.config/claude-usage-monitor"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="claude-usage-daemon.service"

if [ ! -f "$DAEMON_DIR/claude_usage_daemon.py" ]; then
    echo "Error: claude_usage_daemon.py not found in $DAEMON_DIR"
    exit 1
fi

python3 -m venv "$DAEMON_DIR/.venv"
"$DAEMON_DIR/.venv/bin/pip" install -r "$DAEMON_DIR/requirements.txt"

mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config" ]; then
    cp "$DAEMON_DIR/config.example" "$CONFIG_DIR/config"
    echo "Created $CONFIG_DIR/config — please edit it with your Claude config directories."
fi

mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_DIR/$SERVICE_NAME" <<EOF
[Unit]
Description=Claude Usage Daemon for UNO Q
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DAEMON_DIR/.venv/bin/python $DAEMON_DIR/claude_usage_daemon.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"

echo "Installed. Start with: systemctl --user start $SERVICE_NAME"
echo "View logs with: journalctl --user -u $SERVICE_NAME -f"
