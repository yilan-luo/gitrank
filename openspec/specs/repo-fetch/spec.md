# repo-fetch Specification

## Purpose
TBD - created by archiving change github-rank-tui. Update Purpose after archive.
## Requirements
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

