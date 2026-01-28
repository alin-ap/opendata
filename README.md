# getopendata

docs-first 的 OpenData Registry MVP：把 "producer repo" 里的数据产物发布到可索引的对象存储（R2/HTTP），并通过 Python SDK/CLI + 纯静态 portal 进行发现与消费。

- Producer: Python `main.py` 定时抓取/生成数据
- Storage: Cloudflare R2 / HTTP（对象 key 稳定、可预测）
- Registry: `index.json`（数据集列表 + 元数据）
- Consumer: `od load <dataset_id>` / `import opendata as od; od.load(...)`
- Portal: 静态站点读取 `index.json`，支持搜索/详情/README/schema/preview

相关文档：

- `schemas.md`（对象布局 + metadata.json / catalog 合同）

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

## 发布 producers 到 R2

如果在本仓库维护 producers（例如 `producers/<namespace>/<slug>/`），可用脚本批量发布。
本地手动跑（需要 R2 凭证；会直接写入 R2，不会落盘缓存 parquet）：

```bash
source .venv/bin/activate
pip install -e ".[r2]"

export OPENDATA_STORAGE=r2
export OPENDATA_R2_ENDPOINT_URL=...
export OPENDATA_R2_BUCKET=...
export OPENDATA_R2_ACCESS_KEY_ID=...
export OPENDATA_R2_SECRET_ACCESS_KEY=...

python3 scripts/publish_producers_local.py --root producers --ignore-failures
```

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
OPENDATA_INDEX_URL="https://<bucket>.r2.dev/index.json" \
  od load getopendata/owid-covid-global-daily --head 3
```

Python：

```python
import opendata as od

# Configure storage via env vars (e.g. OPENDATA_INDEX_URL / OPENDATA_STORAGE=r2)
df = od.load("getopendata/owid-covid-global-daily")
print(df.head())
```

## Producer 合同（`main.py` + README）

一个 producer repo / producer 目录的最小文件集：

- `main.py`（生成/抓取数据并发布；内含 `CATALOG`）
- `README.md`（数据集说明）

推荐通过脚手架生成：

```bash
od init getopendata/example-dataset --dir ./my-producer
cd my-producer
```

如在本仓库维护 producers，建议放在：`producers/<namespace>/<slug>/`。

## Registry（`index.json`）

`index.json` 是全局 registry（portal 依赖它做发现）。由各数据集的 `metadata.json` 提取/汇总字段生成。

## Storage 配置

SDK/脚本通过环境变量选择 storage（本项目不支持本地目录作为 storage backend，也不会落盘缓存 parquet）：

- `OPENDATA_STORAGE=r2|http`（可选 `memory` 仅用于测试）

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
- `datasets/<namespace>/<name>/metadata.json`
- `datasets/<namespace>/<name>/README.md`
- `index.json`

## 发布到 R2（GitHub Actions）

生产者 repo 可通过 `od deploy` 生成 GitHub Actions workflow 并定时发布到 R2。
