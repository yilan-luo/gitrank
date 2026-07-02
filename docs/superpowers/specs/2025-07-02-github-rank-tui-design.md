---
comet_change: github-rank-tui
role: technical-design
canonical_spec: openspec
---

# github-rank-tui 技术设计

## 1. 概述

`github-rank-tui` 是一个 Python 终端交互工具（TUI），解决 GitHub Trending 只能回溯约一个月的问题。用户按话题和时间窗口搜索仓库，获得 star 数或加权综合分的排名结果。

## 2. 技术栈

| 技术 | 用途 | 选型理由 |
|------|------|---------|
| **Textual** | TUI 框架 | 组件化 Screen 栈匹配向导式输入，内置 DataTable/ListView，CSS 布局 |
| **httpx** | HTTP 客户端 | 异步原生，不阻塞 Textual 事件循环 |
| **Typer** | CLI 入口 | 参数解析 + Textual App 启动 |
| **Pydantic** | 数据模型 | 类型安全，API 响应反序列化 |
| **SQLite** (标准库) | 本地缓存 | 零配置，数万仓库完全够用 |
| **pytest + respx** | 测试 | 单元测试 + HTTP mock |

## 3. 架构

```
                        ┌──────────────────┐
                        │    用户终端       │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │   CLI 入口        │
                        │   (Typer)         │
                        │   + Textual App   │
                        └────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  TUI 层   │      │ Settings │      │  CLI 直通 │
        │ 向导式搜索│      │ ~/.gitrank│      │ --topic   │
        │ 结果表格  │      │ /config  │      │ --since   │
        │ 详情卡片  │      │  .json   │      │ --sort    │
        └────┬─────┘      └──────────┘      └──────────┘
             │
             ▼
        ┌──────────────────────────────────┐
        │          查询编排层               │
        │    (将 TUI 参数 → 缓存查询        │
        │     / API 拉取 → 排名计算)        │
        └────┬─────────┬──────────┬────────┘
             │         │          │
        ┌────▼──┐ ┌───▼────┐ ┌───▼─────┐
        │ API   │ │ Cache  │ │ Rank    │
        │ 客户端 │ │ SQLite │ │ 引擎    │
        │       │ │        │ │         │
        │ 自适应 │ │ repos  │ │ stars   │
        │ 时间切片│ │ +star  │ │ +compos │
        │ 限速感知│ │ _hist  │ │ ite     │
        └───────┘ └────────┘ └─────────┘
```

### 3.1 模块职责

| 模块 | 路径 | 职责 |
|------|------|------|
| `gitrank.main` | `gitrank/main.py` | CLI 入口：Typer 参数解析 → 启动 Textual App |
| `gitrank.tui.app` | `gitrank/tui/app.py` | Textual App 基座：全局按键绑定、CSS 主题 |
| `gitrank.tui.screens.main_menu` | `gitrank/tui/screens/main_menu.py` | 主菜单：Search / Settings / Quit |
| `gitrank.tui.screens.search` | `gitrank/tui/screens/search.py` | 向导式搜索：Step1(Topic) → Step2(Time) → Step3(Sort) |
| `gitrank.tui.screens.results` | `gitrank/tui/screens/results.py` | 结果表格 + 仓库详情 |
| `gitrank.tui.widgets.repo_table` | `gitrank/tui/widgets/repo_table.py` | DataTable 排名表格 |
| `gitrank.tui.widgets.repo_detail` | `gitrank/tui/widgets/repo_detail.py` | 仓库详情卡片 |
| `gitrank.api.client` | `gitrank/api/client.py` | GitHub API：搜索、分页、限速感知、自适应切片 |
| `gitrank.api.models` | `gitrank/api/models.py` | Pydantic 模型：Repository, StarSnapshot |
| `gitrank.cache.db` | `gitrank/cache/db.py` | SQLite：建表、CRUD、缓存命中、star_history |
| `gitrank.rank.engine` | `gitrank/rank/engine.py` | 排名引擎：stars 排序、composite 加权分 |

## 4. 核心设计决策

### 4.1 向导式搜索（Screen 栈）

搜索分为 3 个独立 Screen，用户通过 Enter 前进、Esc 回退：

```
MainMenu → SearchStep1(Topic) → SearchStep2(Time) → SearchStep3(Sort) → Results
              ◀──── Esc ────      ◀──── Esc ────      ◀──── Esc ────
```

