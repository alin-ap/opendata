##  完整执行计划 (Execution Plan)

> **目标：** 用最少的中心化服务，做一个“可审计、可复现、低成本”的数据注册表（Registry）与分发体系。
> - **默认后端：** GitHub Repo + GitHub Actions + Cloudflare R2
> - **可插拔：** 允许生产者未来切换到 self-hosted runner / 本地运行，不被 Actions 限死。

###  项目成功标准 (Definition of Done)

**MVP 必须满足的 3 个用户故事：**

1. **Consumer：** 通过 `od.load("namespace/dataset")` 在 1 分钟内拿到 DataFrame，并可指定版本/日期。
2. **Creator：** 只写 `main.py`（或 notebook）+ 配置文件，即可一键部署定时任务，把数据产出并发布到 R2。
3. **Portal：** 官网可搜索数据集、查看详情页（README/License/Size/更新时间/仓库链接）并预览样例数据。

**非目标（MVP 不做）：**

- 不做重计算平台（Spark/分布式 ETL）；超大任务通过 self-hosted runner 或外部算力解决。
- 不做中心化存储（数据不落你服务器磁盘）；真实数据流尽量直连 R2。
- 不做复杂权限模型（先公共数据为主，私有/团队权限放到商业化阶段）。

###  规范先行：数据集 ID / 元数据 / 存储布局

**1.1 数据集 ID（强约束）**

- 形式：`<namespace>/<name>`
- 示例：`official/us-stock-daily`、`community/binance-kline-1m`
- 规则：小写 + `-`，禁止空格，最大长度可先限制 80。

**1.2 R2 对象布局（可预测、可索引）**

- 建议路径：
  - `datasets/<namespace>/<name>/<version>/data.parquet`
  - `datasets/<namespace>/<name>/<version>/schema.json`
  - `datasets/<namespace>/<name>/latest.json`（指向最新版本）

**1.3 Dataset 元数据（Registry 里的最小字段）**

- `id`：数据集 ID
- `title` / `description`
- `tags`：数组
- `license`：SPDX 或文本
- `source`：数据来源说明/链接
- `repo`：GitHub URL（作为“可验证性”的主锚点）
- `owners`：GitHub handle 列表
- `frequency`：例如 `daily/hourly/adhoc`
- `versioning`：版本策略说明（例如 `date` 或 `semver`）
- `last_updated_at`
- `storage`：R2 bucket + key 前缀
- `checksum`：可选（用于下载完整性校验）

> **注意：** 元数据 schema 需要版本号（例如 `meta_version: 1`），后续演进不会破坏旧数据集。

###  系统拆分：你要维护哪些组件

**2.1 Python SDK/CLI（产品灵魂）**

- 包名：`opendata`（模块名 `opendata`，CLI 名 `od`）
- 最小命令集合：
  - `od load <dataset_id> [--version ...]`
  - `od push <dataset_id> <path|dataframe> [--version ...]`
  - `od init`：创建数据集骨架 + 写入元数据
  - `od deploy`：生成/更新 GitHub Actions workflow + 配置所需 secrets（尽量用短期凭证）
  - `od validate`：检查 metadata、输出 schema、抽样质量校验

**2.2 Registry（轻后端）**

- 职责：
  - 保存数据集元数据（最初可用 KV；后续可迁移 D1/Postgres）
  - 生成下载用的 pre-signed GET（可选；公开数据也可直读）
  - 生成上传用的 pre-signed PUT（强烈推荐；避免长期 R2 密钥下发）

**2.3 边缘网关（Cloudflare Workers，可选但推荐）**

- 职责：
  - API Key 鉴权 / 限流（游客 vs Pro）
  - 签发短期 URL（上传/下载）
  - 统一入口：`SDK -> Worker -> R2`（数据流仍直连 R2）

**2.4 Web Portal（静态 + API）**

- 主要读 `index.json` + 每个数据集的详情元数据
- 详情页展示：README（来自 repo 或 registry 缓存）、schema、大小、更新时间、下载示例、View on GitHub。

###  里程碑拆解（从 0 到可用）

下面按“能交付”的顺序拆，尽量每个里程碑都能形成可演示闭环。

**Milestone 0：样板工程 + 最小规范（1-2 天）**

- 输出：
  - `dataset_id` 规则与元数据 schema（`meta_version: 1`）
  - R2 key layout 约定
  - 3-5 个 `official` 数据集选题清单（用于冷启动）
- 验收：写一份“生产者 repo 最小示例”（伪代码也行）能让人理解怎么接入。

**Milestone 1：SDK 核心 I/O（3-7 天）**

- 实现：
  - `od.load()`：下载 Parquet 并返回 DataFrame（pandas/polars 二选一，另一个后续支持）
  - `od.push()`：本地 DataFrame/文件写 Parquet 并上传 R2
  - 基础缓存（避免重复下载）
- 验收：本地环境可以 `push -> load` 自己的数据集闭环。

**Milestone 2：Registry 最小可用（3-7 天）**

