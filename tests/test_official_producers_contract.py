from __future__ import annotations

from pathlib import Path

from opendata.metadata import load_metadata


def test_official_producers_have_required_files_and_unique_ids() -> None:
    root = Path(__file__).resolve().parents[1] / "producers" / "official"
    assert root.exists()

    ids: set[str] = set()
    for d in sorted([p for p in root.iterdir() if p.is_dir()]):
        meta_path = d / "opendata.yaml"
        main_path = d / "main.py"
        readme_path = d / "README.md"

        assert meta_path.exists(), f"missing {meta_path}"
        assert main_path.exists(), f"missing {main_path}"
        assert readme_path.exists(), f"missing {readme_path}"

        meta = load_metadata(meta_path)
        assert meta.meta_version == 1
        assert meta.id not in ids, f"duplicate dataset id: {meta.id}"
        ids.add(meta.id)
