from __future__ import annotations

import contextlib
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath

import pandas as pd

from opendata.client import load
from opendata.ids import data_key
from opendata.storage.http import HttpStorage


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_http_storage_can_load_dataset(tmp_path: Path) -> None:
    bucket_dir = tmp_path / "bucket"

    dataset_id = "getopendata/stooq-aapl-daily"
    df_in = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

    key = data_key(dataset_id)
    parquet_path = bucket_dir / Path(*PurePosixPath(key).parts)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df_in.to_parquet(parquet_path, index=False)

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
        df_out = load(dataset_id, storage=http_storage)
        pd.testing.assert_frame_equal(df_in, df_out)
    finally:
        httpd.shutdown()