- 实现：
  - `create_dataset`：注册一个 dataset（写入元数据）
  - `resolve_dataset`：通过 dataset id + version 找到 R2 key
  - `index.json` 生成（可先用 cron job 或 Actions 定时生成）
- 验收：Portal/SDK 都能只依赖 registry 完成“查找 -> 下载”。

**Milestone 3：生产者接入（od init）（2-4 天）**

- 实现：
  - `od init` 在 repo 中生成：
    - `opendata.yaml`（元数据）
    - `main.py` 模板（包含输出约定：写到 `./out/` 或 stdout）
    - `README.md` 模板（用于详情页展示）
- 验收：一个新手照着模板改几行就能本地跑出 `out/data.parquet`。

**Milestone 4：一键部署（od deploy + GitHub Actions）（5-10 天）**

- 实现：
  - `od deploy` 生成 workflow：
    - 定时运行（cron）+ 手动触发
    - 执行 `main.py` 产物落地
    - 上传到 R2（推荐走“短期 pre-signed PUT”，而不是永久密钥）
    - 回写 `last_updated_at`（写 registry 或提交 badge/json）
  - 支持 `self-hosted runner`（作为重任务/固定 IP 的逃生舱）
- 验收：用户只需要 fork/clone -> `od init` -> push -> `od deploy` -> 等一次 action，就能在 Portal 看到更新。

**Milestone 5：Web Portal（3-7 天）**

- 实现：
  - 基于 `index.json` 的搜索/筛选（tag、namespace、更新时间）
  - 详情页：README 渲染 + schema + 下载示例
  - 预览：head 100 rows（可由 Actions 预生成 `preview.parquet/csv/json`，避免在线计算）
- 验收：非技术用户也能从网页找到数据并复制一段 `od.load()` 示例。

**Milestone 6：鉴权/限流/商业化（后续迭代）**

- 实现：
  - API Key：Free/Pro/Enterprise
  - Worker 侧限流：按 key、按 IP、按 namespace
  - 配额统计：下载次数、流量、失败率
- 验收：同一数据集对不同 key 呈现不同配额/速度策略。

###  安全与权限模型（从第一天就要对齐）

- **不要下发长期 R2 访问密钥** 给生产者仓库。
- 上传推荐流程：`od deploy` 配置一个“请求签名”的最小凭证（或 GitHub OIDC + 你后端换临时 token），每次 action 运行时拿短期 `pre-signed PUT`。
- 下载推荐流程：公开数据可直读；需要鉴权的走 Worker 签发短期 `pre-signed GET`。
- 供应链：workflow 中锁定依赖版本；必要时提供 `requirements.lock`/`uv.lock`。

###  质量与可观测性（让数据可信）

- 每次产出写入：`row_count`、`schema_hash`、`min/max date`（如适用）、`checksum`。
- Action 失败要有“可读日志”：错误分类（网络/解析/写入/上传）。
- Portal 展示健康度：最近 N 次运行成功率、最近一次失败原因摘要（从 Actions 抓取）。

###  冷启动与治理（让社区敢用）

- `official` 数据集策略：先维护 3-5 个“需求强、更新稳定”的基准数据集。
- `verified` 标识：明确审核规则（可复现、License 清晰、更新频率达标、无恶意依赖）。
- 不做站内评论：统一跳 GitHub Issues；把治理成本外包给 GitHub 生态。

###  推荐时间表（粗略）

- 第 1 周：Milestone 0-1（规范 + SDK I/O 闭环）
- 第 2 周：Milestone 2（Registry + index.json）
- 第 3-4 周：Milestone 3-4（od init/deploy + Actions 上线）
- 第 5 周：Milestone 5（Portal 上线）
- 第 6 周+：Milestone 6（鉴权/限流/商业化）

---

###  TODO


> 项目待办清单（可随迭代更新）。

- [x] 固化 `meta_version: 1` 元数据 schema（字段/约束/示例）并写入仓库（见 `schemas/metadata_v1.md`）
- [x] 确定 3-5 个 `official` 冷启动数据集选题与更新频率：
  - `official/binance-btcusdt-kline-1m` (daily)
  - `official/stooq-aapl-daily` (daily)
  - `official/open-meteo-berlin-hourly` (daily)
  - `official/owid-covid-global-daily` (daily)
- [x] 先跑通 SDK 闭环：`od push` 写 Parquet -> 上传（local/R2） -> `od load` 下载为 DataFrame
- [x] 设计 Registry 最小接口：`create_dataset` / `resolve_dataset` / `index.json`（`od registry add/refresh` + `index.json`）
- [x] 做一个端到端 demo：GitHub Actions 定时跑 -> R2 更新 -> Portal 可搜索/预览
  - 数据发布：`.github/workflows/publish_official.yml`
  - Portal：`portal/` + `.github/workflows/pages.yml`

- [x] 跑一次本地 cold-start：执行 `scripts/publish_official_local.py` 生成 local storage + `index.json`
