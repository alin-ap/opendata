from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from opendata.metadata import load_metadata
from opendata.publish import publish_parquet_file, upload_readme
from opendata.registry import Registry
from opendata.storage import storage_from_env


def _default_version() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _producer_dirs(root: Path) -> list[Path]:
    return sorted(
        [p for p in root.glob("*/") if (p / "main.py").exists() and (p / "opendata.yaml").exists()]
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="producers/official")
    parser.add_argument("--version", default=_default_version())
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args(argv)

    storage = storage_from_env()
    reg = Registry(storage)

    root = Path(args.root)
    dirs = _producer_dirs(root)
    allow = set(args.only)

    for d in dirs:
        meta = load_metadata(d / "opendata.yaml")
        if allow and meta.id not in allow and d.name not in allow:
            continue
        print(f"[run] {meta.id} ({d})")

        subprocess.run([sys.executable, "main.py"], cwd=str(d), check=True)
        parquet_path = d / "out" / "data.parquet"
        if not parquet_path.exists():
            raise RuntimeError(f"producer did not write {parquet_path}")

        publish_parquet_file(
            storage, dataset_id=meta.id, parquet_path=parquet_path, version=args.version
        )

        readme_path = d / "README.md"
        if readme_path.exists():
            upload_readme(storage, dataset_id=meta.id, readme_path=readme_path)

        reg.register(meta)
        reg.refresh_stats(meta.id)

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
