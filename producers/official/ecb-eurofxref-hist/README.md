# ECB Euro FX Reference Rates (History)

Source: ECB euro foreign exchange reference rates.

This producer downloads `eurofxref-hist.csv` and reshapes it into a long table.

Columns:

- `date` (UTC timestamp)
- `currency` (string, e.g. `USD`)
- `rate` (float, units: currency per 1 EUR)
