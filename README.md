# getopendata

docs-first 的 OpenData Registry MVP：把 "producer repo" 里的数据产物发布到可索引的对象存储（local/R2/HTTP），并通过 Python SDK/CLI + 纯静态 portal 进行发现与消费。

- Producer: Python `main.py` 定时抓取/生成数据
- Storage: Cloudflare R2 / 本地目录 / HTTP（对象 key 稳定、可预测）
- Registry: `index.json`（数据集列表 + 元数据 + latest stats）
- Consumer: `od load <dataset_id>` / `import opendata as od; od.load(...)`
- Portal: 静态站点读取 `index.json`，支持搜索/详情/README/schema/preview

相关文档：

- `schemas/dataset_contract.md`（对象布局/产物合同）
- `schemas/metadata.md`（`opendata.yaml` 元数据合同）

## 快速开始（本地开发）

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -e ".[dev]"

ruff format --check .
ruff check .
mypy src
pytest
```

## 运行官方 producers（写入本地 storage）

默认本地 storage 目录：`.opendata/storage/`。

```bash
source .venv/bin/activate
OPENDATA_STORAGE=local \
  python3 scripts/publish_official_local.py
```

产物：

- `.opendata/storage/index.json`
- `.opendata/storage/datasets/<namespace>/<name>/...`

## Portal 预览（本地）

Portal 是纯静态文件（无构建链）。推荐用 HTTP 预览：

```bash
python3 -m http.server 8000
```

打开：`http://localhost:8000/portal/index.html`

Portal 会自动尝试从 `../index.json` 读取 registry（即同一个 bucket/目录下）。

如果 `index.json` 不在同源位置，可以通过 query 参数指定：

`http://localhost:8000/portal/index.html?index=<urlencoded_index_json_url>`

## 使用 SDK / CLI

CLI（`od`）：

```bash
od --help
od load official/owid-covid-global-daily --head 3
od load official/owid-covid-global-daily --download-only
```

Python：

```python
import opendata as od

df = od.load("official/owid-covid-global-daily")
print(df.head())
```

## Producer 合同（`opendata.yaml` + `main.py`）

一个 producer repo / producer 目录的最小文件集：

- `opendata.yaml`（元数据）
- `main.py`（生成/抓取数据并发布）
- `README.md`（数据集说明）

推荐通过脚手架生成：

```bash
od init official/example-dataset --dir ./my-producer
cd my-producer
od validate --meta opendata.yaml
```

官方 producer 放在：`producers/official/<slug>/`。

## Registry（`index.json`）

`index.json` 是全局 registry（portal 依赖它做发现）。避免并发/增量写导致竞态：推荐在批处理结束后一次性重建。

本地 rebuild 官方 registry：

```bash
OPENDATA_STORAGE=local \
  python3 scripts/publish_official_local.py
```

## Storage 配置

SDK/脚本通过环境变量选择 storage：

- `OPENDATA_STORAGE=local|r2|http`（默认 `local`）
- `OPENDATA_LOCAL_STORAGE_DIR`（默认 `.opendata/storage`）

HTTP 只读（从公开 bucket 读取）：

- `OPENDATA_INDEX_URL=https://<bucket>.r2.dev/index.json`（若设置且未显式设置 `OPENDATA_STORAGE`，会自动启用 HTTP storage）

Cloudflare R2（S3 兼容）：

```bash
pip install -e ".[r2]"

export OPENDATA_STORAGE=r2
export OPENDATA_R2_ENDPOINT_URL=...
export OPENDATA_R2_BUCKET=...
export OPENDATA_R2_ACCESS_KEY_ID=...
export OPENDATA_R2_SECRET_ACCESS_KEY=...
```

## 约定（Dataset Contract）

不要手写对象 key：统一用 `src/opendata/ids.py`。

稳定对象布局（v1）：

- `datasets/<namespace>/<name>/data.parquet`
- `datasets/<namespace>/<name>/schema.json`
- `datasets/<namespace>/<name>/preview.json`
- `datasets/<namespace>/<name>/stats.json`
- `datasets/<namespace>/<name>/README.md`

## 发布到 R2（GitHub Actions）

官方 producers 的定时发布 workflow：`.github/workflows/publish_official.yml`
