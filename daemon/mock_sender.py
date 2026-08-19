#!/usr/bin/env python3
"""Mock daemon for bench-testing the MCU firmware without real Claude tokens.

Sends a realistic two-account JSON payload over the configured serial port
every few seconds.
"""

import json
import sys
import time
from pathlib import Path

import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD = 115200
INTERVAL = 5


def make_payload():
    return {
        "ok": True,
        "accounts": [
            {
                "label": "Personal",
                "s": 42,
                "sr": 95,
                "w": 18,
                "wr": 5000,
                "st": "allowed",
                "acct": "pro",
            },
            {
                "label": "Work",
                "s": 78,
                "sr": 30,
                "w": 55,
                "wr": 3000,
                "st": "limited",
                "acct": "pro",
            },
        ],
    }


def main():
    print(f"Opening {PORT} @ {BAUD}")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    try:
        while True:
            line = json.dumps(make_payload(), separators=(",", ":")) + "\n"
            ser.write(line.encode())
            print("Sent:", line.strip())
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()
