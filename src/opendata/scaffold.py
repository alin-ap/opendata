from __future__ import annotations

from pathlib import Path


def init_dataset_repo(*, dataset_id: str, directory: Path) -> None:
    """Create a minimal producer repo skeleton in `directory`."""

    directory.mkdir(parents=True, exist_ok=True)

    main_path = directory / "main.py"
    if not main_path.exists():
        content = """# Producer entrypoint for opendata
#
# This script should publish directly via the opendata SDK.
# Configure storage via env vars (OPENDATA_STORAGE=r2|http, etc).

from __future__ import annotations

from pathlib import Path

import pandas as pd

from opendata.producer import publish_dataframe_from_dir

CATALOG = {
    "id": "__DATASET_ID__",
    "title": "TODO: dataset title",
    "description": "TODO: dataset description",
    "license": "TODO: SPDX license",
    "repo": "TODO: GitHub repo URL",
    "source": {
        "provider": "TODO: provider",
        "homepage": "TODO: homepage URL",
        "dataset": "TODO: dataset URL",
    },
    "topics": [],
    "owners": [],
    # "frequency": "daily",
}


def main() -> None:
    producer_dir = Path(__file__).resolve().parent

    # TODO: replace with real data fetch/transform
    df = pd.DataFrame({"hello": ["world"]})
    publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)


if __name__ == "__main__":
    main()
"""
        content = content.replace("__DATASET_ID__", dataset_id)
        main_path.write_text(content, encoding="utf-8")

    readme_path = directory / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            """# Dataset

TODO: describe the dataset, sources, schema, and update schedule.
""",
            encoding="utf-8",
        )
