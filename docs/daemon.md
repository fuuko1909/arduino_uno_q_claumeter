# Linux daemon

The daemon runs on the **Qualcomm QRB2210 Linux processor (MPU)** inside the Arduino UNO Q. It polls the Anthropic API for Claude usage and sends the data to the STM32U585 MCU over the internal serial bridge.

## Configuration

Create `~/.config/claude-usage-monitor/config`:

```ini
# Claude config directories, each containing .credentials.json
config_dirs = /home/arduino/.claude,/home/arduino/.claude-work

# Labels shown on the device for each account
labels = Personal,Work

# Clock display: off | auto | 12 | 24
clock = auto

# Optional chime when a session limit resets
chime = off
```

You must already be logged in with Claude Code in each config directory:

```bash
claude login --config-dir /home/arduino/.claude
claude login --config-dir /home/arduino/.claude-work
```

## Run manually

```bash
cd /path/to/arduino_uno_q_claumeter/daemon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 claude_usage_daemon.py
```

## Install as systemd user service

```bash
./install.sh
systemctl --user enable --now claude-usage-daemon
systemctl --user status claude-usage-daemon
journalctl --user -u claude-usage-daemon -f
```
