# TOOLS.md - 第一性原理导师 2.0

## 核心工具

### 1. 深度搜索与网页提取（已升级）

- **第一搜索工具（硬性）：** `tavily-search` - 穿透网络限制的全局搜索引擎
  - **优势**：直接获取国内外高价值摘要与链接，无需担心 Docker 环境。
- **正文提取工具：** `web-content-fetcher` - 网页正文深度解析引擎
  - **优势**：完美适配微信公众号、知乎、掘金等国内平台，支持隐身模式渲染。
- **分析工具：** `sequential-thinking` (MCP版) - 支持分支探索与动态反思的思维链引擎
  - **规则：** 每个话题至少 10 条公开信息源，中英文多轮搜索，标注来源，针对搜索来的信息进行分类，并对每分类内容进行不少于 5 轮的顺序思维分析。

### 2. Skill 映射

| 能力 | Skill 名 | 触发词 |
|------|---------|-------|
| 第一性原理解构 | `first-principles-decomposer` | 开始分析 |
| **阶段一信息检索** | `tavily-search` | 信息搜索 / 调研 |
| **阶段一深度解析** | `web-content-fetcher` | 提取全文 / 阅读网页 |
| **阶段一各方向顺序思维分析（强制）** | `sequential-thinking` | 阶段一搜索完成后自动触发 |
| 可视化卡片 | `ljg-card` | 做成图 / 卡片 / 铸 |
| 圆桌讨论 | `ljg-roundtable` | 圆桌 / 辩论 |
| 白话解释 | `ljg-plain` | 白话说 / 说人话 |
| 概念解剖 | `ljg-learn` | 概念解剖 / 深度理解 |

### 3. 配置备注

- `sequential-thinking` 已通过 `mcporter` 对接本地 MCP Server，支持 Revision 和 Branching。
- `ljg-card` 已配置劫持本地 Google Chrome，可绕过 Catalina 系统浏览器安装限制。
- `web-content-fetcher` 采用 Node.js + 本地 Chrome 内核，抓取微信公众号无验证码压力。
