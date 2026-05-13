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
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.6666666666666666`

## What is settled

- bug đọc candle và bug `_get_candle(0)` đã sửa
- strategy đã chạy nhanh hơn nhiều nhờ incremental FVG state
- issue `warm_up_candles` đã giảm mạnh trên baseline
- `overlap FVG` tốt hơn các containment variant cũ
- `pin bar` hiện tại vẫn là signal sạch nhất trong các variant đã test

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

## Current interpretation

- vấn đề không chỉ là `pin bar` quá chặt
- mở entry rộng hơn hiện tại sẽ kéo thêm nhiều trade rác
- baseline hiện tại ít trade nhưng sạch hơn các variant candle đã thử

## Open questions

- có filter nhỏ nào giúp `trend_body` bớt noisy không
- strategy còn nhạy tới mức nào với candle alignment / resample phase
- `overlap FVG` có giữ chất lượng khi mở rộng dataset hơn nữa không

## Next recommended step

1. Nếu test tiếp entry signal:
   - không mở pin bar thô nữa
   - thử `trend_body` kèm một filter nhỏ
2. Nếu test robustness:
   - mở rộng thêm dataset / market windows
3. Chỉ patch `strategies/SMC_FVG_PinBar/__init__.py` khi có variant thắng rõ

## Related files

- `docs/research/smc_fvg_pinbar_backtest_results.md`
- `docs/notes/smc_fvg_pinbar_notes.md`
- `docs/plans/smc_fvg_pinbar_autoresearch_plan.md`
