from __future__ import annotations

from pathlib import Path

from .metadata import load_metadata


def render_github_actions_workflow(*, dataset_id: str, cron: str, python_version: str) -> str:
    # Keep this as a plain string template so producer repos don't need extra deps.
    return (
        "name: opendata\n"
        "\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "  schedule:\n"
        f"    - cron: '{cron}'\n"
        "\n"
        "jobs:\n"
        "  publish:\n"
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v4\n"
        "\n"
        "      - name: Setup Python\n"
        "        uses: actions/setup-python@v5\n"
        "        with:\n"
        f"          python-version: '{python_version}'\n"
        "\n"
        "      - name: Install dependencies\n"
        "        run: |\n"
        "          python -m pip install -U pip\n"
        "          python -m pip install 'opendata[r2]' pandas pyarrow\n"
        "\n"
        "      - name: Run producer\n"
        "        run: |\n"
        "          python main.py\n"
        "\n"
        "      - name: Publish dataset\n"
        "        env:\n"
        "          OPENDATA_STORAGE: r2\n"
        "          OPENDATA_R2_ENDPOINT_URL: ${{ secrets.OPENDATA_R2_ENDPOINT_URL }}\n"
        "          OPENDATA_R2_BUCKET: ${{ secrets.OPENDATA_R2_BUCKET }}\n"
        "          OPENDATA_R2_ACCESS_KEY_ID: ${{ secrets.OPENDATA_R2_ACCESS_KEY_ID }}\n"
        "          OPENDATA_R2_SECRET_ACCESS_KEY: ${{ secrets.OPENDATA_R2_SECRET_ACCESS_KEY }}\n"
        "        run: |\n"
        "          VERSION=$(date -u +%Y-%m-%d)\n"
        f'          od push {dataset_id} out/data.parquet --version "$VERSION"\n'
    )


def write_github_actions_workflow(
    *,
    repo_dir: Path,
    dataset_id: str,
    cron: str = "0 0 * * *",
    python_version: str = "3.11",
    workflow_name: str = "opendata.yml",
) -> Path:
    workflow_dir = repo_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    path = workflow_dir / workflow_name
    path.write_text(
        render_github_actions_workflow(
            dataset_id=dataset_id, cron=cron, python_version=python_version
        ),
        encoding="utf-8",
    )
    return path


def deploy_from_metadata(
    *,
    repo_dir: Path,
    meta_path: Path,
    cron: str = "0 0 * * *",
    python_version: str = "3.11",
) -> Path:
    meta = load_metadata(meta_path)
    return write_github_actions_workflow(
        repo_dir=repo_dir, dataset_id=meta.id, cron=cron, python_version=python_version
    )
