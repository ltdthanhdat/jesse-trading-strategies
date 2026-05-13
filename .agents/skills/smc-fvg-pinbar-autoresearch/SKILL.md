---
name: smc-fvg-pinbar-autoresearch
description: Use when tuning the strategy strategies/SMC_FVG_PinBar with small research loops, especially for entry logic and pin bar detection. Use this when the user asks to continue the SMC_FVG_PinBar tuning work, run variant sweeps, compare backtest results, keep or discard small strategy changes, or update the related docs in docs/plans, docs/notes, and docs/research.
---

# SMC_FVG_PinBar Autoresearch

Use this skill only for iterative tuning of `strategies/SMC_FVG_PinBar/__init__.py`.

## Current source of truth

Read these first when the task is about continuing the existing tuning work:

- `docs/README.md`
- `docs/state/smc_fvg_pinbar_state.md`
- `docs/notes/smc_fvg_pinbar_notes.md`
- `docs/research/smc_fvg_pinbar_backtest_results.md`
- `docs/plans/smc_fvg_pinbar_autoresearch_plan.md`

Read `docs/plans/smc_fvg_pinbar_test_plan.md` only for historical context.

## Hard constraints

- Only change one hypothesis at a time.
- Default write scope is:
  - `strategies/SMC_FVG_PinBar/__init__.py`
  - `docs/state/smc_fvg_pinbar_state.md`
  - `docs/notes/smc_fvg_pinbar_notes.md`
  - `docs/research/smc_fvg_pinbar_backtest_results.md`
- Do not change `routes.py`, infra, Docker, DB config, or unrelated strategies.
- Do not change stop loss, take profit, qty logic, or FVG lifecycle unless the user explicitly asks.
- Current active phase is pin bar tuning. Do not retest old FVG containment ideas unless the user asks.

## Baseline assumptions

- FVG lifecycle is already aligned closer to Pine:
  - no `FVG_LOOKBACK`
  - FVG removed only when fully mitigated
- Current entry containment is already chosen:
  - overlap FVG
- Current open question:
  - is `_is_pin_bar()` too strict?

## Standard loop

1. Read the current state file first, then notes and research result files.
2. State the exact hypothesis in one short sentence.
3. Make the smallest possible code change for that hypothesis.
4. Run a comparable backtest on the same dataset first.
5. Compare against the baseline metrics.
6. Keep or discard the change explicitly.
7. Update docs:
   - state file for latest conclusion / current direction
   - research file for metrics
   - notes file for conclusion if the result changes the working direction

## Metrics to compare

Always capture at least:

- `trades_count`
- `net_profit_percentage`
- `max_drawdown`
- `win_rate`

If useful, also capture:

- sample trades
- long/short mix
- holding period

## Keep / discard rule

Do not keep a change only because it increases trade count.

Prefer keeping a change when:

- trade count improves materially
- drawdown does not degrade sharply
- net profit does not collapse
- the rule is still explainable in SMC/FVG terms

Discard a change when:

- it creates noisy trades
- drawdown worsens clearly
- it drifts away from the intended setup

## Suggested workflow for this repo

- Use `uv run python ...` for scripts and backtests.
- Prefer small sweep scripts over repeated manual edits.
- If you need a one-off comparison, monkeypatch in a script instead of immediately changing the strategy file.
- Only patch the strategy after a variant wins.

## Output discipline

When you finish a loop:

- append metrics/result to `docs/research/smc_fvg_pinbar_backtest_results.md`
- update `docs/state/smc_fvg_pinbar_state.md` with the latest conclusion

Use this compact structure:

```text
Experiment:
- hypothesis:
- file_changed:

Result:
- trades_count:
- net_profit_percentage:
- max_drawdown:
- win_rate:
- keep_or_discard:
- notes:
```
