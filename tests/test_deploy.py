from __future__ import annotations

from pathlib import Path

from opendata.deploy import deploy_workflow


def test_deploy_writes_workflow(tmp_path: Path) -> None:
    workflow_path = deploy_workflow(repo_dir=tmp_path)
    assert workflow_path.exists()

    text = workflow_path.read_text(encoding="utf-8")
    assert "OPENDATA_R2_ENDPOINT_URL" in text
    assert "python main.py" in text
