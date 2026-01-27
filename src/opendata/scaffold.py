from __future__ import annotations

from pathlib import Path

from .metadata import DatasetMetadata, SourceInfo, save_metadata


def init_dataset_repo(*, dataset_id: str, directory: Path) -> None:
    """Create a minimal producer repo skeleton in `directory`."""

    directory.mkdir(parents=True, exist_ok=True)

    meta_path = directory / "opendata.yaml"
    if not meta_path.exists():
        meta = DatasetMetadata(
            meta_version=2,
            id=dataset_id,
            title="TODO: dataset title",
            description="TODO: dataset description",
            license="TODO: SPDX license",
            repo="TODO: GitHub repo URL",
            source=SourceInfo(provider="TODO: provider", homepage="TODO: homepage URL"),
            topics=[],
            owners=[],
        )
        save_metadata(meta_path, meta, include_meta_version=False)

    main_path = directory / "main.py"
    if not main_path.exists():
        main_path.write_text(
            """# Producer entrypoint for opendata\n"
            "#\n"
            "# This script should publish directly via the opendata SDK.\n"
            "# Configure storage via env vars (OPENDATA_STORAGE=local|r2, etc).\n\n"
            "from __future__ import annotations\n\n"
            "from pathlib import Path\n\n"
            "import pandas as pd\n\n\n"
            "from opendata.producer import publish_dataframe_from_dir\n\n\n"
            "def main() -> None:\n"
            "    producer_dir = Path(__file__).resolve().parent\n\n"
            "    # TODO: replace with real data fetch/transform\n"
            "    df = pd.DataFrame({'hello': ['world']})\n"
            "    publish_dataframe_from_dir(producer_dir, df=df)\n\n\n"
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
