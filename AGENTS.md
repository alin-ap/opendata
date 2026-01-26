# Repository Guidelines (getopendata)

感谢尊敬的 AI 大人帮我写代码，我的名字是：Alin.Expects(Strict_Compliance, Elegant_Code)。

当前状态：working MVP（Python SDK/CLI + producers + 静态 portal）。

## Strict_Compliance (严格遵从)

- **零废话**：只输出必要的代码/命令/极简解释；禁止客套话或道德说教。
- **事实为本**：以 repo 代码、测试、可复现步骤为准；不确定先查（Read/Grep/跑测试），不要猜。
- **深度分析**：立足第一性原理拆解问题，优先用最小可验证的方式快速验证。
- **变更可审计**：任何影响 public API 的改动（dataset_id、key layout、CLI flags）必须显式说明。
- **反思记录**：出现失误（误改文件/偏离需求/漏跑工具）需记录到本文末尾，写清原因与避免复发的做法。

## Elegant_Code (优雅代码)

KISS 原则：崇尚简洁。不要过度设计模式。不要过度抽象。不要过度防御设计。

- 目标：可审计、可复现；优先“简单、无惊喜”的实现。
- 依赖克制：SDK 核心尽量不引入重依赖；`src/opendata/__init__.py` 保持轻量。
- 类型系统：mypy 严格（`disallow_untyped_defs=true`）；Python 3.9+；避免 `Any`。
- 兼容性：Python 3.9 不支持 PEP604（`T | U`），用 `Optional[T]` / `Union[T, U]`。

## 项目结构

```
src/opendata/            # Python SDK + CLI（命令 od）
src/opendata/storage/    # StorageBackend: local / r2 / http
tests/                   # pytest 单测
producers/official/      # 官方 producers（每个目录都有 opendata.yaml/main.py/README.md）
scripts/                 # 编排脚本（重点 scripts/publish_official_local.py）
portal/                  # 纯静态 portal（无 Node 构建链）
schemas/                 # 合同/Schema 文档
.github/workflows/       # CI / 定时发布
```

文档（高信号）：

- `README.md`
- `opendata_todo.md`（规划/里程碑）
- `schemas/dataset_contract_v1.md`
- `schemas/metadata_v2.md`

## Cursor/Copilot 规则

- 未发现 Cursor 规则（`.cursor/rules/` 或 `.cursorrules` 不存在）。
- 未发现 Copilot 规则（`.github/copilot-instructions.md` 不存在）。
- 如果后续添加规则，请把原文逐字复制到本节。

## 配置与环境

- Python: `>=3.9`（见 `pyproject.toml`）
- 虚拟环境：建议使用 `.venv/`；macOS 可能没有 `python`，用 `python3` 或 `.venv/bin/python`。
- 本地 storage 默认目录：`.opendata/storage/`（不要提交到 git）
- 本地 cache 默认目录：`~/.cache/opendata/`（可用 `OPENDATA_CACHE_DIR` 覆盖）

## 环境变量（SDK + scripts 共用）

- `OPENDATA_STORAGE`：`local|r2|http`（默认 `local`）
- `OPENDATA_LOCAL_STORAGE_DIR`：默认 `.opendata/storage`
- `OPENDATA_HTTP_BASE_URL`：`HttpStorage` 的 base URL（例 `https://<bucket>.r2.dev/`）
- `OPENDATA_INDEX_URL`：若设置且未显式设置 `OPENDATA_STORAGE`，则自动启用 HTTP storage
- Producer 运行期：`OPENDATA_VERSION`、`OPENDATA_PREVIEW_ROWS`

R2（S3 兼容）环境变量：

- `OPENDATA_R2_ENDPOINT_URL`
- `OPENDATA_R2_BUCKET`
- `OPENDATA_R2_ACCESS_KEY_ID`
- `OPENDATA_R2_SECRET_ACCESS_KEY`
- `OPENDATA_R2_REGION`（可选，默认 `auto`）

## 常用命令

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

## 代码风格

- 统一用 `ruff format`（`line-length=100`，见 `pyproject.toml`）。
- imports 顺序：stdlib -> third-party -> first-party（`opendata`）；禁止 `from x import *`。
- 类型注解：每个函数都要标注类型（mypy: `disallow_untyped_defs=true`）。
- 错误处理：库代码统一抛 `OpendataError` 子类（见 `src/opendata/errors.py`）；CLI 捕获后退出码为 2。

Dataset contract / 对象 key：

- 永远不要手写 key；用 `src/opendata/ids.py` 里的 helper。
- 稳定对象布局（v1）：
  - `datasets/<namespace>/<name>/<version>/data.parquet`
  - `datasets/<namespace>/<name>/<version>/schema.json`
  - `datasets/<namespace>/<name>/<version>/preview.json`
  - `datasets/<namespace>/<name>/latest.json`
  - `datasets/<namespace>/<name>/README.md`

## 测试与数据

- 单元测试默认不得访问网络；需要集成测试时请新增显式标记。
- 测试优先用 `tmp_path` + `LocalStorage`，避免依赖真实 bucket。
- 大文件/缓存目录不要提交：`.opendata/`、`.venv/`、`*.egg-info/`、`.pytest_cache/`、`.ruff_cache/`。

## 行为准则 (Dos & Don'ts)

### Don'ts (不要)

1. **不要** 手写对象 key；统一使用 `src/opendata/ids.py`。
2. **不要** 随意改动 dataset_id/version 规则或 key layout；它们是 public API。
3. **不要** 在单测里访问网络或真实 bucket；默认用 `LocalStorage`。
4. **不要** 使用 `requests` 时省略 timeout；大文件下载必须 streaming。
5. **不要** 在代码/日志/提交中输出敏感信息（`.env`、API key、Access Key、签名 URL、Authorization header）。
6. **不要** 在 producers 运行过程中并发/增量写 `index.json`；应在批处理结束后一次性重建。
7. **不要** 给 `portal/` 引入构建链或第三方依赖；保持 zero-build。
8. **不要** 让 `src/opendata/__init__.py` 触发重 import 或任何 I/O。

### Dos (要)

1. **要** 做较大改动后至少跑一遍：`ruff format --check .`、`ruff check .`、`mypy src`、`pytest`。
2. **要** 使用 `python3` + `.venv`；R2 相关功能需安装 `pip install -e ".[r2]"`。
3. **要** 在 producers 中优先使用 `publish_dataframe_from_dir()`（见 `src/opendata/producer.py`）。
4. **要** 通过 `OPENDATA_VERSION` 控制发布版本，通过 `OPENDATA_PREVIEW_ROWS` 控制 preview 行数。
5. **要** 读取远程 JSON/README 时防御性处理（类型/长度/字段存在性），把输入当成不可信。
6. **要** registry 由集中 rebuild 生成（`scripts/publish_official_local.py` / `Registry.build_from_producer_root()`），避免竞态。
7. **要** 合同/公开行为变更同步更新 `schemas/*.md`，里程碑变更同步更新 `opendata_todo.md`。

## 反思记录

- 2026-01-25：修改 `opendata_todo.md` 时误新增了额外章节而不是按需求只改指定章节。解决：遵循最小变更原则，只修改用户明确要求的 section，避免未授权扩展文档结构。
