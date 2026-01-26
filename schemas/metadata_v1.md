# Dataset Metadata Schema (meta_version: 1)

NOTE: This schema is kept for historical reference. The current producer
metadata contract is `meta_version: 2` (see `schemas/metadata_v2.md`).

This document defines the minimal, human-authored dataset metadata format used by
producer repositories.

File name: `opendata.yaml`

## Example

```yaml
meta_version: 1
id: official/us-stock-daily
title: US Stock Daily
description: Daily OHLCV bars for US stocks.
license: MIT
source: https://example.com/source
repo: https://github.com/example/repo

tags: [stocks, us]
owners: [example]
frequency: daily
versioning: date
```

## Fields

Required:

- `meta_version` (int): must be `1`.
- `id` (string): dataset identifier.
  - Format: `namespace/name`
  - Regex: `^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- `title` (string): short display name.
- `description` (string): 1-3 sentence description.
- `license` (string): SPDX identifier when possible (e.g. `MIT`, `Apache-2.0`).
- `source` (string): upstream data source URL or human-readable provenance.
- `repo` (string): GitHub repository URL containing the producer code.

Optional:

- `tags` (string[]): search/filter tags (short, lowercase preferred).
- `owners` (string[]): GitHub handles or org/team names.
- `frequency` (string): e.g. `hourly`, `daily`, `weekly`, `adhoc`.
- `versioning` (string): version policy, e.g. `date` or `semver`.

## Validation notes

- Unknown fields are allowed for forward compatibility, but should be namespaced
  and documented.
- Both SDK and registry should validate `id` and reject invalid dataset IDs.
