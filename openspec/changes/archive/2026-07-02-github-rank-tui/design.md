## Context

项目从零开始。用户需要一款 Python TUI 工具来按时间窗口和话题浏览 GitHub 仓库排名，数据通过 GitHub API 获取并缓存到本地 SQLite。仓库规模控制在数万活跃仓库级别，无需分布式或外部数据库。

## Goals / Non-Goals

**Goals:**
- 交互式终端界面：菜单导航、表格浏览、详情查看、随时退出
- 从 GitHub API 拉取仓库元数据并本地缓存（SQLite）
- 支持双模式排名：纯 star 数和加权复合分
- 支持按 topic 筛选、按时间窗口过滤
- 优雅处理 GitHub API 限速

**Non-Goals:**
- Web UI、Dashboard、定期报表
- 智能推荐 / AI 分析
- 全量仓库索引
- 多用户 / 认证

## Decisions

### 1. TUI 框架：Textual

选择 [Textual](https://textual.textualize.io/) 而非 Rich + prompt-toolkit 手拼。

| 考量 | Textual | Rich (仅格式化) |
|------|---------|-----------------|
| 组件化 UI | ✅ ListView, DataTable, Input | ❌ 需手写 |
| 键盘导航 | ✅ 内置 focus/app 系统 | ❌ 需手写事件循环 |
| 异步支持 | ✅ async/await 原生 | ❌ |
| 开发生态 | ✅ CSS 布局、主题 | ❌ |
| 学习曲线 | 中等 | 低 |

Textual 是 Rich 的姊妹项目，天然兼容 Rich 的渲染输出。对于我们的交互需求（菜单→列表→详情→返回），Textual 的 `Screen` 栈机制天然匹配。

### 2. HTTP 客户端：httpx

选择 `httpx`。Textual 框架本身是异步的，`httpx` 支持 `async/await`，不会阻塞 UI。备选方案 `requests` 在异步上下文中会阻塞事件循环。

### 3. 项目结构

```
github-rank-tui/
├── gitrank/
│   ├── __init__.py
│   ├── main.py              # CLI 入口 (Typer) + Textual 启动
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py           # Textual App 基座
│   │   ├── screens/
│   │   │   ├── main_menu.py # 主菜单：Search / Filter / Quit
│   │   │   ├── search.py    # 搜索参数输入（topic, since, sort）
│   │   │   └── results.py   # 结果表格 + 仓库详情
│   │   └── widgets/
│   │       ├── repo_table.py   # 排名表格组件
│   │       └── repo_detail.py  # 仓库详情卡片
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py       # GitHub API 客户端（httpx, 限速感知）
│   │   └── models.py       # 仓库数据模型（dataclass / Pydantic）
│   ├── cache/
│   │   ├── __init__.py
│   │   └── db.py           # SQLite 操作（建表、查询、插入、增量更新）
│   └── rank/
│       ├── __init__.py
│       └── engine.py       # 排名引擎：stars / composite 两种算法
├── tests/
├── pyproject.toml
└── README.md
```

### 4. SQLite 数据模型

```sql
CREATE TABLE IF NOT EXISTS repositories (
    id              INTEGER PRIMARY KEY,
    github_id       INTEGER UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,              -- "owner/repo"
    description     TEXT,
    language        TEXT,
    topics          TEXT,                       -- JSON array as string
    stargazers_count INTEGER NOT NULL DEFAULT 0,
    forks_count     INTEGER NOT NULL DEFAULT 0,
    open_issues_count INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,              -- ISO 8601
    updated_at      TEXT NOT NULL,
    pushed_at       TEXT NOT NULL,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now')),
    -- 历史快照表，支持增速计算
    UNIQUE(github_id)
);

CREATE TABLE IF NOT EXISTS star_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id       INTEGER NOT NULL,
    stargazers_count INTEGER NOT NULL,
    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (github_id) REFERENCES repositories(github_id)
);
```

两张表的设计原因：`star_history` 存储历史快照，支持增速计算。首次抓取时同时写入 `repositories` 和 `star_history`；后续更新时比较 `stargazers_count` 变化。

### 5. 复合排名公式

```
composite_score = 0.50 × S_star + 0.30 × S_growth + 0.20 × S_activity
```

各项定义与归一化：

| 因子 | 原始值 | 归一化方式 | 权重 |
|------|--------|-----------|------|
| **S_star** | 总 star 数 | `log10(stars + 1) / log10(max_stars_in_result + 1)` | 0.50 |
| **S_growth** | 月均新增 star | `log10(new_stars_per_month + 1) / log10(max_growth + 1)` | 0.30 |
| **S_activity** | 最近 commit 距今 | `1 - (days_since_last_push / window_days)`，clamp 到 [0, 1] | 0.20 |

- Star 使用对数归一化：防止 1 个 10 万 star 仓库淹没所有 5000 star 仓库
- Growth 使用月均增长：消除窗口长度不同的影响
- Activity 使用线性衰减：越久未更新，得分越低；30 天未更新归零

### 6. API 策略与限速处理

**入口策略**：使用 GitHub Search API `GET /search/repositories`，按 `topic` + `created` 日期范围搜索，按 `stars` 或 `updated` 排序。

**限速处理**：
- 依赖 `GITHUB_TOKEN` 环境变量进行认证（5000 req/h）
- `httpx` 拦截器检测 `X-RateLimit-Remaining`，剩余 < 50 时切换到保守模式（每次请求间隔 ≥ 1s）
- 触发 403 限速时，解析 `X-RateLimit-Reset` 头，在 UI 中显示倒计时
- 未设置 token 时运行时警告，使用未认证限速（60 req/h）

**增量更新**：
- 首次查询：按条件拉取全部结果并写入缓存
- 重复相同查询：直接从缓存返回
- 新增 `--refresh` 选项：强制重新拉取，更新 `star_history` 记录

### 7. TUI 屏幕流转

```
                    ┌──────────┐
                    │ MainMenu │  ← 启动
                    │ Screen   │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        Search     Filter      Quit
              │          │
              ▼          ▼
         ┌─────────┐  ┌──────────┐
         │ Param   │  │ Filter   │
         │ Input   │  │ Settings │
         └────┬─────┘  └──────────┘
              │
              ▼
         ┌─────────┐
         │ Results │  ← DataTable + Detail Panel
         │ Screen   │
         └─────────┘
              │
         Enter on row → 展开 Detail
         q / Esc     → 返回 MainMenu
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| **GitHub Search API 只返回前 1000 条结果** | 按时间分段查询（如每月一次），merge 结果 |
| **首次冷启动数据量较大** | 显示进度条（Textual ProgressBar），明确告知用户"正在首次拉取数据…" |
| **Textual 在 Windows Terminal 上可能有渲染问题** | 项目初期验证 Windows Terminal 兼容性，必要时 fallback 到 Rich 表格的非交互模式 |
| **star_history 长期膨胀** | 定期清理：保留最近 12 个月的月度快照，更早的仅保留季度快照 |
| **GitHub topic 不是正式分类** | topic 是用户自标注的，可能不准确；在 UI 中提示"按 GitHub topic 筛选，结果可能有噪音" |

## Open Questions

以下留待 build 阶段验证：

1. Search API 的 `created` 日期过滤精度是否足够？是否需要用 `pushed` + `stars` 辅助过滤？
2. 增长率计算依赖历史快照——需要几次快照才能输出有意义的增速？（初步设定：至少 2 次快照，间隔 ≥ 7 天）
3. Windows Terminal 上 Textual 的 DataTable 渲染是否正常？需实测。
