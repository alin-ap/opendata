from __future__ import annotations

import argparse
import ast
import os
import runpy
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from opendata.ids import data_key, metadata_key
from opendata.metadata import DatasetCatalog, coerce_catalog
from opendata.portal_publish import publish_portal_assets
from opendata.registry import Registry
from opendata.storage import storage_from_env


def _load_catalog(main_path: Path) -> DatasetCatalog:
    raw = main_path.read_text(encoding="utf-8")
    tree = ast.parse(raw, filename=str(main_path))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "CATALOG":
                catalog = ast.literal_eval(node.value)
                return coerce_catalog(catalog)

    raise RuntimeError(f"missing literal CATALOG in {main_path}")


def _producer_entries(root: Path) -> list[tuple[Path, DatasetCatalog]]:
    entries: list[tuple[Path, DatasetCatalog]] = []
    for main_path in sorted(root.glob("**/main.py")):
        if main_path.name != "main.py":
            continue
        catalog = _load_catalog(main_path)
        entries.append((main_path.parent, catalog))
    return entries


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
    parser.add_argument("--root", default="producers")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--ignore-failures", action="store_true")
    args = parser.parse_args(argv)

    storage = storage_from_env()
    reg = Registry(storage)

    root = Path(args.root)
    entries = _producer_entries(root)
    allow = set(args.only)

    failures: list[str] = []
    successes = 0

    for d, catalog in entries:
        try:
            if allow and catalog.id not in allow and d.name not in allow:
                continue
            print(f"[run] {catalog.id} ({d})")

            with _chdir(d):
                runpy.run_path(str(d / "main.py"), run_name="__main__")

            # Ensure the producer actually published the stable objects.
            if not storage.exists(data_key(catalog.id)):
                raise RuntimeError("producer did not publish data.parquet")
            if not storage.exists(metadata_key(catalog.id)):
                raise RuntimeError("producer did not publish metadata.json")

            reg.refresh_metadata(catalog.id)

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
