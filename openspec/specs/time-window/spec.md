# time-window Specification

## Purpose
TBD - created by archiving change github-rank-tui. Update Purpose after archive.
## Requirements
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

