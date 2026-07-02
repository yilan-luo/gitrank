---
change: github-rank-tui
design-doc: docs/superpowers/specs/2025-07-02-github-rank-tui-design.md
base-ref: 3cc02b7f9735eee68cc58d7eb79cde674197845c
archived-with: 2026-07-02-github-rank-tui
---

# github-rank-tui 实施计划

**Goal:** 构建一个 Python TUI 工具 `gitrank`，让用户按话题和时间窗口搜索 GitHub 仓库排名，支持 star 数和加权复合分两种排序。

**Architecture:** 分层架构：CLI 入口(Typer) → TUI 层(Textual Screen 栈，向导式搜索) → 查询编排层(参数转换、缓存优先、API 拉取) → 底层模块(API 客户端/缓存 SQLite/排名引擎)。

**Tech Stack:** Python 3.11+, Textual, httpx, Typer, Pydantic, SQLite (标准库), pytest + respx

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | 项目元数据、依赖声明、脚本入口点 |
| `gitrank/main.py` | CLI 入口：Typer 参数解析 → 启动 Textual App |
| `gitrank/tui/app.py` | Textual App 基座：全局按键绑定、CSS 主题、Screen 栈管理 |
| `gitrank/tui/state.py` | SearchState 数据类：向导各步骤参数收集与传递 |
| `gitrank/tui/screens/main_menu.py` | 主菜单 Screen：Search / Settings / Quit |
| `gitrank/tui/screens/search_topic.py` | 搜索向导 Step1：Topic 选择 |
| `gitrank/tui/screens/search_time.py` | 搜索向导 Step2：时间窗口选择 |
| `gitrank/tui/screens/search_sort.py` | 搜索向导 Step3：排序方式选择 |
| `gitrank/tui/screens/results.py` | 结果表格 Screen |
| `gitrank/tui/screens/settings.py` | Settings 设置 Screen |
| `gitrank/tui/screens/loading.py` | 加载进度 Screen |
| `gitrank/tui/widgets/repo_table.py` | DataTable 排名表格组件 |
| `gitrank/tui/widgets/repo_detail.py` | 仓库详情卡片组件 |
| `gitrank/api/client.py` | GitHub API 客户端：搜索、分页、限速感知、自适应时间切片 |
| `gitrank/api/models.py` | Pydantic 数据模型：Repository, StarSnapshot, SearchParams, RankedRepo |
| `gitrank/cache/db.py` | SQLite 数据库操作：建表、CRUD、缓存命中判断、star_history |
| `gitrank/rank/engine.py` | 排名引擎：stars 排序、composite 加权分计算 |
| `gitrank/orchestrator.py` | 查询编排层：将 SearchState → 缓存/API → 排名结果 |
| `gitrank/settings.py` | Settings 管理器：读取/写入 ~/.gitrank/config.json |

## Tasks

### Task 1: 项目骨架初始化
Files: `pyproject.toml`, `README.md`, all `__init__.py` files, `gitrank/main.py` (minimal)
- 创建目录结构，编写 pyproject.toml (dependencies: textual, httpx, typer, pydantic; dev: pytest, respx, pytest-asyncio)
- 创建最小 main.py 和 README.md
- 验证 `pip install -e .` 和 `gitrank --help` 可用

### Task 2: Pydantic 数据模型
Files: `gitrank/api/models.py`, `tests/test_models.py`
- Repository (id, full_name, description, language, topics, stargazers_count, created_at, pushed_at...)
- StarSnapshot (github_id, stargazers_count, recorded_at)
- SearchParams (topic, date_start, date_end, sort, limit)
- RankedRepo (rank, repo, stars_score, growth_score, activity_score, composite_score, growth_per_month)
- 5 tests covering parsing, defaults, validation

