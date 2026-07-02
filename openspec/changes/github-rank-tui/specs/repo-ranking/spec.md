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
