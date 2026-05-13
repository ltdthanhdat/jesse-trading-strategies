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
  - hoặc `displacement_break` nhưng phải có `wick reclaim` trong FVG
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
- issue `warm_up_candles` không còn tái hiện trên 7 cache đã test
- `overlap FVG` tốt hơn các containment variant cũ
- phase entry signal đã chốt:
  - `pin_bar OR trend_body_wick_reclaim OR displacement_break_wick_reclaim`

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
- `displacement_break` hoạt động như một confirmation kiểu displacement-close khỏi FVG, gần hơn với cách nhiều tài liệu FVG mô tả việc chờ candle mạnh xác nhận sau khi reclaim
- entry logic hiện tại giữ nguyên baseline tốt:
  - `trades_count = 4`
  - `net_profit_percentage = 0.73935024987001`
  - `max_drawdown = -0.13520595720001305`
- winner hiện tại stable theo `warm_up_candles = 0, 24, 60, 120, 240` trên toàn bộ 7 cache
- vấn đề còn lại là market coverage vẫn hẹp:
  - trên bộ cache cũ đã test, giờ có trade ở `3/7` cache nhưng chỉ `2/7` cache là dương
  - ngay trong baseline 2 tháng cũng chỉ có trade ở `2/9` window 7 ngày
  - trên data gần đây:
    - `2026-03` có `1 trade`
    - `2026-04` có `5 trades`
    - run continuous `2026-03 -> 2026-04` còn âm nhẹ, nhưng đã đỡ hơn nhiều nhờ thêm `2` trade thắng giữa và cuối `2026-04`

## Open questions

- strategy còn nhạy tới mức nào với candle alignment / resample phase ngoài bộ cache hiện có
- `displacement_break` có phải là rule đủ general hay chỉ cứu được riêng cụm `2026-04`
- vì sao cache `1740495600000-1740873540000-...` lại sinh thêm `1 short` thua ngay khi mở rộng bằng displacement

## Next recommended step

1. Inspect trực tiếp trade thua mới ở cache `1740495600000-1740873540000-...`
2. Inspect 2 trade thắng mới ở `2026-04` để xem có thật sự là mẫu displacement tốt, lặp lại được không
3. So sánh state / active FVG / signal candle giữa:
   - `2026-04` standalone
   - `2026-03 -> 2026-04` continuous
4. Chưa union thêm signal khác nữa cho tới khi hiểu rõ trade mới tốt/xấu này

## Related files

- `docs/research/smc_fvg_pinbar_backtest_results.md`
- `docs/notes/smc_fvg_pinbar_notes.md`
- `docs/plans/smc_fvg_pinbar_autoresearch_plan.md`
