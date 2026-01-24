from __future__ import annotations

from pathlib import Path

from .metadata import DatasetMetadata, save_metadata


def init_dataset_repo(*, dataset_id: str, directory: Path) -> None:
    """Create a minimal producer repo skeleton in `directory`."""

    directory.mkdir(parents=True, exist_ok=True)

    meta_path = directory / "opendata.yaml"
    if not meta_path.exists():
        meta = DatasetMetadata(
            meta_version=1,
            id=dataset_id,
            title="TODO: dataset title",
            description="TODO: dataset description",
            license="TODO: SPDX license",
            source="TODO: data source URL",
            repo="TODO: GitHub repo URL",
            tags=[],
            owners=[],
        )
        save_metadata(meta_path, meta)

    main_path = directory / "main.py"
    if not main_path.exists():
        main_path.write_text(
            """# Producer entrypoint for opendata\n"
            "#\n"
            "# Expected output: write a Parquet file to ./out/data.parquet\n"
            "# (the deployment workflow will upload it to R2)\n\n"
            "from __future__ import annotations\n\n"
            "from pathlib import Path\n\n"
            "import pandas as pd\n\n\n"
            "def main() -> None:\n"
            "    out_dir = Path('out')\n"
            "    out_dir.mkdir(parents=True, exist_ok=True)\n\n"
            "    # TODO: replace with real data fetch/transform\n"
            "    df = pd.DataFrame({'hello': ['world']})\n"
            "    df.to_parquet(out_dir / 'data.parquet', index=False)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n",
            encoding="utf-8",
        )

    readme_path = directory / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            """  # Dataset\n\n"
            "TODO: describe the dataset, sources, schema, and update schedule.\n",
            encoding="utf-8",
        )