每个 Step 退出时状态保留在 `SearchState` 对象中，下次进入时恢复。确认搜索后 `SearchState` 传递给查询编排层。

### 4.2 自适应时间切片

GitHub Search API 最多返回 1000 条。为保证数据完整：

```
fetch_window(start, end, topic):
    1. 查询 Search API，合并分页
    2. 如果 total_count ≤ 1000 → 返回全部
    3. 如果 total_count > 1000 且 (end - start) > 1 day:
       → 对半拆分为两个子窗口
       → 递归调用 fetch_window(start, mid) + fetch_window(mid, end)
       → 合并去重
    4. 如果窗口 < 1 天 → 接受截断，取前 1000
```

停止条件：

| 条件 | 行为 |
|------|------|
| `total_count ≤ 1000` | 停止拆分，返回 |
| 窗口长度 < 1 天 | 停止，取前 1000 |
| 最大递归深度 10 | 停止，取前 1000 |

### 4.3 复合排名公式

```
composite_score = 0.50 × S_star + 0.30 × S_growth + 0.20 × S_activity
```

各项归一化到 [0, 1]：

| 因子 | 含义 | 计算 |
|------|------|------|
| **S_star** | 总热度 | `log10(stars + 1) / log10(max_stars_in_result + 1)` |
| **S_growth** | 月均增长 | 有历史快照：`log10(new_stars_per_month + 1) / log10(max_growth + 1)`；冷启动默认 0.5 |
| **S_activity** | 维护活跃度 | `1 - (days_since_last_push / window_days)`，clamp [0, 1] |

### 4.4 Settings（默认偏好）

```
~/.gitrank/
├── config.json        # 默认 topic, time_window, sort
└── cache.db           # SQLite 缓存
```

Settings 屏幕修改默认值 → Search 时自动填入，用户可在向导中覆盖。

### 4.5 API 限速处理

- 检测 `X-RateLimit-Remaining`：< 50 → 请求间隔 ≥ 1s
- 403 触发：解析 `X-RateLimit-Reset`，UI 显示倒计时
- 未设置 `GITHUB_TOKEN`：启动时警告，使用 60 req/h 非认证限速

## 5. 数据模型

### SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS repositories (
    id                INTEGER PRIMARY KEY,
    github_id         INTEGER UNIQUE NOT NULL,
    full_name         TEXT NOT NULL,
    description       TEXT,
    language          TEXT,
    topics            TEXT,
    stargazers_count  INTEGER NOT NULL DEFAULT 0,
    forks_count       INTEGER NOT NULL DEFAULT 0,
    open_issues_count INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    pushed_at         TEXT NOT NULL,
    fetched_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS star_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id         INTEGER NOT NULL,
    stargazers_count  INTEGER NOT NULL,
    recorded_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (github_id) REFERENCES repositories(github_id)
);
```

### Settings Schema (`config.json`)

```json
{
  "default_topic": null,
  "default_time_window": "6m",
  "default_sort": "composite"
}
```

## 6. 测试策略

| 层 | 方式 | 工具 | 目标 |
|------|------|------|------|
| 排名引擎 | 纯单元测试 | pytest | 高覆盖率 |
| 缓存层 | 单元 + :memory: 集成 | pytest | 高覆盖率 |
| API 客户端 | Mock HTTP 响应 | pytest + respx | 覆盖正常/限速/分页场景 |
| CLI 入口 | 参数解析 | typer.testing.CliRunner | 覆盖所有参数组合 |
| TUI | 手动验证 | `textual run --dev` | 核心交互路径 |

## 7. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 热门 topic + 长时间窗口 → 大量 API 请求 | 自适应切片 + 缓存命中后零请求；进度条告知当前进度 |
| Textual Windows Terminal 兼容性 | 初期验证；必要时 fallback 到 Rich 表格非交互模式 |
| star_history 长期膨胀 | 后续版本定期清理：保留近 12 月月度快照，更早的保留季度快照 |
| GitHub Search API 按 `created` 过滤精度有限 | 本地按 `created_at` 二次过滤确保一致性 |

## 8. 开放问题

1. Search API 的 `created` 日期过滤精度是否足够？需实测验证
2. 增速计算需要至少 2 次快照间隔 ≥ 7 天才有意义——首次用户体验如何？冷启动默认 0.5 是否合理？
3. Windows Terminal 上 Textual DataTable 渲染是否正常？需实测
