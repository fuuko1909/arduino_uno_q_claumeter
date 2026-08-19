#!/usr/bin/env python3
"""Test the multi-account payload builder using mock credentials.

Creates two temporary config directories with fake .credentials.json files,
runs poll_all_accounts(), and verifies the resulting payload contains both
labels with the expected structure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Import the functions under test.
from claude_usage_daemon import poll_all_accounts


def make_fake_credentials(token: str) -> str:
    return json.dumps({"claudeAiOauth": {"accessToken": token}})


async def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dir_a = tmp_path / "claude-a"
        dir_b = tmp_path / "claude-b"
        dir_a.mkdir()
        dir_b.mkdir()

        (dir_a / ".credentials.json").write_text(make_fake_credentials("sk-ant-test-token-a"))
        (dir_b / ".credentials.json").write_text(make_fake_credentials("sk-ant-test-token-b"))

        # We expect the API call to fail because the tokens are fake, but the
        # daemon should still produce a payload with two account slots.
        cfg = {
            "config_dirs": [dir_a, dir_b],
            "labels": ["Personal", "Work"],
            "clock": "off",
            "chime": "off",
        }

        payload = await poll_all_accounts(cfg)
        print(json.dumps(payload, indent=2))

        accounts = payload.get("accounts", [])
        if len(accounts) != 2:
            print("FAIL: expected 2 account entries", file=sys.stderr)
            return 1
        if accounts[0].get("label") != "Personal" or accounts[1].get("label") != "Work":
            print("FAIL: labels did not match config", file=sys.stderr)
            return 1
        print("OK: multi-account payload structure is correct")
        return 0


if __name__ == "__main__":
    import asyncio

    raise SystemExit(asyncio.run(main()))
