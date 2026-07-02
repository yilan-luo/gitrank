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
