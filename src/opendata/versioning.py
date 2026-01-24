from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def default_version(now: Optional[datetime] = None) -> str:
    """Default version string for datasets.

    The project supports per-dataset versioning strategies, but for early-stage
    usage we default to an ISO date (UTC), e.g. "2026-01-24".
    """

    dt = now or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
