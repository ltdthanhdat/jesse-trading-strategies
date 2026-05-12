---
name: jesse-trade
description: Points to official Jesse Trade documentation sections. Use when working with Jesse, algo-trading strategies, backtesting, routes, indicators, config, or when the user mentions Jesse, jesse.trade, or docs.jesse.trade.
---

# Jesse Trade — Documentation index

Jesse is an advanced algo-trading framework in Python (self-hosted, privacy-first). Official docs: **https://docs.jesse.trade**

This skill does not duplicate docs. It maps topics to the right section so the agent can suggest links or fetch content from the URLs below.

## When to use this skill

- User asks about Jesse Trade, setup, strategies, backtesting, or configuration.
- User works in a Jesse project (e.g. `strategies/`, `routes.py`, `.env`).
- User needs API details (strategy properties, indicators, utils).
- User mentions docs.jesse.trade or wants to “check the docs”.

## Agent behavior

- For a topic below, **suggest the corresponding doc link** or use `mcp_web_fetch` with that URL to retrieve and summarize content.
- Prefer pointing to the official doc section rather than pasting long excerpts.

---

## Documentation index

### Getting started & setup

| Topic | Link |
|-------|------|
| Getting started (overview, requirements, create project, pip, run) | https://docs.jesse.trade/docs/getting-started/ |
| Docker (recommended for beginners) | https://docs.jesse.trade/docs/getting-started/docker |
| Environment setup (Windows, macOS, Ubuntu) | https://docs.jesse.trade/docs/getting-started/environment-setup |

### Project structure & config

| Topic | Link |
|-------|------|
| Configuration (.env, exchanges, webhooks, etc.) | https://docs.jesse.trade/docs/configuration.html |
| Routing (symbols, timeframes, exchanges, strategies) | https://docs.jesse.trade/docs/routes |

### Strategies & API

| Topic | Link |
|-------|------|
| Strategies API reference (properties, methods, position, orders, etc.) | https://docs.jesse.trade/docs/strategies/api.html |
| Indicators (import, usage, `candles`, `get_candles`) | https://docs.jesse.trade/docs/indicators/ |
| Indicators reference (list of indicators, matypes) | https://docs.jesse.trade/docs/indicators/reference |
| Utilities (risk_to_qty, fee_rate, timeframe helpers, etc.) | https://docs.jesse.trade/docs/utils |

### Debugging & research

| Topic | Link |
|-------|------|
| Debugging (backtest debug, paper trading, logging) | https://docs.jesse.trade/docs/debugging.html |
| Research / Jupyter | https://docs.jesse.trade/docs/research/jupyter.html |

### Home

| Topic | Link |
|-------|------|
| Docs home | https://docs.jesse.trade/ |

---

## Quick reference

- **Create project**: clone `https://github.com/jesse-ai/project-template`, then `cp .env.example .env`, configure, then `jesse run`.
- **Requirements**: Redis ≥5, PostgreSQL ≥10, Python ≥3.10 and ≤3.13, pip ≥23.
- **Run (native)**: `jesse run` (default http://0.0.0.0:9000); set `POSTGRES_HOST` and `REDIS_HOST` to `localhost` in `.env`.

For full details, always use the links above.
