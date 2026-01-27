# 数据集契约（Schemas）

本文档定义 producer、存储 (R2/HTTP)、注册表和消费者之间的**数据契约**。

## 1) 标识符

### Dataset ID

- 格式：`namespace/name`
- 正则：`^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- 示例：
  - `getopendata/stooq-aapl-daily`
  - `getopendata/fred-unrate-monthly`

Dataset ID 是规范的，用于派生存储 key。

## 2) 存储布局 (R2 keys)

所有对象必须位于可预测的前缀下：

```
datasets/<namespace>/<name>/data.parquet    # 数据文件
datasets/<namespace>/<name>/metadata.json   # 元数据（统计 + 列定义）
datasets/<namespace>/<name>/README.md       # 文档
```

说明：

| 文件 | 作用 |
|------|------|
| `data.parquet` | 数据集的实际数据 |
| `metadata.json` | 统计信息 + 列定义（行数、大小、校验和、schema） |
| `README.md` | 人类可读的文档 |

## 3) JSON 格式

### metadata.json

每个数据集的元数据文件，包含统计信息和列定义。producer 发布时写入。

```json
{
  "dataset_id": "getopendata/fred-unrate-monthly",
  "updated_at": "2026-01-24T19:07:54+00:00",
  "data_key": "datasets/getopendata/fred-unrate-monthly/data.parquet",
  "metadata_key": "datasets/getopendata/fred-unrate-monthly/metadata.json",
  "row_count": 936,
  "data_size_bytes": 12137,
  "checksum_sha256": "...",
  "format": "parquet",
  "columns": [
    {"name": "date", "type": "timestamp[ns, tz=UTC]"},
    {"name": "value", "type": "double"}
  ],
  "preview": {
    "generated_at": "2026-01-24T19:07:54+00:00",
    "columns": ["date", "value", "series_id"],
    "rows": [
      {"date": "1948-01-01T00:00:00+00:00", "value": 3.4, "series_id": "UNRATE"}
    ]
  }
}
```

### index.json

全局注册表，汇总所有数据集。**所有 producer 完成后统一重建**，避免并发写冲突。

```json
{
  "generated_at": "2026-01-24T19:08:09+00:00",
  "datasets": [
    {
      "id": "getopendata/fred-unrate-monthly",
      "title": "FRED UNRATE (Unemployment Rate)",
      "description": "US unemployment rate (monthly) from FRED.",
      "license": "unknown",
      "source": {
        "provider": "fred",
        "homepage": "https://fred.stlouisfed.org/",
        "dataset": "https://fred.stlouisfed.org/series/UNRATE"
      },
      "repo": "https://github.com/getopendata/getopendata",
      "readme_key": "datasets/getopendata/fred-unrate-monthly/README.md",
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

## 4) Producer 元数据（opendata.yaml）

文件名：`opendata.yaml`（人类可编辑，提交到 repo；用于 registry 索引和发现）。

示例：

```yaml
id: getopendata/treasury-yield-curve-daily
title: US Treasury Yield Curve (Daily)
description: Daily yield curve rates published by the U.S. Treasury.
license: Public Domain
repo: https://github.com/<org>/<repo>

source:
  provider: us_treasury
  homepage: https://home.treasury.gov/
  dataset: https://home.treasury.gov/resource-center/data-chart-center/interest-rates

topics: [rates, macro]
geo:
  scope: country
  countries: [US]

owners: [alin]
frequency: daily
```
