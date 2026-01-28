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
datasets/<namespace>/<name>/metadata.json   # 统计 + schema + 目录字段（可选 preview）
datasets/<namespace>/<name>/README.md       # 文档
```

说明：

| 文件 | 作用 |
|------|------|
| `data.parquet` | 数据集的实际数据 |
| `metadata.json` | 统计信息 + 列定义 + 目录字段（可选 preview） |
| `README.md` | 人类可读的文档 |

## 3) JSON 格式

### metadata.json

**单一事实来源**。由 producer 发布时写入。

```json
{
  "dataset_id": "getopendata/fred-unrate-monthly",
  "updated_at": "2026-01-24T19:07:54+00:00",
  "title": "FRED UNRATE (Unemployment Rate)",
  "description": "US unemployment rate (monthly) from FRED.",
  "license": "unknown",
  "source": {
    "provider": "fred",
    "homepage": "https://fred.stlouisfed.org/",
    "dataset": "https://fred.stlouisfed.org/series/UNRATE"
  },
  "repo": "https://github.com/getopendata/getopendata",
  "topics": ["macro", "fred", "unemployment"],
  "owners": ["alin"],
  "frequency": "monthly",
  "row_count": 936,
  "data_size_bytes": 12137,
  "checksum_sha256": "...",
  "columns": [
    {"name": "date", "type": "timestamp[ns, tz=UTC]"},
    {"name": "value", "type": "double"}
  ],
  "preview": {
    "generated_at": "2026-01-24T19:07:54+00:00",
    "columns": ["date", "value", "series_id"],
    "rows": [
      {"date": "1948-01-01T00:00:00+00:00", "value": 3.4, "series_id": "UNRATE"},
      {"date": "1948-02-01T00:00:00+00:00", "value": 3.5, "series_id": "UNRATE"}
    ]
  }
}
```


```

### index.json

全局注册表，**从各数据集的 `metadata.json` 抽取字段汇总生成**。

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
      "topics": ["macro", "fred", "unemployment"],
      "owners": ["alin"],
      "frequency": "monthly",
      "updated_at": "2026-01-24T19:07:54+00:00",
      "row_count": 936,
      "data_size_bytes": 12137
    },
    {
      "id": "getopendata/fred-xx-monthly",
      "title": "FRED XX (Example)",
      "description": "US xx rate (monthly) from FRED.",
      "license": "unknown",
      "source": {
        "provider": "fred",
        "homepage": "https://fred.stlouisfed.org/",
        "dataset": "https://fred.stlouisfed.org/series/XXXX"
      },
      "repo": "https://github.com/getopendata/getopendata",
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

