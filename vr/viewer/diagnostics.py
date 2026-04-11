"""Durable stage logging for VR startup debugging."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".bigym_vr_stage.log"


def log_stage(message: str) -> None:
    """Append a timestamped stage marker and flush it to disk."""
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")
    line = f"{timestamp} pid={os.getpid()} {message}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
