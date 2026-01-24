from __future__ import annotations

from pathlib import Path

from opendata.deploy import deploy_from_metadata


def test_deploy_writes_workflow(tmp_path: Path) -> None:
    (tmp_path / "opendata.yaml").write_text(
        """meta_version: 1
id: official/us-stock-daily
title: US Stock Daily
description: Daily OHLCV bars for US stocks.
license: MIT
source: https://example.com/source
repo: https://github.com/example/repo
""",
        encoding="utf-8",
    )

    workflow_path = deploy_from_metadata(repo_dir=tmp_path, meta_path=tmp_path / "opendata.yaml")
    assert workflow_path.exists()

    text = workflow_path.read_text(encoding="utf-8")
    assert "OPENDATA_R2_ENDPOINT_URL" in text
    assert "python main.py" in text
