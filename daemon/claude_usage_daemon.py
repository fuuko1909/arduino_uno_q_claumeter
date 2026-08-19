#!/usr/bin/env python3
"""Claude Usage Daemon for Arduino UNO Q (Linux MPU side).

Polls the Anthropic API for one or more Claude accounts and streams a
JSON payload to the STM32U585 MCU over the internal serial bridge
(typically /dev/ttyHS1 at 115200 baud).
"""

from __future__ import annotations

import calendar
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import serial

CONFIG_FILE = Path.home() / ".config" / "claude-usage-monitor" / "config"
DEFAULT_CONFIG_DIR = Path.home() / ".claude"

POLL_INTERVAL = 60
SERIAL_BAUD = 115200
API_URL = "https://api.anthropic.com/v1/messages"
API_BODY = {
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 1,
    "messages": [{"role": "user", "content": "hi"}],
}
API_HEADERS = {
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "oauth-2025-04-20",
    "Content-Type": "application/json",
    "User-Agent": "claude-code/2.1.5",
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def read_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "config_dirs": [DEFAULT_CONFIG_DIR],
        "labels": [],
        "clock": "off",
        "chime": "off",
        "serial_port": "/dev/ttyHS1",
        "serial_baud": SERIAL_BAUD,
    }
    if not CONFIG_FILE.exists():
        return cfg

    try:
        for raw in CONFIG_FILE.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if "=" not in line:
                continue
            key, val = [p.strip() for p in line.split("=", 1)]
            key = key.lower()
            if key == "config_dirs":
                cfg["config_dirs"] = [
                    Path(p.strip()).expanduser()
                    for p in val.split(",")
                    if p.strip()
                ]
            elif key == "labels":
                cfg["labels"] = [p.strip() for p in val.split(",")]
            elif key == "clock":
                cfg["clock"] = val.lower()
            elif key == "chime":
                cfg["chime"] = val.lower()
            elif key == "serial_port":
                cfg["serial_port"] = val
            elif key == "serial_baud":
                try:
                    cfg["serial_baud"] = int(val)
                except ValueError:
                    pass
    except OSError as e:
        log(f"Config read failed: {e}")
    return cfg


def _extract_token(blob: str) -> str | None:
    blob = blob.strip()
    if not blob:
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        if isinstance(data.get("accessToken"), str):
            return data["accessToken"]
        for v in data.values():
            if isinstance(v, dict) and isinstance(v.get("accessToken"), str):
                return v["accessToken"]
    m = re.search(r'"accessToken"\s*:\s*"([^"]+)"', blob)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_\-.~+/=]{20,}", blob):
        return blob
    return None


def read_token(config_dir: Path) -> str | None:
    cred = config_dir / ".credentials.json"
    if not cred.exists():
        return None
    try:
        return _extract_token(cred.read_text())
    except OSError as e:
        log(f"Error reading {cred}: {e}")
        return None


def reset_minutes(reset_ts: str, now: float) -> int:
    try:
        r = float(reset_ts)
    except ValueError:
        return 0
    mins = (r - now) / 60.0
    return int(round(mins)) if mins > 0 else 0


def pct(util: str) -> int:
    try:
        return int(round(float(util) * 100))
    except ValueError:
        return 0


def _billing_period_info(now: float, reset_ts: str) -> dict[str, Any]:
    try:
        period_end = float(reset_ts)
    except ValueError:
        return {"tp": 0, "pd": 30}
    if period_end <= 0:
        return {"tp": 0, "pd": 30}
    dt_end = datetime.datetime.fromtimestamp(period_end)
    prev_month = dt_end.month - 1 or 12
    prev_year = dt_end.year if dt_end.month > 1 else dt_end.year - 1
    prev_day = min(dt_end.day, calendar.monthrange(prev_year, prev_month)[1])
    dt_start = dt_end.replace(year=prev_year, month=prev_month, day=prev_day)
    period_len = period_end - dt_start.timestamp()
    if period_len <= 0:
        return {"tp": 0, "pd": 30}
    pct_val = (now - dt_start.timestamp()) / period_len * 100
    total_days = int(round(period_len / 86400))
    return {
        "tp": max(0, min(100, int(round(pct_val)))),
        "pd": total_days,
        "rd": f"{dt_end.strftime('%b')} {dt_end.day}",
    }


