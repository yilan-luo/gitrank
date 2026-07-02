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
