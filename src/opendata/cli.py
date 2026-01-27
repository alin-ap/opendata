from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .client import load
from .deploy import deploy_from_metadata
from .errors import OpendataError
from .metadata import load_metadata
from .publish import publish_parquet_file
from .registry import Registry
from .storage import storage_from_env


def _cmd_load(args: argparse.Namespace) -> int:
    storage = storage_from_env()

    df = load(args.dataset_id, storage=storage)
    head = int(args.head)
    print(df.head(head).to_string(index=False))
    print(f"\nrows={len(df)} cols={len(df.columns)}")
    return 0


def _cmd_push(args: argparse.Namespace) -> int:
    storage = storage_from_env()

    published = publish_parquet_file(
        storage,
        dataset_id=args.dataset_id,
        parquet_path=Path(args.parquet_path),
        write_metadata=not args.no_stats,
    )
    print(json.dumps(published.metadata(), indent=2, sort_keys=True))
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    from .scaffold import init_dataset_repo

    init_dataset_repo(dataset_id=args.dataset_id, directory=Path(args.dir))
    print(f"initialized dataset repo skeleton in {args.dir}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    meta = load_metadata(Path(args.meta))
    print(json.dumps(meta.to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_registry_add(args: argparse.Namespace) -> int:
    storage = storage_from_env()
    reg = Registry(storage, index_key=args.index_key)
    meta = reg.register_from_file(Path(args.meta))
    if args.refresh:
        reg.refresh_metadata(meta.id)
    print(f"registered {meta.id} into {reg.index_key}")
    return 0


def _cmd_registry_refresh(args: argparse.Namespace) -> int:
    storage = storage_from_env()
    reg = Registry(storage, index_key=args.index_key)
    reg.refresh_metadata(args.dataset_id)
    print(f"refreshed metadata for {args.dataset_id} in {reg.index_key}")
    return 0


def _cmd_deploy(args: argparse.Namespace) -> int:
    path = deploy_from_metadata(
        repo_dir=Path(args.dir),
        meta_path=Path(args.dir) / args.meta,
        cron=args.cron,
        python_version=args.python_version,
    )
    print(path)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="od")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_load = sub.add_parser("load", help="Load a dataset")
    p_load.add_argument("dataset_id")
    p_load.add_argument("--head", default="5")
    p_load.set_defaults(func=_cmd_load)

    p_push = sub.add_parser("push", help="Publish a parquet file")
    p_push.add_argument("dataset_id")
    p_push.add_argument("parquet_path")
    p_push.add_argument("--no-stats", action="store_true")
    p_push.set_defaults(func=_cmd_push)

    p_init = sub.add_parser("init", help="Create a dataset repo skeleton")
    p_init.add_argument("dataset_id")
    p_init.add_argument("--dir", default=".")
    p_init.set_defaults(func=_cmd_init)

    p_validate = sub.add_parser("validate", help="Validate dataset metadata")
    p_validate.add_argument("--meta", default="opendata.yaml")
    p_validate.set_defaults(func=_cmd_validate)

    p_registry = sub.add_parser("registry", help="Manage the dataset registry index")
    reg_sub = p_registry.add_subparsers(dest="registry_cmd", required=True)

    p_reg_add = reg_sub.add_parser("add", help="Register a dataset into index.json")
    p_reg_add.add_argument("meta")
    p_reg_add.add_argument("--index-key", default="index.json")
    p_reg_add.add_argument("--refresh", action="store_true")
    p_reg_add.set_defaults(func=_cmd_registry_add)

    p_reg_refresh = reg_sub.add_parser("refresh", help="Refresh from metadata.json")
    p_reg_refresh.add_argument("dataset_id")
    p_reg_refresh.add_argument("--index-key", default="index.json")
    p_reg_refresh.set_defaults(func=_cmd_registry_refresh)

    p_deploy = sub.add_parser("deploy", help="Generate a GitHub Actions workflow")
    p_deploy.add_argument("--dir", default=".")
    p_deploy.add_argument("--meta", default="opendata.yaml")
    p_deploy.add_argument("--cron", default="0 0 * * *")
    p_deploy.add_argument("--python-version", default="3.11")
    p_deploy.set_defaults(func=_cmd_deploy)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except OpendataError as e:
        parser.exit(2, f"error: {e}\n")
