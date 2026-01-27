# OpenData 模式：去中心化数据注册表（Registry）

> **一句话定义**：用 **GitHub Repo（代码与可审计性）+ GitHub Actions（计算与调度）+ Cloudflare R2（对象存储与分发）** 组成一个“去中心化数据注册表”。我们提供 **SDK/CLI** 把三者串起来，并提供 **Web Portal** 做检索与展示。

---

## 1) 核心逻辑：Registry（注册表）模式

这个体系的关键不是“我们集中托管数据”，而是“我们维护一个 **可索引、可验证、可审计（MVP 默认只提供最新数据；需要可复现快照时再引入 snapshot/version）** 的注册表（Registry）”。

* **代码在哪里？** 生产者自己的 **GitHub 仓库**（开源、版本管理、可审计）。
* **计算在哪里？** **GitHub Actions**（定时运行、低成本自动化）。
* **数据在哪里？** **Cloudflare R2**（便宜存储、0 egress 友好）。
* **我们提供什么？**

  * **Python SDK/CLI**：把“注册 → 产出 → 发布 → 校验 → 分发”串成一条流水线。
  * **轻量 Registry 服务**：负责鉴权、映射（dataset_id → R2 路径）、签发短期访问（pre-signed URL）。
  * **Web Portal**：可搜索、可预览、可追溯到 GitHub 源码。

---

## 2) 技术架构（The Stack）

### 2.1 存储层：Cloudflare R2（低成本对象存储）

* **核心**：R2
* **格式**：Parquet（高压缩 + 高性能）

### 2.2 交互层：Python SDK/CLI（产品灵魂）

目标：把复杂的发布与分发流程“产品化”，让用户感觉像在用 HuggingFace 一样顺手。

* 安装：`pip install opendata`
* 模块名：`opendata`，CLI：`od`

**消费者（Consumer）**：一行拿到 DataFrame（默认最新数据，支持时间区间选择）

```python
import opendata as od

# 默认返回最新数据（MVP 阶段不提供历史快照/version）
df = od.load("opendata/us-stock-daily")

# 选择时间区间
df_2024 = od.load(
    "opendata/us-stock-daily",
    start="2024-01-01",
    end="2024-12-31",
)
```

**生产者（Creator）**：只写抓取脚本 `main.py` + 元数据 `opendata.yaml`，其余自动化

```bash
od init    # 生成数据集骨架与元数据模板
od deploy  # 自动生成/更新 GitHub Actions、配置发布流程
```

### 2.3 服务端：Registry（极简后端）

* **职责最小化**：

  * 鉴权（API Key / 订阅档位）
  * dataset 映射（repo → dataset_id → R2 key layout）
  * 生成短期访问（pre-signed GET/PUT）
  * 生成/聚合全局索引 `index.json`
* **流量极低**：只发签名与索引，不搬运数据。

### 2.4 边缘网关：Cloudflare Workers（可选但推荐）

用于“精细化限流 + VIP 提速 + 统一入口”。

`SDK → Worker(鉴权/限流/签名) → R2`

---

## 3) 规范先行：ID / 元数据 / 存储布局

### 3.1 R2 对象布局（可预测、可索引）

**MVP：稳定 key（覆盖写）**

* `index.json`（全局 registry）
* `datasets/<namespace>/<name>/data.parquet`
* `datasets/<namespace>/<name>/metadata.json`
* `datasets/<namespace>/<name>/README.md`

（后续可扩展：manifest + 分片对象，用于按时间区间只拉取必要数据。）

### 3.2 元数据：`opendata.yaml`（静态 Source of Truth）

目标：让数据集“可被发现、可被审计、可被复用”。`opendata.yaml` 是 producer repo 的静态 Source of Truth。

结构化元数据。

必填字段：

* `id`: dataset_id（`namespace/name`）
* `title` / `description`
* `license`: 优先 SPDX（例如 `MIT`, `Apache-2.0`）
* `repo`: producer GitHub URL（可验证性的锚点）
* `source`: mapping

  * `provider`: 数据来源标识（例如 `us_treasury`, `fred`, `binance`）
  * `homepage`: 可选，机构/站点主页 URL
  * `dataset`: 可选，具体数据页/API 文档/下载链接

推荐字段：

* `topics`: string[]（主题/标签；可逐步收敛成受控词表）
* `geo`: mapping

  * `scope`: `global|region|country|multi`
  * `countries`: 可选，ISO 3166-1 alpha-2
  * `regions`: 可选（UN M49 / 自定义枚举）

* `owners`: string[]（维护者）
* `frequency`: string（例如 `daily`/`hourly`/`monthly`/`adhoc`）

示例：

```yaml
id: getopendata/treasury-yield-curve-daily
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
owners: [<github_handle>]
frequency: daily
```


---

## 4) 商业模式（简单、可扩展）

