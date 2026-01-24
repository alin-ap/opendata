"""OpenData SDK.

This package is the Python SDK/CLI entrypoint described in `opendata.md`.
"""

from __future__ import annotations

from .client import load, push

__all__ = ["load", "push"]

__version__ = "0.1.0"