def poll_account(token: str) -> dict[str, Any] | None:
    headers = dict(API_HEADERS)
    headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(API_URL, headers=headers, json=API_BODY)
    except httpx.HTTPError as e:
        log(f"API call failed: {e}")
        return None

    if resp.status_code in (401, 403):
        log(f"API HTTP {resp.status_code} (token expired/invalid)")
        return {"ok": False, "error": "token_expired"}
    if resp.status_code >= 400:
        log(f"API HTTP {resp.status_code}: {resp.text[:200]}")
        return None

    now = time.time()

    if resp.headers.get("anthropic-ratelimit-unified-5h-utilization"):
        return {
            "ok": True,
            "s": pct(resp.headers.get("anthropic-ratelimit-unified-5h-utilization", "0")),
            "sr": reset_minutes(resp.headers.get("anthropic-ratelimit-unified-5h-reset", "0"), now),
            "w": pct(resp.headers.get("anthropic-ratelimit-unified-7d-utilization", "0")),
            "wr": reset_minutes(resp.headers.get("anthropic-ratelimit-unified-7d-reset", "0"), now),
            "st": resp.headers.get("anthropic-ratelimit-unified-5h-status", "unknown"),
            "acct": "pro",
        }
    else:
        reset_ts = resp.headers.get("anthropic-ratelimit-unified-overage-reset", "0")
        return {
            "ok": True,
            "s": pct(resp.headers.get("anthropic-ratelimit-unified-overage-utilization", "0")),
            "sr": reset_minutes(reset_ts, now),
            "w": 0,
            "wr": 0,
            "st": resp.headers.get("anthropic-ratelimit-unified-status", "unknown"),
            "acct": "ent",
            **_billing_period_info(now, reset_ts),
        }


def detect_hour_format() -> int:
    try:
        import locale
        locale.setlocale(locale.LC_TIME, "")
        fmt = locale.nl_langinfo(locale.T_FMT)
        if "%p" in fmt or "%r" in fmt or "%I" in fmt:
            return 12
    except Exception:
        pass
    return 24


def add_clock_fields(payload: dict[str, Any], cfg: dict[str, Any]) -> None:
    clock = cfg.get("clock", "off")
    if clock == "off":
        return
    tf = 24 if clock == "24" else 12 if clock == "12" else detect_hour_format()
    payload["t"] = int(time.time()) + time.localtime().tm_gmtoff
    payload["tf"] = tf


def build_payload(cfg: dict[str, Any]) -> dict[str, Any]:
    dirs = cfg.get("config_dirs", [DEFAULT_CONFIG_DIR])
    labels = cfg.get("labels", [])
    accounts: list[dict[str, Any]] = []
    any_live = False
    all_dead = True

    for i, d in enumerate(dirs):
        token = read_token(d)
        if not token:
            log(f"No token in {d}; skipping")
            continue
        any_live = True
        result = poll_account(token)
        if result is None:
            all_dead = False  # transient failure, retry later
            continue
        if not result.get("ok"):
            accounts.append({
                "ok": False,
                "label": labels[i] if i < len(labels) else f"Account {i + 1}",
                "error": result.get("error", "unknown"),
            })
            all_dead = False
            continue
        result["label"] = labels[i] if i < len(labels) else f"Account {i + 1}"
        accounts.append(result)

    payload: dict[str, Any] = {"ok": True, "accounts": accounts}
    if cfg.get("chime") == "on":
        payload["c"] = 1
    add_clock_fields(payload, cfg)
    return payload


def main() -> int:
    cfg = read_config()
    port = cfg.get("serial_port", "/dev/ttyHS1")
    baud = int(cfg.get("serial_baud", SERIAL_BAUD))
    log(f"=== UNO Q Claude Usage Daemon ===")
    log(f"Serial: {port} @ {baud}")
    log(f"Config dirs: {cfg.get('config_dirs')}")

    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        log(f"Cannot open serial port {port}: {e}")
        return 1

    last_poll = 0.0
    try:
        while True:
            now = time.time()
            if now - last_poll >= POLL_INTERVAL:
                payload = build_payload(cfg)
                line = json.dumps(payload, separators=(",", ":")) + "\n"
                log(f"Sending {len(line)} bytes")
                try:
                    ser.write(line.encode())
                except serial.SerialException as e:
                    log(f"Serial write failed: {e}")
                last_poll = now

            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
