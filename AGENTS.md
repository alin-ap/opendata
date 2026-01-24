# Agent Guide (getopendata)

Status: docs-first. Source of truth: `opendata.md`. Backlog: `TODO.md`.
No code or build system is checked in yet; when bootstrapping, keep this file updated.

## Cursor/Copilot rules

- No Cursor rules found (`.cursor/rules/` or `.cursorrules` not present).
- No Copilot instructions found (`.github/copilot-instructions.md` not present).
- If rules are added later, copy them into this section verbatim.

## Build / Lint / Test

### Always do command discovery first

1. Look for `Makefile`, `justfile`, `pyproject.toml`, `package.json`, `wrangler.toml`.
2. If present, use the commands/scripts defined there (do not invent new ones).
3. If absent (current state), use the baselines below and standardize later.

### Python SDK/CLI baseline (expected: `opendata` package, `od` CLI)

```bash
# Setup (pick one)
python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -e ".[dev]"
# or: uv venv && uv sync --all-extras

# Optional: R2 support
pip install -e ".[r2]"  # boto3-based S3-compatible backend

# Format / lint / types (pick tools and enforce via CI)
ruff format .        # or: black .
ruff check .         # or: python -m flake8
mypy src             # keep mypy focused on library code

# Tests
pytest
pytest tests/test_ids.py
pytest tests/test_metadata_registry.py::test_registry_register_and_refresh
pytest -k "presign"
```

### JS/TS baseline (Workers / Portal)

```bash
npm ci
npm run build
npm run lint
npm run format
npm test

# Single test (depends on runner; check package.json)
npx vitest run path/to/test.ts -t "case name"
npx jest path/to/test.ts -t "case name"

# Workers dev (if using Wrangler)
npx wrangler dev
```

## Code style

### General principles

- Optimize for auditability and reproducibility; prefer simple, boring code.
- Do not commit secrets; prefer short-lived credentials (pre-signed URLs, OIDC minting).
- Keep public interfaces stable: dataset IDs, `od.load()`, version semantics.
- Default to ASCII unless a file already uses non-ASCII.
- 尽量用中文来注释和写文档
- 请称呼我为Alin

### Repo layout (when code is added)

- Prefer a clear split by component (e.g. `python/`, `workers/`, `web/`), each with its own config.
- Keep generated artifacts out of git (`dist/`, `.venv/`, `node_modules/`, `__pycache__/`).

### Naming & conventions

- Dataset ID: `namespace/name` (lowercase, `-` allowed, no spaces).
- Versioning: pick one convention per dataset (date, semver) and document it in metadata.
- Prefer explicit names: `dataset_id`, `r2_key_prefix`, `presigned_url`, `last_updated_at`.

### Data publishing conventions

- R2 keys must be predictable and versioned; avoid renames after publishing.
- Recommended object layout:
  - `datasets/<namespace>/<name>/<version>/data.parquet`
  - `datasets/<namespace>/<name>/<version>/schema.json`
  - `datasets/<namespace>/<name>/latest.json`
- Publish minimal stats with each version: row count, schema hash, min/max date (if applicable), checksum.

### Registry / signing conventions (when implemented)

- Validate dataset identifiers server-side. Recommended regexes:
  - dataset id: `^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$`
  - version: `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` (no slashes)
- Never accept raw R2 keys/paths from clients; resolve `dataset_id + version` to a known key, then sign that.
- Pre-signed URLs: keep expiries short (5-15 min); do not log full signed URLs; avoid open redirects.
- For uploads, prefer PUT to a versioned key; update `latest.json` as a separate, explicit step.

### Logging / observability

- Prefer structured logging with stable keys (`dataset_id`, `version`, `request_id`).
- Redact tokens, API keys, and signatures; avoid logging request headers by default.
- Emit enough context to debug CI failures without leaking secrets.

### Performance / caching

- Prefer local caching for downloads (e.g. `~/.cache/opendata/`) with optional checksum validation.
- Precompute preview/stats during publish so portal/worker paths stay fast.

### Dependency policy

- Minimize dependencies in the core SDK; prefer stdlib over heavy frameworks.
- Pin versions for reproducibility; avoid floating git deps and unpinned GitHub Actions.

### Python

- Target Python 3.9+ (can raise once CI/tooling is standardized).
- Type hints on all public APIs; prefer `from __future__ import annotations`.
- Prefer `pathlib.Path`; avoid new `os.path` usage.
- Use `dataclasses` for simple records; adopt `pydantic` only for validation/schema evolution needs.
- Imports: stdlib -> third-party -> local; no wildcard imports; keep `__init__.py` light.
- Errors:
  - Define `OpendataError` as the base exception plus narrow domain subclasses.
  - Include context (`dataset_id`, `version`, host) but never secrets/tokens.
  - Avoid bare `except:`; catch specific exceptions and re-raise with context.
- Networking and I/O:
  - Always set timeouts.
  - Add retries with exponential backoff for idempotent operations.
  - Stream large Parquet uploads/downloads; avoid loading entire files into memory.

### TypeScript / Cloudflare Workers

- Use TypeScript with `strict`; avoid `any` (use `unknown` + narrowing).
- Workers runtime: do not use Node-only APIs; use Web APIs (`fetch`, `crypto.subtle`, Streams).
- Treat `env` and request params as untrusted; validate before access/signing.
- API keys: use constant-time compare; never log raw keys.

### GitHub Actions / CI (when added)

- Use least-privilege permissions; prefer `permissions: {contents: read}` by default.
- Pin action versions; avoid unpinned `@master`.
- Avoid printing secrets; scrub logs; do not echo signed URLs.
- Prefer OIDC to mint short-lived upload credentials over long-lived R2 keys.

### Formatting

- Use formatters; do not hand-format to satisfy lint.
- Prefer ruff/black (Python) and prettier (TS). Keep line length consistent (Python 88/100).

### Testing

- Unit tests should not hit the network; mock HTTP by default.
- Keep integration tests behind an explicit marker/flag (e.g. `pytest -m integration`).
- Security-sensitive areas (signing/auth): test invalid inputs, expiry handling, path traversal prevention.

### Docs

- `opendata.md` is the architecture source of truth; update it when decisions change.
- `TODO.md` is the backlog; keep it current when milestones move.
