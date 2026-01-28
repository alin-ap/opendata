# 数据集契约（Schemas）

本文档定义 producer、存储 (R2/HTTP)、注册表和消费者之间的**数据契约**。

核心原则：

- `metadata.json` 是**单一事实来源**（single source of truth）。
- `index.json` 是**从 `metadata.json` 投影生成**的全局索引（用于发现/搜索）。

## 1) 标识符

### Dataset ID

- 格式：`namespace/name`
- 正则：`^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- 示例：
  - `getopendata/fred-unrate-monthly`
  - `alice/us-stock-daily`

Dataset ID 是规范的，用于派生存储 key。

## 2) 存储布局 (R2 keys)

所有对象必须位于可预测的前缀下：

```
datasets/<namespace>/<name>/data.parquet    # 数据文件
datasets/<namespace>/<name>/metadata.json   # 目录字段 + 统计 + schema + (可选 preview)
datasets/<namespace>/<name>/README.md       # 文档
```

说明：

| 文件 | 作用 |
|------|------|
| `data.parquet` | 数据集的实际数据 |
| `metadata.json` | 单一事实来源：目录字段 + 统计 + schema + (可选 preview) |
| `README.md` | 人类可读的文档 |

## 3) JSON 格式

### metadata.json

由 producer 发布时写入。

示例：

```json
{
  "dataset_id": "getopendata/fred-unrate-monthly",
  "updated_at": "2026-01-24T19:07:54+00:00",

  "title": "FRED UNRATE (Unemployment Rate)",
  "description": "US unemployment rate (monthly) from FRED.",
  "license": "unknown",
  "repo": "https://github.com/getopendata/getopendata",

  "source": {
    "provider": "fred",
    "homepage": "https://fred.stlouisfed.org/",
    "dataset": "https://fred.stlouisfed.org/series/UNRATE"
  },

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

字段约束：

必填：

- `dataset_id` (string)
- `updated_at` (string, ISO-8601)
- `title` (string)
- `description` (string)
- `license` (string)
- `repo` (string)
- `topics` (string[], 非空)
- `owners` (string[], 非空)
- `frequency` (string)
- `row_count` (int, >= 0)
- `data_size_bytes` (int, >= 0)
- `checksum_sha256` (string)
- `columns` (array of `{name,type}`)

选填：

- `source` (object)
- `geo` (object)
- `preview` (object)

关于 `source`：

- `source` 本身可省略。
- 若提供 `source`，其内部字段 `provider/homepage/dataset` 都是选填。
- 但只要出现，就必须是非空字符串（不能是空字符串/纯空白）。

关于 `preview`：

- `preview` 可省略（例如 `preview_rows<=0`）。
- 若提供，必须包含：
  - `generated_at` (ISO-8601)
  - `columns` (string[])
  - `rows` (object[])，且列值必须可 JSON 序列化

### index.json

全局注册表，用于发现/搜索，**从各数据集的 `metadata.json` 抽取字段汇总生成**。

示例：

```json
{
  "generated_at": "2026-01-24T19:08:09+00:00",
  "datasets": [
    {
      "id": "getopendata/fred-unrate-monthly",
      "title": "FRED UNRATE (Unemployment Rate)",
      "description": "US unemployment rate (monthly) from FRED.",
      "license": "unknown",
      "repo": "https://github.com/getopendata/getopendata",
      "source": {
        "provider": "fred",
        "homepage": "https://fred.stlouisfed.org/",
        "dataset": "https://fred.stlouisfed.org/series/UNRATE"
      },
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

注意：`index.json` 只应包含发现/列表页需要的字段；`columns/checksum/preview` 等大字段应留在 `metadata.json`。

## 4) Producer 目录字段（写在代码里）

Producer 在代码里定义 `CATALOG`（必须是字面量 dict，方便工具解析），并传给发布函数。

```python
from pathlib import Path
import pandas as pd

from opendata.producer import publish_dataframe_from_dir

CATALOG = {
    "id": "getopendata/treasury-yield-curve-daily",
    "title": "US Treasury Yield Curve (Daily)",
    "description": "Daily yield curve rates published by the U.S. Treasury.",
    "license": "Public Domain",
    "repo": "https://github.com/<org>/<repo>",
    "source": {
        "provider": "us_treasury",
        "homepage": "https://home.treasury.gov/",
        "dataset": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates",
    },
    "topics": ["rates", "macro"],
    "owners": ["alin"],
    "frequency": "daily",
}

producer_dir = Path(__file__).resolve().parent
df = pd.DataFrame(...)
publish_dataframe_from_dir(producer_dir, df=df, catalog=CATALOG)
```

`CATALOG` 的字段约束：

必填：

- `id` (string)
- `title` (string)
- `description` (string)
- `license` (string)
- `repo` (string)
- `topics` (string[], 非空)
- `owners` (string[], 非空)
- `frequency` (string)

选填：

- `source` (object，整体可省略；内部字段均选填)
- `geo` (object)

## 5) Producer 运行契约

若在单一仓库内维护多个 producer，建议放在：

```
producers/<namespace>/<slug>/
```

每个目录至少包含：

- `main.py`
- `README.md`

环境变量：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `OPENDATA_STORAGE` | 存储后端（`r2` / `http`；`memory` 用于测试） | 无（建议显式设置） |
| `OPENDATA_INDEX_URL` | 公共 registry URL；若 `OPENDATA_STORAGE` 未设置则自动启用 `http` | 无 |
| `OPENDATA_HTTP_BASE_URL` | HttpStorage base URL | 无 |
| `OPENDATA_PREVIEW_ROWS` | preview 行数（设为 0 关闭） | 100 |
