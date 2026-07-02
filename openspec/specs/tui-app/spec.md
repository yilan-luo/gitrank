# tui-app Specification

## Purpose
TBD - created by archiving change github-rank-tui. Update Purpose after archive.
## Requirements
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

#### Scenario: 缓存命中
- **WHEN** 数据直接从缓存返回
- **THEN** 界面短暂显示"从缓存加载"后立即展示结果

### Requirement: Settings 设置界面
系统 SHALL 提供 Settings 界面，允许用户预设默认搜索偏好（topic、时间窗口、排序方式），设置保存到 `~/.gitrank/config.json`。Search 向导打开时自动填入 Settings 中的默认值。

#### Scenario: Settings 界面操作
- **WHEN** 用户在主菜单选择 Settings
- **THEN** 进入 Settings 界面，可设置：默认 Topic、默认 Time Window、默认 Sort，保存到本地配置文件 `~/.gitrank/config.json`

#### Scenario: Search 自动填入 Settings 默认值
- **WHEN** 用户已通过 Settings 保存默认偏好后进入 Search
- **THEN** Search 向导各步骤自动高亮 Settings 中的默认选项，用户可直接 Enter 确认或选择其他值覆盖

