# Comet Design Handoff

- Change: github-rank-tui
- Phase: design
- Mode: compact
- Context hash: bf50be1938946d9cf4186057f1e4513978af50f2ceed8b71a4ddd90a67a030f9

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/github-rank-tui/proposal.md

- Source: openspec/changes/github-rank-tui/proposal.md
- Lines: 1-41
- SHA256: 2c214f6a0baef543e633ed721dd5b4f6eb40e02e92f165f1f1b18925f66da9a5

```md
## Why

GitHub Trending 只能回溯到最近一个月。用户如果几周或几个月没有关注开源社区，就会错过那些在 Trending 窗口之外爆发的好项目。而 GitHub 自带的 Search 不擅长按"新兴热度"排序——高 star 老项目永远排在前面，真正值得关注的新项目反而被淹没。本项目提供一个交互式终端工具，让用户能按任意时间窗口、任意话题方向发现"那个时间段里最值得关注的项目"。

## What Changes

提供一个新的 CLI 工具 `gitrank`（内部项目名 `github-rank-tui`），核心能力包括：

- **GitHub 仓库数据采集与本地缓存**：通过 GitHub REST/Search API 拉取仓库元数据（star 数、描述、语言、话题、创建时间、最近更新时间等），写入本地 SQLite 数据库，支持增量更新
- **双模式排名引擎**：提供 `stars`（纯 star 数降序）和 `composite`（star 数 × 0.5 + 增速 × 0.3 + 活跃度 × 0.2 加权）两种排序
- **按话题分类筛选**：支持 `--topic` 参数或交互界面中选择话题分类（ai, frontend, rust, python 等）
- **任意时间窗口查询**：`--since` 指定起始日期，`--range` 指定起止区间
- **交互式终端界面（TUI）**：启动后展示选项菜单（Search / Filter / Quit），支持键盘导航（↑↓）、Enter 选中看详情、q 退出。排名结果以表格展示，每行附仓库简介

### 非目标

- 智能推荐 / AI 语义分析（预留未来扩展）
- Web 界面、仪表盘、定期报表、邮件推送
- 全量 GitHub 仓库索引
- 多用户 / SaaS 化

## Capabilities

### New Capabilities

- `repo-fetch`: 从 GitHub API 拉取仓库元数据，写入本地 SQLite 缓存，支持增量更新和 API 限速处理
- `repo-ranking`: 双模式排名引擎——纯 star 数排序与加权复合分排序（star × 0.5 + 增速 × 0.3 + 活跃度 × 0.2）
- `topic-filter`: 按话题分类（topic）筛选仓库
- `time-window`: 按用户指定的时间窗口（`--since` 或 `--range`）过滤仓库
- `tui-app`: 交互式终端应用，包含主菜单导航、结果表格浏览、仓库详情卡片、退出机制

### Modified Capabilities

_无（全新增，不修改已有能力）_

## Impact

- **新增依赖**：Python 项目从零开始，引入 `rich` / `textual`（TUI）、`httpx` 或 `requests`（API 调用）、`sqlite3`（标准库，本地缓存）
- **API 限速**：依赖 GitHub API，需支持 token 认证（GITHUB_TOKEN 环境变量），实现速率感知的重试与降级策略
- **数据规模**：中等（活跃仓库数万级别），SQLite 完全够用，无需引入外部数据库服务
- **平台**：优先支持 macOS / Linux 终端，Windows Terminal 兼容
```

## openspec/changes/github-rank-tui/design.md

- Source: openspec/changes/github-rank-tui/design.md
- Lines: 1-181
- SHA256: 50ae8fc85af3c3de879d6ae6cfb45bbff59cddccdb86fd3a2cb2aba893702736

[TRUNCATED]

