# Agent Guide（getopendata）
当前状态：working MVP（Python SDK/CLI + producers + 静态 portal）。
- 文档：`opendata.md`（架构/决策）、`TODO.md`（backlog）、`schemas/*.md`（合同/Schema）

## 仓库结构（高信号）
- `src/opendata/`：Python SDK + CLI（命令 `od`）
- `tests/`：pytest 测试
- `producers/official/`：官方 producers（每个目录都有 `opendata.yaml`/`main.py`/`README.md`）
- `scripts/`：编排脚本（重点 `scripts/publish_official_local.py`）
- `portal/`：纯静态 portal（无 Node 构建链）
- `.github/workflows/`：CI / 定时发布

## Cursor/Copilot 规则
- 未发现 Cursor 规则（`.cursor/rules/` 或 `.cursorrules` 不存在）。
- 未发现 Copilot 规则（`.github/copilot-instructions.md` 不存在）。
- 如果后续添加规则，请把原文逐字复制到本节。

## Build / Lint / Test
- 优先用 `pyproject.toml` 定义的工具（ruff / mypy / pytest）。
- macOS 可能没有 `python`：用 `python3` 或 `.venv/bin/python`。

```bash
# 安装
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

# 可选：Cloudflare R2（S3 兼容）后端
pip install -e ".[r2]"

# 格式化 / Lint / 类型
ruff format .
ruff format --check .
ruff check .
ruff check . --fix
mypy src

# 测试
pytest
pytest -q

# 单测：跑单文件 / 单用例 / 关键词过滤
pytest tests/test_ids.py -q
pytest tests/test_publish_dataframe.py::test_publish_dataframe_writes_objects -q
pytest -k "registry_build" -q

# CLI 冒烟
od --help
od load official/owid-covid-global-daily --head 3
OPENDATA_INDEX_URL="https://<bucket>.r2.dev/index.json" od load official/owid-covid-global-daily --head 3

# 本地发布冒烟（写到本地 storage）
OPENDATA_STORAGE=local .venv/bin/python scripts/publish_official_local.py --version 2026-01-24
OPENDATA_STORAGE=local .venv/bin/python scripts/publish_official_local.py --only official/owid-covid-global-daily

# Portal 本地预览
python3 -m http.server 8000
# 打开 http://localhost:8000/portal/index.html
```

环境变量（SDK + scripts 共用）
- `OPENDATA_STORAGE`：`local|r2|http`（默认 `local`）
- `OPENDATA_LOCAL_STORAGE_DIR`：默认 `.opendata/storage`
- `OPENDATA_HTTP_BASE_URL`：`HttpStorage` 的 base URL（例 `https://<bucket>.r2.dev/`）
- `OPENDATA_INDEX_URL`：若设置且未显式设置 `OPENDATA_STORAGE`，则自动启用 HTTP storage
- Producer 运行期：`OPENDATA_VERSION`、`OPENDATA_PREVIEW_ROWS`

## Producers（数据生产者）
- 位置：`producers/official/<slug>/`。
- 每个 producer 必须包含：`opendata.yaml`、`main.py`、`README.md`。
- `opendata.yaml` 的 `id`（dataset id）属于公共 API；必须合法且唯一。
- producer 运行期版本：优先读 `OPENDATA_VERSION`（Actions/脚本会设置）。
- 推荐发布方式（不要手写 key）：
  - `from opendata.producer import publish_dataframe_from_dir`
  - `publish_dataframe_from_dir(Path(__file__).resolve().parent, df=df)`
- 预览行数：可用 `OPENDATA_PREVIEW_ROWS` 或函数参数覆盖。
- 编排脚本：`scripts/publish_official_local.py` 会逐个运行 producer，并在最后 rebuild `index.json`。
- 脚本支持 `--ignore-failures`：允许部分 producer 失败但整体流程继续（用于 CI 稳定性）。