### Task 3: SQLite 缓存层
Files: `gitrank/cache/db.py`, `tests/test_cache.py`, `tests/conftest.py`
- CacheDB(db_path): initialize(), upsert_repository(), get_repository(), get_repositories_by_date(), cache_hit(), record_snapshot(), get_snapshots(), refresh_repositories()
- 双表：repositories (github_id UNIQUE) + star_history
- ~12 tests covering CRUD, date range filtering, topic filtering, cache hit/miss, star history

### Task 4: GitHub API 客户端
Files: `gitrank/api/client.py`, `tests/test_api_client.py`
- GitHubClient(token): search_repos() (pagination+rate-limit), adaptive_fetch() (time slicing), _update_rate_limit(), _should_throttle()
- 自适应时间切片：total > 1000 → 二分窗口递归；停止条件: total ≤ 1000 / window < 1 day / depth ≥ 10
- ~6 tests with respx mocking

### Task 5: 排名引擎
Files: `gitrank/rank/engine.py`, `tests/test_rank_engine.py`
- rank_by_stars(): 纯 star 降序
- rank_by_composite(): 0.50×S_star + 0.30×S_growth + 0.20×S_activity
- _calc_star_score(): log10 归一化
- _calc_growth_score(): 月均增速 + cold start 默认 0.5
- _calc_activity_score(): 线性衰减 clamp [0,1]
- ~11 tests covering all edge cases

### Task 6: Settings 管理与查询编排层
Files: `gitrank/settings.py`, `gitrank/orchestrator.py`, `tests/test_settings.py`, `tests/test_orchestrator.py`
- Settings.load()/save()/update()/get_defaults() → ~/.gitrank/config.json
- QueryOrchestrator.execute(params, force_refresh): 缓存 → API → 排名

### Task 7: TUI 基座与主菜单
Files: `gitrank/tui/app.py`, `gitrank/tui/state.py`, `gitrank/tui/screens/main_menu.py` + 占位 screens
- GitRankApp (Textual App, q=quit, push MainMenuScreen)
- SearchState dataclass: topic, time_window, custom_since, custom_until, sort
- MainMenuScreen: ListView with Search/Settings/Quit, Enter 导航

### Task 8: TUI 搜索向导
Files: `gitrank/tui/screens/search_topic.py`, `search_time.py`, `search_sort.py`
- SearchTopicScreen: 预设 topic 列表 + 自定义输入, Enter→Step2, Esc→返回
- SearchTimeScreen: 预设窗口 + 自定义日期, Enter→Step3, Esc→返回
- SearchSortScreen: stars/composite 选择, Enter→开始搜索

### Task 9: TUI Settings 屏幕
Files: `gitrank/tui/screens/settings.py`
- SettingsScreen: 显示当前默认值，选择修改 Topic/Time/Sort
- 子 picker screens: _TopicPickerScreen, _TimePickerScreen, _SortPickerScreen
- 修改后自动保存到 ~/.gitrank/config.json

### Task 10: TUI 加载与结果屏幕
Files: `gitrank/tui/screens/loading.py`, `results.py`, `gitrank/tui/widgets/repo_table.py`, `repo_detail.py`
- LoadingScreen: ProgressBar + status text, 后台线程执行查询
- ResultsScreen: DataTable (Rank|Repository|Stars|Growth|Language|Description), Enter→详情, Esc→返回
- RepoDetailScreen: 完整元数据卡片 (stars, forks, issues, language, topics, dates, GitHub URL, scores)

### Task 11: CLI 入口与集成
Files: `gitrank/main.py`, `gitrank/tui/app.py`, `tests/test_cli.py`
- Typer 参数: --topic, --since, --range, --sort, --limit, --refresh
- 日期格式验证，GITHUB_TOKEN 检测与警告
- CLI 直通模式：参数预设 SearchState，跳过向导直接搜索

### Task 12: 集成验证与收尾
- 运行全部单元测试确认通过
- 验证 GITHUB_TOKEN 检测、help 输出、缓存目录创建、--refresh + star_history
- 最终 commit

## Spec Coverage

All 5 capability specs (repo-fetch, repo-ranking, topic-filter, time-window, tui-app) fully covered across the 12 tasks.
