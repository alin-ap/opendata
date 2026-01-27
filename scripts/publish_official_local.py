from __future__ import annotations

import argparse
import os
import runpy
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from opendata.ids import data_key, metadata_key
from opendata.metadata import load_metadata
from opendata.portal_publish import publish_portal_assets
from opendata.registry import Registry
from opendata.storage import storage_from_env


def _producer_dirs(root: Path) -> list[Path]:
    return sorted(
        [p for p in root.glob("*/") if (p / "main.py").exists() and (p / "opendata.yaml").exists()]
    )


@contextmanager
def _chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="producers/official")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--ignore-failures", action="store_true")
    args = parser.parse_args(argv)

    storage = storage_from_env()
    reg = Registry(storage)

    root = Path(args.root)
    dirs = _producer_dirs(root)
    allow = set(args.only)

    failures: list[str] = []
    successes = 0

    for d in dirs:
        try:
            meta = load_metadata(d / "opendata.yaml")
            if allow and meta.id not in allow and d.name not in allow:
                continue
            print(f"[run] {meta.id} ({d})")

            with _chdir(d):
                runpy.run_path(str(d / "main.py"), run_name="__main__")

            # Ensure the producer actually published the stable objects.
            if not storage.exists(data_key(meta.id)):
                raise RuntimeError("producer did not publish data.parquet")
            if not storage.exists(metadata_key(meta.id)):
                raise RuntimeError("producer did not publish metadata.json")

            successes += 1
        except SystemExit as e:
            failures.append(f"{d.name}: {e}")
            print(f"[error] {d}: {e}")
            if not args.ignore_failures:
                raise
        except Exception as e:  # noqa: BLE001
            failures.append(f"{d.name}: {e}")
            print(f"[error] {d}: {e}")
            if not args.ignore_failures:
                raise

    # Build/refresh the global registry index after producers run.
    reg.build_from_producer_root(root)

    # Publish portal assets alongside the datasets.
    repo_root = Path(__file__).resolve().parents[1]
    portal_dir = repo_root / "portal"
    if portal_dir.exists():
        publish_portal_assets(storage, portal_dir=portal_dir)

    if failures:
        print("failures:")
        for f in failures:
            print(f"- {f}")
        if successes == 0:
            print("no datasets published; failing run")
            return 1
        if not args.ignore_failures:
            return 1

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
