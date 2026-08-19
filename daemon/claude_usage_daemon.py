#!/usr/bin/env python3
"""Claude Usage Daemon for Arduino UNO Q (Linux MPU side).

Polls the Anthropic API for one or more Claude Code accounts in parallel and
streams a compact JSON payload to the STM32U585 MCU over the internal serial
bridge (typically /dev/ttyHS1 at 115200 baud).

Can also run in local test mode by setting serial_port = "stdout" or
"mock" in the config, which prints payloads instead of opening a serial port.
"""

from __future__ import annotations

import asyncio
import calendar
import datetime
import json
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# Optional import; only needed when serial_port is a real device.
try:
    import serial
except Exception:  # pragma: no cover - serial may be missing in test envs
    serial = None  # type: ignore

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
        "poll_interval": POLL_INTERVAL,
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
            elif key == "poll_interval":
                try:
                    cfg["poll_interval"] = int(val)
                except ValueError:
                    pass
    except OSError as e:
        log(f"Config read failed: {e}")
    return cfg


def _extract_access_token(blob: str) -> str | None:
    """Pull the accessToken out of a Claude credentials blob.

    Mirrors the logic in Clawdmeter's BLE daemon: the file may contain a
    bare token, a JSON object, or a nested object with multiple tokens.
    """
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
        log(f"No credentials file at {cred}")
        return None
    try:
        token = _extract_access_token(cred.read_text())
        if token:
            return token
        log(f"Could not extract token from {cred}")
        return None
    except OSError as e:
        log(f"Error reading {cred}: {e}")
        return None


def _pct(util: str) -> int:
    try:
        return int(round(float(util) * 100))
    except ValueError:
        return 0


def _reset_minutes(reset_ts: str, now: float) -> int:
    try:
        r = float(reset_ts)
    except ValueError:
        return 0
    mins = (r - now) / 60.0
    return int(round(mins)) if mins > 0 else 0


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


class TokenExpired(Exception):
    """Raised when Anthropic returns 401/403."""


