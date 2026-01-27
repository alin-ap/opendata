# 数据集契约

本文档定义 producer、存储 (R2)、注册表和消费者之间的**数据契约**。

## 1) 标识符

### Dataset ID

- 格式：`namespace/name`
- 正则：`^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- 示例：
  - `official/stooq-aapl-daily`
  - `official/fred-unrate-monthly`

Dataset ID 是规范的，用于派生存储 key。

## 2) 存储布局 (R2 keys)

所有对象必须位于可预测的前缀下：

```
datasets/<namespace>/<name>/data.parquet    # 数据文件
datasets/<namespace>/<name>/metadata.json   # 元数据（统计 + 列定义）
datasets/<namespace>/<name>/preview.json    # 预览数据（前 N 行）
datasets/<namespace>/<name>/README.md       # 文档
```

说明：

| 文件 | 作用 |
|------|------|
| `data.parquet` | 数据集的实际数据 |
| `metadata.json` | 统计信息 + 列定义（行数、大小、校验和、schema） |
| `preview.json` | 预计算的前 N 行，供 portal 展示 |
| `README.md` | 人类可读的文档 |

## 3) JSON 格式

### metadata.json

每个数据集的元数据文件，包含统计信息和列定义。producer 发布时写入。

```json
{
  "dataset_id": "official/fred-unrate-monthly",
  "updated_at": "2026-01-24T19:07:54+00:00",
  "data_key": "datasets/official/fred-unrate-monthly/data.parquet",
  "preview_key": "datasets/official/fred-unrate-monthly/preview.json",
  "metadata_key": "datasets/official/fred-unrate-monthly/metadata.json",
  "row_count": 936,
  "data_size_bytes": 12137,
  "checksum_sha256": "...",
  "format": "parquet",
  "columns": [
    {"name": "date", "type": "timestamp[ns, tz=UTC]"},
    {"name": "value", "type": "double"}
  ]
}
```

### preview.json

```json
{
  "dataset_id": "official/fred-unrate-monthly",
  "generated_at": "2026-01-24T19:07:54+00:00",
  "columns": ["date", "value", "series_id"],
  "rows": [
    {"date": "1948-01-01T00:00:00+00:00", "value": 3.4, "series_id": "UNRATE"}
  ]
}
```

规则：
- `rows` 必须是 JSON 对象数组
- 时间戳使用 ISO-8601 格式

### index.json

全局注册表，汇总所有数据集。**所有 producer 完成后统一重建**，避免并发写冲突。

```json
{
  "generated_at": "2026-01-24T19:08:09+00:00",
  "datasets": [
    {
      "id": "official/fred-unrate-monthly",
      "title": "FRED UNRATE (Unemployment Rate)",
      "description": "US unemployment rate (monthly) from FRED.",
      "license": "unknown",
      "source": "https://fred.stlouisfed.org/series/UNRATE",
      "repo": "https://github.com/getopendata/getopendata",
      "readme_key": "datasets/official/fred-unrate-monthly/README.md",
      "topics": ["macro", "fred", "unemployment"],
      "owners": ["alin"],
      "frequency": "monthly",
      "updated_at": "2026-01-24T19:07:54+00:00",
      "row_count": 936,
      "data_size_bytes": 12137
    }
  ]
}
```

## 4) Producer 契约

官方 producer 位于 `producers/official/<slug>/`，必须包含：

- `opendata.yaml`（元数据）
- `README.md`（文档）
- `main.py`（数据生成脚本）

运行契约：

```python
from pathlib import Path
import pandas as pd
from opendata.producer import publish_dataframe_from_dir

producer_dir = Path(__file__).resolve().parent
df = pd.DataFrame(...)
publish_dataframe_from_dir(producer_dir, df=df)
```

环境变量：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `OPENDATA_STORAGE` | 存储后端 (`local` / `r2`) | `local` |
| `OPENDATA_PREVIEW_ROWS` | preview 行数 | 100 |

## 5) 独立性原则

- 每个数据集只写入自己的 key 前缀
- 全局 `index.json` 在所有 producer 完成后统一重建（避免并发写）