```md
## Context

项目从零开始。用户需要一款 Python TUI 工具来按时间窗口和话题浏览 GitHub 仓库排名，数据通过 GitHub API 获取并缓存到本地 SQLite。仓库规模控制在数万活跃仓库级别，无需分布式或外部数据库。

## Goals / Non-Goals

**Goals:**
- 交互式终端界面：菜单导航、表格浏览、详情查看、随时退出
- 从 GitHub API 拉取仓库元数据并本地缓存（SQLite）
- 支持双模式排名：纯 star 数和加权复合分
- 支持按 topic 筛选、按时间窗口过滤
- 优雅处理 GitHub API 限速

**Non-Goals:**
- Web UI、Dashboard、定期报表
- 智能推荐 / AI 分析
- 全量仓库索引
- 多用户 / 认证

## Decisions

### 1. TUI 框架：Textual

选择 [Textual](https://textual.textualize.io/) 而非 Rich + prompt-toolkit 手拼。

| 考量 | Textual | Rich (仅格式化) |
|------|---------|-----------------|
| 组件化 UI | ✅ ListView, DataTable, Input | ❌ 需手写 |
| 键盘导航 | ✅ 内置 focus/app 系统 | ❌ 需手写事件循环 |
| 异步支持 | ✅ async/await 原生 | ❌ |
| 开发生态 | ✅ CSS 布局、主题 | ❌ |
| 学习曲线 | 中等 | 低 |

Textual 是 Rich 的姊妹项目，天然兼容 Rich 的渲染输出。对于我们的交互需求（菜单→列表→详情→返回），Textual 的 `Screen` 栈机制天然匹配。

### 2. HTTP 客户端：httpx

选择 `httpx`。Textual 框架本身是异步的，`httpx` 支持 `async/await`，不会阻塞 UI。备选方案 `requests` 在异步上下文中会阻塞事件循环。

### 3. 项目结构

```
github-rank-tui/
├── gitrank/
│   ├── __init__.py
│   ├── main.py              # CLI 入口 (Typer) + Textual 启动
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py           # Textual App 基座
│   │   ├── screens/
│   │   │   ├── main_menu.py # 主菜单：Search / Filter / Quit
│   │   │   ├── search.py    # 搜索参数输入（topic, since, sort）
│   │   │   └── results.py   # 结果表格 + 仓库详情
│   │   └── widgets/
│   │       ├── repo_table.py   # 排名表格组件
│   │       └── repo_detail.py  # 仓库详情卡片
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py       # GitHub API 客户端（httpx, 限速感知）
│   │   └── models.py       # 仓库数据模型（dataclass / Pydantic）
│   ├── cache/
│   │   ├── __init__.py
│   │   └── db.py           # SQLite 操作（建表、查询、插入、增量更新）
│   └── rank/
│       ├── __init__.py
│       └── engine.py       # 排名引擎：stars / composite 两种算法
├── tests/
├── pyproject.toml
└── README.md
```

### 4. SQLite 数据模型

```sql
CREATE TABLE IF NOT EXISTS repositories (
    id              INTEGER PRIMARY KEY,
    github_id       INTEGER UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,              -- "owner/repo"
    description     TEXT,
    language        TEXT,
```

Full source: openspec/changes/github-rank-tui/design.md

## openspec/changes/github-rank-tui/tasks.md

- Source: openspec/changes/github-rank-tui/tasks.md
- Lines: 1-64
- SHA256: 1ea7dc22942c3796f91fa606bb5a030a61ec59f896c1d85728ccda427f67fdbd

```md
## 1. 项目初始化

- [ ] 1.1 创建项目目录结构和空白模块骨架（gitrank, api, cache, rank, tui）
- [ ] 1.2 编写 `pyproject.toml`，声明依赖：textual, httpx, typer, pydantic
- [ ] 1.3 创建 `README.md`，包含安装说明和基本用法示例

## 2. 数据模型与缓存层

- [ ] 2.1 定义 Pydantic 数据模型（`Repository`, `StarSnapshot`）
- [ ] 2.2 实现 SQLite 数据库初始化和 `repositories` / `star_history` 建表
- [ ] 2.3 实现仓库数据增/查/更新操作（根据 github_id upsert）
- [ ] 2.4 实现 star 历史快照写入与查询
- [ ] 2.5 实现缓存命中判断和 `--refresh` 强制刷新逻辑

## 3. GitHub API 客户端

- [ ] 3.1 实现 httpx 客户端基础封装（Base URL, 认证头, User-Agent）
- [ ] 3.2 实现 Search API 调用：按 topic + created 日期范围搜索
- [ ] 3.3 实现 API 限速检测（X-RateLimit-Remaining / Reset 头解析）
- [ ] 3.4 实现限速降级模式（间隔控制）和 403 限速提示
- [ ] 3.5 实现分页拉取（处理 GitHub API 分页，合并多页结果）

## 4. 排名引擎

- [ ] 4.1 实现纯 star 数排序
- [ ] 4.2 实现 S_star 因子计算（对数归一化）
- [ ] 4.3 实现 S_growth 因子计算（月均增速 + 对数归一化，含冷启动默认值）
- [ ] 4.4 实现 S_activity 因子计算（距上次 push 的线性衰减）
- [ ] 4.5 实现 composite 复合分汇总与排序

## 5. TUI — 基座与主菜单

- [ ] 5.1 创建 Textual App 基座和 CSS 主题
- [ ] 5.2 实现 MainMenu 屏幕（Search / Filter / Quit 选项导航）
- [ ] 5.3 实现全局按键绑定（q 退出，Esc 返回上级）

## 6. TUI — Search 与 Filter

- [ ] 6.1 实现 Search 参数输入屏幕（topic 选择列表 + 自行输入）
- [ ] 6.2 实现时间窗口选择（预设 + 自定义日期输入）
- [ ] 6.3 实现排序方式切换（stars / composite）
- [ ] 6.4 实现 Filter 设置屏幕（预设 topic 和默认时间窗口，保存到配置文件）
- [ ] 6.5 实现搜索确认后的加载进度提示

## 7. TUI — 结果表格与详情

- [ ] 7.1 实现结果表格屏幕（DataTable：Rank | Repository | Stars | Growth | Language | Description）
- [ ] 7.2 实现键盘滚动浏览（↑↓、PageUp/PageDown）
- [ ] 7.3 实现仓库详情卡片（Enter 展开，包含完整元数据 + GitHub URL）
- [ ] 7.4 实现详情返回功能（Esc 回到表格）

## 8. CLI 入口与集成

- [ ] 8.1 实现 CLI 入口（Typer），解析 `--topic`、`--since`、`--range`、`--sort`、`--limit` 参数
- [ ] 8.2 连接 CLI 入口与 Textual App（将命令行参数传递到 TUI 预设状态）
- [ ] 8.3 实现 GITHUB_TOKEN 环境变量检测与启动提示

## 9. 验证与收尾

- [ ] 9.1 端到端手动测试：启动 → 搜索 → 浏览结果 → 查看详情 → 退出
- [ ] 9.2 验证缓存命中：重复查询秒出结果
- [ ] 9.3 验证 `--refresh` 强制刷新和 star_history 快照记录
- [ ] 9.4 验证 API 限速场景（token 未设置时提示，达到限速时展示倒计时）
- [ ] 9.5 Windows Terminal 兼容性验证（Textual 渲染是否正常）
```

## openspec/changes/github-rank-tui/specs/repo-fetch/spec.md

- Source: openspec/changes/github-rank-tui/specs/repo-fetch/spec.md
- Lines: 1-53
- SHA256: 8481ba5f7d33c0b198ee6f35c972b9392b60557cdce481d28d91959b5fa66606

```md
## ADDED Requirements

### Requirement: 从 GitHub API 搜索仓库
系统 SHALL 通过 GitHub Search API (`GET /search/repositories`) 按指定条件检索仓库元数据，包括：full_name、description、language、topics、stargazers_count、forks_count、open_issues_count、created_at、updated_at、pushed_at。

#### Scenario: 按 topic 和时间窗口搜索成功
- **WHEN** 用户指定 `topic=ai` 且 `since=2025-01-01`
- **THEN** 系统调用 Search API，参数 `q=topic:ai+created:>=2025-01-01`，返回匹配仓库列表

#### Scenario: API 认证
- **WHEN** 环境变量 `GITHUB_TOKEN` 已设置
- **THEN** 所有 API 请求附带 `Authorization: Bearer $GITHUB_TOKEN` 头，享受 5000 req/h 限速

#### Scenario: 未认证警告
- **WHEN** 环境变量 `GITHUB_TOKEN` 未设置
- **THEN** 系统启动时在 UI 中显示警告"未检测到 GITHUB_TOKEN，限速仅 60 req/h"

### Requirement: 本地 SQLite 缓存
系统 SHALL 将拉取的仓库数据持久化到本地 SQLite 数据库（`repositories` 表），以 `github_id` 作为唯一键，后续相同的查询条件可直接从缓存返回。

#### Scenario: 首次查询写入缓存
- **WHEN** 用户首次执行某个查询条件组合
- **THEN** 系统从 API 拉取数据，写入 `repositories` 表，`fetched_at` 记录当前时间戳

#### Scenario: 重复查询命中缓存
- **WHEN** 用户再次执行相同的查询条件
- **THEN** 系统直接从 SQLite 缓存返回结果，不发起 API 请求

#### Scenario: 强制刷新
- **WHEN** 用户指定 `--refresh` 选项
- **THEN** 系统忽略缓存，重新拉取数据并更新 `repositories` 表和 `star_history` 表

### Requirement: 增量更新与 star 历史
系统 SHALL 维护 `star_history` 表，记录每次抓取时各仓库的 star 数快照，支持后续的增速计算。

#### Scenario: 首次抓取记录快照
- **WHEN** 仓库首次写入缓存
- **THEN** 同时在 `star_history` 表中插入一条记录（github_id, stargazers_count, recorded_at）

#### Scenario: 刷新时追加快照
- **WHEN** 用户执行 `--refresh` 且 star 数有变化
- **THEN** 系统在 `star_history` 表中插入新的快照记录

### Requirement: API 限速感知
系统 SHALL 检测 GitHub API 限速状态，在接近限制时自动降速，在触发限速时提示用户等待。

#### Scenario: 接近限速阈值
- **WHEN** `X-RateLimit-Remaining` < 50
- **THEN** 系统切换到保守模式，每次 API 请求间隔 ≥ 1 秒

#### Scenario: 触发限速
- **WHEN** API 返回 403 且限速已耗尽
- **THEN** 系统解析 `X-RateLimit-Reset`，在 UI 中显示"API 限速，请等待 N 分钟"及倒计时
```

## openspec/changes/github-rank-tui/specs/repo-ranking/spec.md

- Source: openspec/changes/github-rank-tui/specs/repo-ranking/spec.md
- Lines: 1-42
- SHA256: 6e06eb9adf3b35ff61818489ce3958b1f16a8932c3874378e64aad5889587759

```md
## ADDED Requirements

### Requirement: 纯 star 数排名
系统 SHALL 支持按 `stargazers_count` 降序排列仓库。

#### Scenario: 按 star 数排名
- **WHEN** 用户选择排序方式为 `stars`
- **THEN** 结果列表按 star 数从高到低排列

### Requirement: 加权复合分排名
系统 SHALL 支持按加权复合分排序，公式为 `0.50 × S_star + 0.30 × S_growth + 0.20 × S_activity`，各项归一化到 [0, 1]。

#### Scenario: 按复合分排名
- **WHEN** 用户选择排序方式为 `composite`
- **THEN** 结果列表按复合分从高到低排列，每一项因子已归一化

#### Scenario: Star 因子计算
- **WHEN** 计算 S_star
- **THEN** 使用对数归一化：`log10(stars + 1) / log10(max_stars_in_result + 1)`

#### Scenario: 增速因子计算
- **WHEN** 计算 S_growth 且有至少 2 条历史快照
- **THEN** 计算月均新增 star = (当前 star - 最早快照 star) / 间隔月数，然后对数归一化

#### Scenario: 增速因子冷启动
- **WHEN** 计算 S_growth 时仅有一条快照（首次抓取）
- **THEN** S_growth 设为 0.5（中位默认值）

#### Scenario: 活跃度因子计算
- **WHEN** 计算 S_activity
- **THEN** 使用 `1 - (days_since_last_push / window_days)`，clamp 到 [0, 1]

### Requirement: 排名结果分页
系统 SHALL 支持限制返回条数，默认 20 条，用户可调整。

#### Scenario: 默认显示前 20
- **WHEN** 用户未指定 `--limit`
- **THEN** 结果列表仅显示前 20 条

#### Scenario: 自定义条数
- **WHEN** 用户指定 `--limit 50`
- **THEN** 结果列表显示前 50 条
```

## openspec/changes/github-rank-tui/specs/time-window/spec.md

- Source: openspec/changes/github-rank-tui/specs/time-window/spec.md
- Lines: 1-30
- SHA256: 009a8e28e73b048ce0a7a94d3831204ff10294d2ed54bcc8e77da2977bc3169a

```md
## ADDED Requirements

### Requirement: 按起始日期过滤
系统 SHALL 支持 `--since` 参数，筛选在指定日期之后创建的仓库。

#### Scenario: 指定起始日期
- **WHEN** 用户选择 `since=2025-01-01`
- **THEN** 系统仅返回 `created_at >= 2025-01-01` 的仓库

#### Scenario: 日期格式验证
- **WHEN** 用户输入的日期格式非 `YYYY-MM-DD`
- **THEN** 系统提示"日期格式错误，请使用 YYYY-MM-DD"

### Requirement: 按时间区间过滤
系统 SHALL 支持 `--range` 参数，筛选在指定起止日期之间创建的仓库。

#### Scenario: 指定时间区间
- **WHEN** 用户选择 `range=2024-06..2024-12`
- **THEN** 系统仅返回 `2024-06-01 <= created_at < 2025-01-01` 的仓库

#### Scenario: range 优先于 since
- **WHEN** 用户同时指定了 `--range` 和 `--since`
- **THEN** 系统优先使用 `--range`，忽略 `--since`

### Requirement: 默认时间窗口
系统 SHALL 在用户未指定时间窗口时，默认使用最近 6 个月。

#### Scenario: 未指定时间窗口
- **WHEN** 用户未指定 `--since` 或 `--range`
- **THEN** 系统默认筛选最近 6 个月创建的仓库，并在界面中提示当前使用的默认窗口
```

## openspec/changes/github-rank-tui/specs/topic-filter/spec.md

- Source: openspec/changes/github-rank-tui/specs/topic-filter/spec.md
- Lines: 1-27
- SHA256: fc6f6203017500d928ab171b777386ddd0dcca4790b7eaa785ae2b55f531e464

```md
## ADDED Requirements

### Requirement: 按 topic 筛选
系统 SHALL 支持按 GitHub topic 标签筛选仓库。

#### Scenario: 指定单个 topic
- **WHEN** 用户选择 `topic=ai`
- **THEN** 系统仅返回标记了 `ai` topic 的仓库

#### Scenario: 不指定 topic
- **WHEN** 用户未选择任何 topic
- **THEN** 系统返回所有话题的仓库，不做 topic 过滤

#### Scenario: topic 有效性提示
- **WHEN** 用户指定的 topic 在结果中匹配极少量仓库（< 3）
- **THEN** 系统在结果界面提示"该话题匹配结果较少，可能是非常见 topic"

### Requirement: 预置常用 topic 列表
系统 SHALL 提供一组常用技术方向 topic 供用户快速选择，同时允许用户自行输入任意 topic。

#### Scenario: 展示预置 topic 列表
- **WHEN** 用户进入 topic 筛选界面
- **THEN** 系统展示常用 topic 列表（如 `ai`, `machine-learning`, `frontend`, `react`, `vue`, `rust`, `python`, `go`, `cli`, `devops` 等），并提供"自行输入"选项

#### Scenario: 用户自行输入 topic
- **WHEN** 用户选择"自行输入"
- **THEN** 系统提供文本输入框，用户输入任意 topic 字符串
```

## openspec/changes/github-rank-tui/specs/tui-app/spec.md

- Source: openspec/changes/github-rank-tui/specs/tui-app/spec.md
- Lines: 1-94
- SHA256: 83a3518dc17e06a2404eb364975ceb84cdf9f68da98ef755c04f01e6138580bd

[TRUNCATED]

```md
## ADDED Requirements

### Requirement: 主菜单导航
系统启动时 SHALL 展示主菜单界面，包含 Search、Settings、Quit 选项，用户可使用键盘 ↑↓ 导航、Enter 选中。

#### Scenario: 启动进入主菜单
- **WHEN** 用户运行 `gitrank` 命令
- **THEN** 终端展示主菜单，包含"Search"、"Settings"、"Quit"三个选项

#### Scenario: 键盘导航
- **WHEN** 用户按下 ↑ 或 ↓ 键
- **THEN** 菜单高亮移动到上一个或下一个选项

#### Scenario: 选中选项
- **WHEN** 用户在高亮选项上按 Enter
- **THEN** 系统进入该选项对应的子界面

### Requirement: 退出程序
用户 SHALL 能够在任意界面按 `q` 键退出程序，或在主菜单选择 Quit 退出。

#### Scenario: 按 q 退出
- **WHEN** 用户在任意界面按下 `q`
- **THEN** 程序立即退出，返回终端提示符

#### Scenario: 主菜单选 Quit
- **WHEN** 用户在主菜单选择 Quit 并按 Enter
- **THEN** 程序退出

### Requirement: Search 向导式参数输入
系统 SHALL 以向导式（分步）流程收集搜索参数，分三步：Topic → Time Window → Sort。用户按 Enter 前进到下一步，按 Esc 返回上一步，已输入的状态在回退时保留。

#### Scenario: 向导第一步——Topic 选择
- **WHEN** 用户在主菜单选择 Search
- **THEN** 进入 Topic 选择界面，展示常用 topic 列表（如 ai, machine-learning, frontend 等）+ "自行输入"选项。如 Settings 中已存默认 topic，自动高亮该项

#### Scenario: 向导第二步——Time Window 选择
- **WHEN** 用户在 Topic 步骤按 Enter
- **THEN** 进入 Time Window 界面，展示预设选项（最近 1 个月/3 个月/6 个月/自定义区间）。如 Settings 中已存默认时间窗口，自动高亮该项

#### Scenario: 向导第三步——Sort 选择
- **WHEN** 用户在 Time Window 步骤按 Enter
- **THEN** 进入 Sort 选择界面，展示 stars / composite 两个选项。如 Settings 中已存默认排序，自动高亮该项

#### Scenario: Esc 回退
- **WHEN** 用户在向导任一步骤按 Esc
- **THEN** 返回上一步，已选参数保留；第一步按 Esc 返回主菜单

#### Scenario: 确认搜索
- **WHEN** 用户在 Sort 步骤按 Enter
- **THEN** 系统发起数据查询（缓存优先），显示加载进度，跳转到结果表格

### Requirement: 结果表格展示
系统 SHALL 以表格形式展示排名结果，列包含：排名序号、仓库名、Star 数、月均增速、语言、简介摘要。

#### Scenario: 排名表格
- **WHEN** 搜索结果就绪
- **THEN** 展示 DataTable，列为：Rank | Repository | Stars | Growth(/mo) | Language | Description

#### Scenario: 上下翻页
- **WHEN** 结果超过一屏
- **THEN** 用户可使用 ↑↓ 或 PageUp/PageDown 滚动浏览

### Requirement: 仓库详情查看
用户在结果表格中选中某个仓库按 Enter 时，系统 SHALL 展示该仓库详情卡片。

#### Scenario: 查看详情
- **WHEN** 用户选中某行按 Enter
- **THEN** 展示详情卡片，包含：Full Name、Description、Stars、Forks、Open Issues、Language、Topics、Created、Last Pushed、GitHub URL

#### Scenario: 返回列表
- **WHEN** 用户在详情卡片按 Esc 或 q
- **THEN** 返回结果表格

### Requirement: 加载状态反馈
系统 SHALL 在数据拉取期间展示加载状态，避免用户面对空白界面。

#### Scenario: 首次加载
- **WHEN** 数据正在从 API 拉取
- **THEN** 界面显示进度条和"正在从 GitHub 拉取数据..."文字提示

```

Full source: openspec/changes/github-rank-tui/specs/tui-app/spec.md

