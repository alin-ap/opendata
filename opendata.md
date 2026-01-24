# OpenData 模式：去中心化金融数据注册表

## 一、 核心逻辑：Registry (注册表) 模式

- **代码在哪？** 在用户的 **GitHub** 仓库里（开源、版本管理）。
- **计算在哪？** 在 **GitHub Actions** 里（免费、定时运行）。
- **数据在哪？** 在 **Cloudflare R2** 里（免费流量、便宜存储）。
- **我们做什么？** 提供 **SDK** 串联三者，并提供 **Web 门户** 检索数据。

---

## 二、 技术架构 (The Stack)

### 1. 存储层 (成本极低)
- **核心：** Cloudflare R2。
- **格式：** Parquet (高性能、高压缩)。
- **优势：** 流出流量费为 $0。

### 2. 交互层 (Python SDK)
产品的灵魂，通过封装复杂逻辑降低用户门槛。
`pip install opendata`

- **数据消费者 (Consumer)：**
  ```python
  import opendata as od
  # 类似 HuggingFace，直接获取 DataFrame
  df = od.load("official/us-stock-daily")
  ```

- **数据生产者 (Creator)：**
  用户只需编写 `main.py` 爬虫脚本，即可实现“一键部署”：
  ```bash
  od init    # 登录并创建元数据
  od deploy  # 自动配置 GitHub Actions、Secret 及部署流程
  ```
  > **核心价值：** 将繁琐的 CI/CD 配置自动化，让用户感觉在部署云服务，实则运行在自己的 GitHub 上。

### 3. 服务端 (Backend)
- **功能：** 极简。负责鉴权、映射“仓库 -> R2 路径”、生成 **预签名链接 (Pre-signed URL)**。
- **流量：** 极低。真实数据流不经过服务器，直连 R2。

---

## 三、 商业模式

| 档位 | 费用 | 核心权限 | 运营成本 |
| :--- | :--- | :--- | :--- |
| **Free API Key** | **免费** | 下载公开数据（有限额） | 极低 (仅 R2 存储) |
| **Pro** | **付费** | 更高额度 / 并发 / 稳定性 | 极低 |

> **说明：** `Verified` 或 `Official` 标识将作为数据集的**元信息**展示，而非作为付费档位划分。

---

## 四、 启动路线图 (MVP RoadMap)

### 第一阶段：工具人阶段 (The Library)
**目标：** 打造好用的 SDK，满足自身需求。
1. 搭建 Cloudflare R2 + 极简 KV 数据库。
2. 开发 `opendata` SDK：实现 `push()` (DataFrame to Parquet) 和 `load()`。
3. **冷启动：** 官方维护 3-5 个核心脚本（如加密货币 K 线），建立数据基准。

### 第二阶段：社区化阶段 (The Hub)
**目标：** 降低门槛，吸引外部生产者。
1. 完善 `od deploy`：自动化 GitHub Action 配置。
2. 上线 **Web 官网**：
   - 数据集列表与搜索。
   - 数据预览 (Head 100 rows)。
   - **View on GitHub：** 源码透明化，建立社区信任。

### 第三阶段：商业化阶段 (The Business)
**目标：** 变现与生态闭环。
1. 上线 **API Key 鉴权系统**。
2. 推出 **Pro/Enterprise** 订阅计划，提供更高配额与 SLA。

---

## 五、 进阶：付费与限流方案 (Edge Computing)

为了解决 IP 限流“误伤”及 VIP 提速需求，引入 **Cloudflare Workers**。

### 1. 架构演进
`SDK 请求` -> `Cloudflare Worker (边缘网关)` -> `Cloudflare R2`

### 2. 核心逻辑 (The "Bouncer" Logic)
Worker 作为“智能交警”，在边缘节点处理请求：

```javascript
// 边缘鉴权伪代码
export default {
  async fetch(request, env) {
    const apiKey = request.headers.get("X-API-Key");

    // VIP 通道：查 KV 数据库，校验通过则不限速放行
    if (apiKey && await env.VIP_KEYS.get(apiKey)) {
      return await env.MY_BUCKET.get(request.url);
    }

    // 游客通道：按 IP 自动触发 WAF 限流
    return await env.MY_BUCKET.get(request.url);
  }
}
```

### 3. 方案优势
1. **零运维：** Serverless 架构，无需管理 Linux 服务器。
2. **精准控制：** 区分游客（严格限流）与 VIP（全速下载）。
3. **极低成本：** 每日 10 万次免费额度，初期几乎零成本。

---

## 六、 网站设计要点 (极简主义)
- **可发现性：** 列表页基于 `index.json` 实现搜索与标签。
- **可验证性：** 详情页展示 `README.md`、License、Size 及 GitHub 源码链接。
- **实时状态：** 显示 `Last updated` (同步 GitHub Actions 运行记录)。
- **互动：** 不自建评论区，直接跳转 GitHub Issues。

---