## Storage / Registry
- StorageBackend 由 `src/opendata/storage/storage_from_env()` 决定（local/r2/http）。
- 设置 `OPENDATA_INDEX_URL` 且未设置 `OPENDATA_STORAGE` 时会自动使用 HTTP storage（用于公开 bucket 读取）。
- `index.json` 是全局 registry；避免并发/增量写导致竞态，优先“全部 producer 结束后一次性重建”。
- 任何对象 key 都应来自 `src/opendata/ids.py`（可审计、可预测、可测试）。

## 代码风格 / 约定
通用原则
- 目标：可审计、可复现；优先“简单、无惊喜”的实现。
- 绝不提交 secrets；`.env` 已被忽略（用 `.env.example` 作为模板）。
- 公开接口要稳定：dataset id、对象 key 布局、`od` CLI flags。
- 默认使用 ASCII；本仓库文档/注释允许中文（请尽量用中文写注释/文档）。
- 请称呼我为 Alin。

格式化 / Import
- 统一用 `ruff format`；`line-length=100`（见 `pyproject.toml`）。
- imports 顺序：stdlib -> third-party -> first-party（`opendata`）；禁止 `from x import *`。
- `src/opendata/__init__.py` 保持轻量，避免 import 时加载重依赖。

类型系统（Python 3.9+）
- 每个函数都要标注类型（mypy: `disallow_untyped_defs=true`）。
- 避免 `Any`；优先 `object` + narrowing / `TypedDict` / `dataclass`。
- Python 3.9 不支持 PEP604（`T | U`），请用 `Optional[T]` / `Union[T, U]`。

命名
- 函数/变量：`snake_case`；类：`PascalCase`。
- 变量名尽量“显式”：`dataset_id`、`version`、`data_key`、`schema_hash_sha256`。
- dataset id 属于 public API；必须用 `opendata.ids.validate_dataset_id()` 校验。

Dataset contract / 对象 key
- 永远不要手写 key；用 `src/opendata/ids.py` 里的 helper。
- 稳定对象布局：
  - `datasets/<namespace>/<name>/<version>/data.parquet`
  - `datasets/<namespace>/<name>/<version>/schema.json`
  - `datasets/<namespace>/<name>/<version>/preview.json`
  - `datasets/<namespace>/<name>/latest.json`
  - `datasets/<namespace>/<name>/README.md`

CLI / 公共接口
- CLI 入口：`src/opendata/cli.py`，命令名 `od`（见 `pyproject.toml`）。
- CLI 报错：库抛 `OpendataError`，CLI 捕获后退出码为 2，并打印简洁错误信息。
- 任何会影响公开行为的改动（dataset id 规则、key 布局、flag 语义）都要非常谨慎。

错误处理
- 库代码统一抛 `OpendataError` 子类（见 `src/opendata/errors.py`）。
- 错误信息包含上下文（`dataset_id`/`version`/`url`），但不要包含 secrets/签名。
- 捕获尽量窄；需要包装时用 `raise ... from e`。

安全
- 不要提交任何密钥/凭证；`.env` 只用于本地开发（已被 gitignore）。
- 不要在日志中输出签名 URL、Authorization header、Access Key。
- 读取远程数据/JSON 时按“不可信输入”处理（长度、类型、字段存在性）。

网络 / I/O / 测试
- 所有 HTTP（`requests`）必须设置 timeout；大文件用 streaming。
- 单元测试默认不得访问网络；需要集成测试时请新增显式标记。
- 测试优先用 `tmp_path` + `LocalStorage`，避免依赖真实 bucket。

Git / CI
- 保持工作区干净：不要提交 `.opendata/`、`.venv/`、`*.egg-info/`、缓存目录。
- GitHub Actions 里尽量避免单点失败导致全绿变红：producer 批处理可容错，但要明确记录失败。
- 依赖尽量少且稳定；核心 SDK 避免引入重依赖（`__init__.py` 不要触发重 import）。

Portal / 文档
- `portal/` 是纯静态目录（无 npm）；JS 不引入依赖；解析远程 JSON 时防御性处理。
- 架构/合同变更同步更新：`opendata.md`、`schemas/*.md`；里程碑变更同步更新 `TODO.md`。
