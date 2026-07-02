# gitrank

GitHub repository ranking TUI tool. Discover trending repos beyond GitHub's 1-month Trending window.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Launch interactive TUI
gitrank

# CLI mode with direct parameters
gitrank --topic ai --since 2025-01-01 --sort composite --limit 20
```

## Requirements

- Python 3.11+
- Optional: `GITHUB_TOKEN` environment variable (increases API rate limit from 60 to 5000 req/h)
