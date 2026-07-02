## 1. 项目初始化

- [x] 1.1 创建项目目录结构和空白模块骨架（gitrank, api, cache, rank, tui）
- [x] 1.2 编写 `pyproject.toml`，声明依赖：textual, httpx, typer, pydantic
- [x] 1.3 创建 `README.md`，包含安装说明和基本用法示例

## 2. 数据模型与缓存层

- [x] 2.1 定义 Pydantic 数据模型（`Repository`, `StarSnapshot`）
- [x] 2.2 实现 SQLite 数据库初始化和 `repositories` / `star_history` 建表
- [x] 2.3 实现仓库数据增/查/更新操作（根据 github_id upsert）
- [x] 2.4 实现 star 历史快照写入与查询
- [x] 2.5 实现缓存命中判断和 `--refresh` 强制刷新逻辑

## 3. GitHub API 客户端

- [x] 3.1 实现 httpx 客户端基础封装（Base URL, 认证头, User-Agent）
- [x] 3.2 实现 Search API 调用：按 topic + created 日期范围搜索
- [x] 3.3 实现 API 限速检测（X-RateLimit-Remaining / Reset 头解析）
- [x] 3.4 实现限速降级模式（间隔控制）和 403 限速提示
- [x] 3.5 实现分页拉取（处理 GitHub API 分页，合并多页结果）

## 4. 排名引擎

- [x] 4.1 实现纯 star 数排序
- [x] 4.2 实现 S_star 因子计算（对数归一化）
- [x] 4.3 实现 S_growth 因子计算（月均增速 + 对数归一化，含冷启动默认值）
- [x] 4.4 实现 S_activity 因子计算（距上次 push 的线性衰减）
- [x] 4.5 实现 composite 复合分汇总与排序

## 5. TUI — 基座与主菜单

- [x] 5.1 创建 Textual App 基座和 CSS 主题
- [x] 5.2 实现 MainMenu 屏幕（Search / Filter / Quit 选项导航）
- [x] 5.3 实现全局按键绑定（q 退出，Esc 返回上级）

## 6. TUI — Search 与 Filter

- [x] 6.1 实现 Search 参数输入屏幕（topic 选择列表 + 自行输入）
- [x] 6.2 实现时间窗口选择（预设 + 自定义日期输入）
- [x] 6.3 实现排序方式切换（stars / composite）
- [x] 6.4 实现 Filter 设置屏幕（预设 topic 和默认时间窗口，保存到配置文件）
- [x] 6.5 实现搜索确认后的加载进度提示

## 7. TUI — 结果表格与详情

- [x] 7.1 实现结果表格屏幕（DataTable：Rank | Repository | Stars | Growth | Language | Description）
- [x] 7.2 实现键盘滚动浏览（↑↓、PageUp/PageDown）
- [x] 7.3 实现仓库详情卡片（Enter 展开，包含完整元数据 + GitHub URL）
- [x] 7.4 实现详情返回功能（Esc 回到表格）

## 8. CLI 入口与集成

- [x] 8.1 实现 CLI 入口（Typer），解析 `--topic`、`--since`、`--range`、`--sort`、`--limit` 参数
- [x] 8.2 连接 CLI 入口与 Textual App（将命令行参数传递到 TUI 预设状态）
- [x] 8.3 实现 GITHUB_TOKEN 环境变量检测与启动提示

## 9. 验证与收尾

- [x] 9.1 端到端手动测试：启动 → 搜索 → 浏览结果 → 查看详情 → 退出
- [x] 9.2 验证缓存命中：重复查询秒出结果
- [x] 9.3 验证 `--refresh` 强制刷新和 star_history 快照记录
- [x] 9.4 验证 API 限速场景（token 未设置时提示，达到限速时展示倒计时）
- [x] 9.5 Windows Terminal 兼容性验证（Textual 渲染是否正常）
