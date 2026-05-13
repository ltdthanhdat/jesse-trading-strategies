# SMC_FVG_PinBar Current State

Ngày cập nhật: 2026-05-13

Mục đích:
- lưu kết luận working state hiện tại
- đọc nhanh trước khi tiếp tục research
- không trộn với log backtest chi tiết

## Current strategy state

- FVG lifecycle đã bám Pine hơn:
  - không có `FVG_LOOKBACK`
  - FVG chỉ bị remove khi mitigated hoàn toàn
- Entry containment đã chốt:
  - `overlap FVG`
  - `high >= fvg.bottom`
  - `low <= fvg.top`
- Entry signal hiện tại:
  - `pin_bar`
  - hoặc `trend_body` nhưng phải có `wick reclaim` trong FVG
- Không đổi trong phase hiện tại:
  - stop loss
  - take profit
  - qty logic

## Baseline đang dùng

- dataset:
  - `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- setup:
  - exchange: `Binance Perpetual Futures`
  - symbol: `BTC-USDT`
  - timeframe: `1h`
  - `warm_up_candles = 0`
- result:
  - `trades_count = 4`
  - `net_profit_percentage = 0.73935024987001`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.75`

## What is settled

- bug đọc candle và bug `_get_candle(0)` đã sửa
- strategy đã chạy nhanh hơn nhiều nhờ incremental FVG state
- issue `warm_up_candles` đã giảm mạnh trên baseline
- `overlap FVG` tốt hơn các containment variant cũ
- phase entry signal đã chốt:
  - `pin_bar OR trend_body_wick_reclaim`

## What was tested and discarded

- `loose_pin_bar`
  - tăng trade mạnh
  - quality xấu rõ
- `trend_body`
  - mở thêm window có trade
  - drawdown xấu hơn baseline nhiều
- `loose_pin_bar OR trend_body`
  - coverage cao
  - trade rác nhiều
- `current pin bar OR trend_body`
  - sạch hơn union trên
  - vẫn drawdown xấu hơn baseline quá nhiều
- `trend_body` variants khác
  - có tăng trade hoặc coverage
  - nhưng không giữ được quality tốt bằng variant đã chọn

## Current interpretation

- vấn đề đúng là không chỉ nằm ở `pin bar` quá chặt
- thêm `trend_body` chỉ hợp lý khi có `wick reclaim` để tránh momentum trade rác
- entry logic hiện tại tốt hơn baseline cũ mà không làm drawdown baseline xấu thêm

## Open questions

- strategy còn nhạy tới mức nào với candle alignment / resample phase
- entry logic mới có giữ chất lượng khi mở rộng dataset hơn nữa không

## Next recommended step

1. Test robustness của entry logic mới trên thêm dataset / market windows
2. Kiểm tra sensitivity với candle alignment / resample phase
3. Không mở rộng entry signal thêm nữa trừ khi quality mới tốt hơn rõ ràng

## Related files

- `docs/research/smc_fvg_pinbar_backtest_results.md`
- `docs/notes/smc_fvg_pinbar_notes.md`
- `docs/plans/smc_fvg_pinbar_autoresearch_plan.md`
