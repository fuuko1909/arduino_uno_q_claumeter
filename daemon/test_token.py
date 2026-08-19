#!/usr/bin/env python3
"""Quick sanity check that token extraction works for the default config dir.

The actual token is never printed.
"""

from pathlib import Path

from claude_usage_daemon import read_token


def main():
    default = Path.home() / ".claude"
    token = read_token(default)
    if token:
        print(f"OK: extracted token (length {len(token)}) from {default}")
    else:
        print(f"FAIL: no token found in {default}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