| 档位           | 费用 | 核心权限         | 运营成本          |
| ------------ | -- | ------------ | ------------- |
| Free API Key | 免费 | 可下载所有数据，但速度慢 | 极低（主要是 R2 存储） |
| Pro          | 订阅 | 速度快          | 仍然很低          |

* `Verified` 作为 **元信息标识**（可信度/审计程度/质量标准），不直接作为付费分层；数据的“发布者”用 `namespace`（通常对应 GitHub owner/org）表达。

---

## 5) Edge Computing：付费与限流（Workers 作为边缘网关）

### 5.1 为什么需要 Worker

* 避免纯 IP 限流的误伤
* 提供 Pro/VIP 的更高并发与更稳体验
* 把“鉴权、限流、短期签名”放在边缘，降低中心化成本

### 5.2 核心逻辑（Bouncer）

```js
export default {
  async fetch(request, env) {
    const apiKey = request.headers.get("X-API-Key");

    // VIP：校验通过则放行或更高配额
    if (apiKey && await env.VIP_KEYS.get(apiKey)) {
      return await env.MY_BUCKET.get(request.url);
    }

    // 游客：按 IP / 规则触发限流
    return await env.MY_BUCKET.get(request.url);
  }
}
```

##

---

## 6) 执行计划（能交付的里程碑拆解）

### Milestone 0：样板工程 + 最小规范（1–2 天）

- [x] 输出：dataset_id 规则、元数据 schema、R2 key layout、示例 3–5 个数据集清单
- [x] 验收：一份“生产者 repo 最小示例”让人看懂如何接入

### Milestone 1：SDK 核心 I/O（3–7 天）

- [x] `od.load()`：读取 `data.parquet` 并返回 DataFrame（pandas；内存解码，不落盘缓存）
- [x] `od.push()`：DataFrame/文件 → Parquet → 上传（同时写入 metadata/preview）
- [x] 验收：本地 `push → load` 闭环（单测覆盖）
- [ ] `od.load()`：支持 `start/end/columns` 等参数
- [ ] `manifest.json` + 时间分片：按区间只下载覆盖范围的分片

### Milestone 2：Registry 最小可用（3–7 天）

- [x] `index.json` registry：加载/保存/更新数据集列表
- [x] 注册 dataset 元数据：`od registry add` / `Registry.register_from_file()`
- [x] `index.json` 生成：从 producers root 重建并合并 `metadata.json`
- [x] 避免并发竞态：所有 producers 结束后一次性 rebuild `index.json`
- [ ] Registry 服务端：鉴权、repo→dataset_id 映射、pre-signed GET/PUT
- [ ] 验收：Portal/SDK 都只依赖 Registry 完成“查找 → 下载”（SDK 当前不读 `index.json` 做发现）

### Milestone 3：生产者接入（od init）（2–4 天）

- [x] 生成：`opendata.yaml`、`main.py` 模板、`README.md` 模板（`od init`）
- [x] 验收：新手照模板改几行就能本地运行并发布

### Milestone 4：一键部署（od deploy + Actions）（5–10 天）

- [x] workflow：cron + 手动触发，运行 main.py，上传到 R2（`od deploy` 生成）
- [x] 示例 producers（可选）：定时 workflow 发布到 R2
- [ ] 推荐：走短期 pre-signed PUT，不下发永久密钥
- [ ] 支持：self-hosted runner（重任务/固定 IP 的逃生舱）
- [ ] 验收：fork/clone → init → deploy → 等一次 action → Portal 可见更新

### Milestone 5：Web Portal（3–7 天）

- [x] 列表页：搜索（关键字匹配 id/title/description/tags）
- [ ] 列表页：筛选（tag/namespace/更新时间/时间覆盖范围）
- [x] 详情页：README + schema + 下载示例
- [x] 预览：预生成 head 100 rows（嵌入 metadata.json）避免在线计算
- [x] 验收：非技术用户也能从网页复制 `od.load()` 用起来

### Milestone 6：鉴权/限流/商业化（后续）

- [ ] API Key 档位：Free/Pro/Enterprise
- [ ] Worker 限流：按 key、按 IP、按 namespace
- [ ] 配额统计：下载次数、流量、失败率

---

## 7) 质量与可观测性（让数据可信）

* 每次产出写入：row_count、schema_hash、min/max date（如适用）、checksum
* Action 失败日志：可读、可分类（网络/解析/上传/权限）
* Portal 展示健康度：最近 N 次成功率、最近一次失败摘要

---

## 8. 项目成功标准（Definition of Done）

**MVP 必须满足 3 个用户故事：**

1. **Consumer**：`od.load("namespace/dataset")` 1 分钟内拿到 DataFrame（默认最新数据）。
2. **Creator**：一个文件比如 `main.py` + `opendata.yaml`，即可一键部署定时任务并发布到 R2。
3. **Portal**：可搜索数据集（sdk也可查）、查看详情（README/License/Size/更新时间/仓库链接）并预览样例。
