# getopendata

一个 docs-first 的 OpenData Registry MVP：

- Producer：用 Python 写 `main.py`，通过 GitHub Actions 定时抓取/生成数据
- Storage：发布到 Cloudflare R2（对象 key 可预测、可索引）
- Consumer：`od load <dataset_id>` 直接拿到 DataFrame
- Portal：静态站点读取 `index.json`，可搜索/查看 README/schema/preview

## 快速开始（本地）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

pytest
ruff check .
ruff format --check .
mypy src
```

## 运行官方 producers（本地 storage）

默认使用本地 storage（写入 `.opendata/storage/`）：

```bash
source .venv/bin/activate
OPENDATA_STORAGE=local \
  python scripts/publish_official_local.py --version 2026-01-24
```

运行完成后会生成：

- `.opendata/storage/index.json`
- `.opendata/storage/datasets/<namespace>/<name>/...`

## 预览 Portal（本地）

Portal 是纯静态文件，直接开 `portal/index.html` 也可；如果你想走 HTTP：

```bash
python3 -m http.server 8000
```

然后访问：`http://localhost:8000/portal/index.html`

## 发布到 R2（需要环境变量）

SDK/脚本通过环境变量选择 storage：

- `OPENDATA_STORAGE=r2`
- `OPENDATA_R2_ENDPOINT_URL=...`
- `OPENDATA_R2_BUCKET=...`
- `OPENDATA_R2_ACCESS_KEY_ID=...`
- `OPENDATA_R2_SECRET_ACCESS_KEY=...`

GitHub Actions 已内置工作流：`.github/workflows/publish_official.yml`

## 约定（Dataset Contract v1）

详情见：`schemas/dataset_contract_v1.md`、`schemas/metadata_v2.md`

推荐对象布局：

- `datasets/<namespace>/<name>/<version>/data.parquet`
- `datasets/<namespace>/<name>/<version>/schema.json`
- `datasets/<namespace>/<name>/<version>/preview.json`
- `datasets/<namespace>/<name>/latest.json`
- `datasets/<namespace>/<name>/README.md`
