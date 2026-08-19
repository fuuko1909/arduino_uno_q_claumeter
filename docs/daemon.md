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

# Serial port. On the UNO Q this is /dev/ttyHS1.
# For local testing on a PC, set this to stdout to print JSON payloads.
serial_port = /dev/ttyHS1
serial_baud = 115200

# How often to poll Anthropic (seconds)
poll_interval = 60
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

### Local test mode (no UNO Q required)

Set `serial_port = stdout` in the config, then run:

```bash
python3 claude_usage_daemon.py --once
```

This prints one JSON payload to stdout so you can verify token reading and API polling without hardware.

## Test scripts

- `test_token.py` — verifies that a token can be extracted from the configured credentials file (token is never printed).
- `test_multiaccount.py` — verifies the multi-account payload structure using mock credentials.

```bash
python3 test_token.py
python3 test_multiaccount.py
```

## Install as systemd user service on the UNO Q

```bash
./install.sh
systemctl --user enable --now claude-usage-daemon
systemctl --user status claude-usage-daemon
journalctl --user -u claude-usage-daemon -f
```
