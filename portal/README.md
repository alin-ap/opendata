# OpenData Portal

This is a static, zero-build portal that reads the registry `index.json` from a public
bucket (Cloudflare R2 recommended).

## Usage

1. Open the site.
2. Provide the public URL to `index.json` (example: `https://<bucket>.r2.dev/index.json`).
3. Search datasets, open details, view README / schema / preview (if embedded).

You can provide the index URL via the `?index=` query parameter, or by editing `portal/config.js`.

## R2 public read + CORS

To make the portal work in the browser, configure your bucket for public read and set CORS
to allow the portal origin to read objects like:

- `index.json`
- `datasets/*/data.parquet`
- `datasets/*/metadata.json`
- `datasets/*/README.md`

Minimum CORS for a public demo:

```
Allowed methods: GET, HEAD, OPTIONS
Allowed origins: *
Allowed headers: *
Expose headers: *
Max age: 86400
```
