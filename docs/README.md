# Docs

Nguồn sự thật cho tài liệu trong repo này.

## Cấu trúc

- `AGENTS.md`
  - rule ngắn gọn để viết tài liệu mới đúng chỗ

- `plans/`
  - kế hoạch test
  - kế hoạch tuning
  - kế hoạch refactor

- `notes/`
  - debug note
  - trạng thái hiện tại
  - bug đã sửa
  - blocker còn lại

- `research/`
  - kết quả backtest
  - sweep result
  - benchmark

- `reference/`
  - tài liệu tham chiếu ổn định hơn
  - template
  - access/setup note

## File hiện có

- `plans/smc_fvg_pinbar_test_plan.md`
  - plan test cho `SMC_FVG_PinBar`

- `plans/smc_fvg_pinbar_autoresearch_plan.md`
  - plan dùng kiểu `autoresearch` để tune entry logic

- `notes/smc_fvg_pinbar_notes.md`
  - debug note chính cho strategy `SMC_FVG_PinBar`

- `research/smc_fvg_pinbar_backtest_results.md`
  - baseline result
  - sweep entry variants
  - sweep `warm_up_candles`
  - cross-window cache results

- `reference/access.md`
  - note access / setup liên quan

- `reference/pine-template/script.pine`
  - Pine template tham chiếu cho FVG / structure

## Rule ngắn

- plan mới -> `plans/`
- debug note -> `notes/`
- kết quả test dài -> `research/`
- template / tài liệu tham chiếu -> `reference/`
