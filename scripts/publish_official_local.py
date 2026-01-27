from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from opendata.ids import stats_key
from opendata.metadata import load_metadata
from opendata.portal_publish import publish_portal_assets
from opendata.registry import Registry
from opendata.storage import storage_from_env


def _producer_dirs(root: Path) -> list[Path]:
    return sorted(
        [p for p in root.glob("*/") if (p / "main.py").exists() and (p / "opendata.yaml").exists()]
    )


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

            env = dict(**os.environ)

            # Ensure all producers write into the same local storage directory.
            if env.get("OPENDATA_STORAGE", "").strip().lower() in {"local", "file"}:
                base = Path(env.get("OPENDATA_LOCAL_STORAGE_DIR", ".opendata/storage")).resolve()
                env["OPENDATA_LOCAL_STORAGE_DIR"] = str(base)

            subprocess.run([sys.executable, "main.py"], cwd=str(d), env=env, check=True)

            # Ensure the producer actually published stats.
            if not storage.exists(stats_key(meta.id)):
                raise RuntimeError("producer did not publish stats.json")

            successes += 1
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
