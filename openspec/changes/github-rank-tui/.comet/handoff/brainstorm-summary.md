# Brainstorm Summary

- Change: github-rank-tui
- Date: 2025-07-02

## 确认的技术方案

- **TUI 框架**：Textual，利用 Screen 栈机制匹配向导式参数输入
- **参数输入**：向导式（3 步：Topic → Time Window → Sort），Esc 回退上一步，状态保留
- **API 1000 条限制**：自适应时间切片——满 1000 条自动二分拆分窗口递归拉取，停止条件为 total ≤ 1000 或窗口 < 1 天
- **Settings**：Filter 改名为 Settings，存默认偏好（topic、时间窗口、排序方式）到 `~/.gitrank/config.json`，Search 打开时自动填入
- **排名公式**：composite = 0.50 × S_star + 0.30 × S_growth + 0.20 × S_activity，对数归一化，冷启动 S_growth 默认 0.5
- **测试策略**：分层——rank/cache 单元测试高覆盖 + API mock 测试 + TUI 手动验证
- **HTTP**：httpx（异步，不阻塞 Textual 事件循环）
- **缓存**：SQLite（repositories + star_history 双表）

## 关键取舍与风险

- **自适应切片 vs 接受 1000 上限**：选择切片保证数据完整性，代价是热门 topic 首次拉取 API 请求数增加；通过缓存和进度条缓解
- **Textual vs Rich 简单表格**：选择 Textual 提供更好的交互体验，代价是 Windows Terminal 兼容性需要实测验证
- **首次体验 vs 后续体验**：首次拉取数据较慢（API 限速 + 可能多次请求），后续走缓存秒出；UI 进度条告知用户当前状态
- **star_history 膨胀**：长期使用可能积累大量快照；后续需定期清理（保留最近 12 个月月度快照，更早的保留季度快照）

## 测试策略

| 层 | 方式 | 工具 |
|---|---|---|
| 排名引擎 | 纯单元测试 | pytest |
| 缓存层 | 单元 + :memory: SQLite 集成测试 | pytest |
| API 客户端 | httpx.MockTransport mock 测试 | pytest + respx |
| TUI | 手动验证（textual run --dev） | 手动 |
| CLI 入口 | CliRunner 参数解析测试 | pytest |

## Spec Patch

- `tui-app`: Filter → Settings 重命名，更新所有相关场景和描述