async def poll_account(token: str, client: httpx.AsyncClient) -> dict[str, Any] | None:
    """Poll Anthropic for a single account. Returns a payload dict or None."""
    headers = dict(API_HEADERS)
    headers["Authorization"] = f"Bearer {token}"
    try:
        resp = await client.post(API_URL, headers=headers, json=API_BODY)
    except httpx.HTTPError as e:
        log(f"API call failed: {e}")
        return None

    if resp.status_code in (401, 403):
        log(f"API HTTP {resp.status_code} (token expired/invalid)")
        raise TokenExpired()
    if resp.status_code >= 400:
        log(f"API HTTP {resp.status_code}: {resp.text[:200]}")
        return None

    now = time.time()

    # Pro / Max accounts expose 5h/7d windows.
    if resp.headers.get("anthropic-ratelimit-unified-5h-utilization"):
        return {
            "ok": True,
            "s": _pct(resp.headers.get("anthropic-ratelimit-unified-5h-utilization", "0")),
            "sr": _reset_minutes(resp.headers.get("anthropic-ratelimit-unified-5h-reset", "0"), now),
            "w": _pct(resp.headers.get("anthropic-ratelimit-unified-7d-utilization", "0")),
            "wr": _reset_minutes(resp.headers.get("anthropic-ratelimit-unified-7d-reset", "0"), now),
            "st": resp.headers.get("anthropic-ratelimit-unified-5h-status", "unknown"),
            "acct": "pro",
        }

    # Enterprise / overage accounts use a single spending-limit window.
    reset_ts = resp.headers.get("anthropic-ratelimit-unified-overage-reset", "0")
    return {
        "ok": True,
        "s": _pct(resp.headers.get("anthropic-ratelimit-unified-overage-utilization", "0")),
        "sr": _reset_minutes(reset_ts, now),
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


async def poll_all_accounts(cfg: dict[str, Any]) -> dict[str, Any]:
    """Poll every configured account and build the combined payload."""
    dirs = cfg.get("config_dirs", [DEFAULT_CONFIG_DIR])
    labels = cfg.get("labels", [])

    tokens: dict[Path, str] = {}
    for d in dirs:
        token = read_token(d)
        if token:
            tokens[d] = token

    if not tokens:
        return {"ok": False, "error": "no_tokens"}

    accounts: list[dict[str, Any]] = []
    any_live = False

    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = {d: poll_account(token, client) for d, token in tokens.items()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for idx, (d, result) in enumerate(zip(tasks.keys(), results)):
        label = labels[idx] if idx < len(labels) else f"Account {idx + 1}"
        if isinstance(result, TokenExpired):
            accounts.append({"ok": False, "label": label, "error": "token_expired"})
            any_live = True
            continue
        if isinstance(result, Exception):
            accounts.append({"ok": False, "label": label, "error": type(result).__name__})
            continue
        if result is None:
            accounts.append({"ok": False, "label": label, "error": "poll_failed"})
            continue
        result["label"] = label
        accounts.append(result)
        any_live = True

    payload: dict[str, Any] = {"ok": any_live, "accounts": accounts}
    if cfg.get("chime") == "on":
        payload["c"] = 1
    add_clock_fields(payload, cfg)
    return payload


class Transport:
    """Abstraction over serial, stdout, or mock output."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.port = cfg.get("serial_port", "/dev/ttyHS1")
        self.baud = int(cfg.get("serial_baud", SERIAL_BAUD))
        self._ser: Any | None = None
        self.refresh_event = asyncio.Event()

    def open(self) -> bool:
        if self.port in ("stdout", "-", "mock"):
            log(f"Output mode: {self.port}")
            return True
        if serial is None:
            log("pyserial not installed; cannot open real serial port")
            return False
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=1)
            log(f"Opened {self.port} @ {self.baud}")
            return True
        except serial.SerialException as e:
            log(f"Cannot open serial port {self.port}: {e}")
            return False

    def write(self, line: bytes) -> bool:
        if self.port in ("stdout", "-"):
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
            return True
        if self.port == "mock":
            return True
        if self._ser is None:
            return False
        try:
            self._ser.write(line)
            return True
        except serial.SerialException as e:
            log(f"Serial write failed: {e}")
            self._ser = None
            return False

    def start_reader(self) -> None:
        """Start a background thread reading refresh commands from the MCU."""
        if self.port in ("stdout", "-", "mock") or self._ser is None:
            return
        import threading

        def reader():
            buf = ""
            while self._ser is not None:
                try:
                    data = self._ser.read(self._ser.in_waiting or 1)
                except serial.SerialException:
                    break
                if not data:
                    continue
                buf += data.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if '"cmd"' in line and '"refresh"' in line:
                        log("Refresh requested by MCU")
                        self.refresh_event.set()

        threading.Thread(target=reader, daemon=True).start()

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None


async def main(once: bool = False) -> int:
    cfg = read_config()
    poll_interval = int(cfg.get("poll_interval", POLL_INTERVAL))

    log("=== UNO Q Claude Usage Daemon ===")
    log(f"Poll interval: {poll_interval}s")
    log(f"Config dirs: {[str(d) for d in cfg.get('config_dirs', [DEFAULT_CONFIG_DIR])]}")

    transport = Transport(cfg)
    if not transport.open():
        return 1
    transport.start_reader()

    stop_event = asyncio.Event()

    def _stop(*_args: Any) -> None:
        log("Stopping")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, _stop)

    try:
        while not stop_event.is_set():
            payload = await poll_all_accounts(cfg)
            line = json.dumps(payload, separators=(",", ":")) + "\n"
            log(f"Sending {len(line)} bytes: {line.strip()[:200]}")
            ok = transport.write(line.encode())
            if not ok:
                log("Transport write failed; will retry connection next cycle")
                transport.close()
                if not transport.open():
                    log("Reconnection failed, sleeping")

            if once:
                break

            try:
                # Wake early if the MCU requests a refresh.
                done, pending = await asyncio.wait(
                    {stop_event.wait(), transport.refresh_event.wait()},
                    timeout=poll_interval,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for fut in pending:
                    fut.cancel()
                transport.refresh_event.clear()
            except asyncio.TimeoutError:
                pass
    finally:
        transport.close()

    return 0


if __name__ == "__main__":
    once = "--once" in sys.argv
    try:
        sys.exit(asyncio.run(main(once=once)))
    except KeyboardInterrupt:
        sys.exit(0)
