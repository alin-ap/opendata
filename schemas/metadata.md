# Dataset Metadata Schema

This document defines the structured dataset metadata format used by producer
repositories.

File name: `opendata.yaml`

## Example

```yaml
id: official/treasury-yield-curve-daily
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

## Fields

Required:
- `id` (string): dataset identifier.
  - Format: `namespace/name`
  - Regex: `^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
- `title` (string): short display name.
- `description` (string): 1-3 sentence description.
- `license` (string): SPDX identifier when possible (e.g. `MIT`, `Apache-2.0`).
- `repo` (string): GitHub repository URL containing the producer code.
- `source` (object): structured provenance.
  - `provider` (string, required): a stable provider identifier (e.g. `fred`, `ecb`).
  - `homepage` (string, optional): provider homepage URL.
  - `dataset` (string, optional): dataset page / API documentation / download URL.

Optional:

- `topics` (string[]): search/filter topics. Prefer short, lowercase tokens.
- `owners` (string[]): GitHub handles or org/team names.
- `frequency` (string): e.g. `hourly`, `daily`, `weekly`, `monthly`, `adhoc`.
- `geo` (object): geographic scope.
  - `scope` (string): one of `global`, `region`, `country`, `multi`.
  - `countries` (string[], optional): ISO 3166-1 alpha-2.
  - `regions` (string[], optional): UN M49 or project-specific region codes.

## Validation notes

- Unknown fields are allowed for forward compatibility, but should be namespaced
  and documented.
- Both SDK and registry should validate `id` and reject invalid dataset IDs.
