from __future__ import annotations

import contextlib
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd

from opendata.client import load
from opendata.publish import publish_parquet_file
from opendata.storage.http import HttpStorage
from opendata.storage.local import LocalStorage


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_http_storage_can_load_dataset(tmp_path: Path) -> None:
    bucket_dir = tmp_path / "bucket"
    storage = LocalStorage(bucket_dir)

    dataset_id = "official/stooq-aapl-daily"
    version = "2026-01-24"
    df_in = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parquet_path = tmp_path / "data.parquet"
    df_in.to_parquet(parquet_path, index=False)
    publish_parquet_file(storage, dataset_id=dataset_id, parquet_path=parquet_path, version=version)

    port = _free_port()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            super().__init__(*args, directory=str(bucket_dir), **kwargs)

        def log_message(self, format, *args):  # type: ignore[no-untyped-def]
            # Silence server logs in test output.
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    try:
        http_storage = HttpStorage(base_url=f"http://127.0.0.1:{port}/")
        df_out = load(
            dataset_id,
            version=version,
            storage=http_storage,
            cache_dir=tmp_path / "cache",
        )
        pd.testing.assert_frame_equal(df_in, df_out)
    finally:
        httpd.shutdown()
