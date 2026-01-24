from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_dotenv(path: Optional[Path] = None, *, override: bool = False) -> bool:
    """Load environment variables from a local `.env` file.

    This is intentionally tiny (no extra dependency). It supports basic `KEY=VALUE`
    lines and ignores blank lines / comments.
    """

    env_path = path or Path(".env")
    if not env_path.exists():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        if not override and key in os.environ:
            continue
        os.environ[key] = value

    return True
