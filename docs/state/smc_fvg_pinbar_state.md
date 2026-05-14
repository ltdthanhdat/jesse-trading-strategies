# SMC_FVG_PinBar Current State

Ngày cập nhật: 2026-05-14

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
    - không bắt buộc màu nến cùng hướng trade
    - `PIN_BAR_BODY_RATIO = 0.33`
    - `PIN_BAR_WICK_TO_BODY = 2.25`
    - `PIN_BAR_CLOSE_EXTREME_RATIO = 0.30`
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
- trade thua thêm ở cache `1740495600000-1740873540000-...` đúng là trade `displacement`
- guard hẹp cho `displacement` đã test:
  - `close vẫn nằm trong FVG`
  - `FVG age >= 5`
  - `overshoot <= 0.2 * FVG height`
  - cả 3 đều loại được losing short cũ mà không làm mất 2 trade thắng mới ở `2026-04`
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
- nới nhẹ `displacement` để tăng số lệnh chưa ra winner:
  - nới `body_ratio` từ `0.6 -> 0.55` không thêm trade
  - nới `close near extreme` từ `0.2 -> 0.25` có thêm trade trên recent data
  - nhưng profit và win rate recent xấu đi rõ
- sweep `pin_bar` hẹp trên winner hiện tại:
  - `wick_to_body 1.75`
  - `close_extreme_ratio 0.30`
  - bỏ ràng buộc màu nến
  - cả 3 đều không tạo thêm trade nào
- chỉ variant `pin_bar_intent_relaxed` tạo thêm trade thật:
  - baseline `4 -> 5`
  - recent continuous `7 -> 10`
  - recent `2026-04` `5 -> 7`
  - nhưng baseline degrade rõ:
    - `net_profit_percentage 0.7393% -> 0.4100%`
    - `max_drawdown -0.1352 -> -0.3269`
    - `win_rate 0.75 -> 0.6`
- đã salvage được nhánh này bằng cách siết lại `wick/body`:
  - giữ `body_ratio = 0.33`
  - giữ `close_extreme_ratio = 0.30`
  - giữ `no_color`
  - tăng `wick_to_body` lên `2.25`
- kết quả trên 5 cache mục tiêu:
  - baseline giữ nguyên winner cũ:
    - `4 trades`
    - `0.73935024987001%`
    - `max_drawdown -0.13520595720001305`
  - recent continuous `2026-03 -> 2026-04`:
    - `7 -> 10 trades`
    - `-0.04465644600880868% -> 0.7134234949907934%`
  - recent `2026-04`:
    - `5 -> 7 trades`
    - `0.42577161733199426% -> 0.8749591917543952`
- `wick_to_body = 2.50` không cho thêm lợi ích so với `2.25`
- sweep `trend_body` refinement hẹp:
  - nới `body_ratio` xuống `0.50`
  - nới `close near extreme` lên `0.20`
  - nới `wick_reclaim` sang `touch 0.40 / close 0.60`
  - tất cả đều không đổi kết quả
- chỉ khi nới mạnh hơn sang `touch 0.45 / close 0.55` mới thêm trade:
  - recent continuous `7 -> 8`
  - recent `2026-04` `5 -> 6`
  - nhưng quality xấu đi rõ, nên loại
- đã test thêm nhánh `union thêm start trade` bằng `engulfing / reversal reclaim` trên `12 cache`:
  - `engulfing_strict`: tổng trade `30 -> 32`
  - `engulfing_close_025`: tổng trade `30 -> 35`
  - `reversal_loose`: tổng trade `30 -> 37`
  - nhưng tất cả đều làm baseline xấu đi rõ
- salvage tốt nhất của nhánh này là `engulfing_strict_fresh5`:
  - baseline `4 -> 5 trades`
  - `net_profit_percentage 0.7393% -> 0.4086%`
  - `max_drawdown -0.1352 -> -0.3283`
  - `win_rate 0.75 -> 0.6`
  - vẫn không đủ tốt để giữ
- winner hiện tại khi chạy rộng hơn trên `12 cache`:
  - có trade ở `6/12` cache
  - cả `6/12` cache có trade đều dương
  - `total_trades_all_caches = 30`

## Open questions

- strategy còn nhạy tới mức nào với candle alignment / resample phase ngoài bộ cache hiện có
- `displacement_break` có phải là rule đủ general hay chỉ cứu được riêng cụm `2026-04`
- trade short thua lớn ở recent continuous `2026-04-09 -> 2026-04-11` hiện là trade `pin_bar`, không phải `displacement`
- nếu mục tiêu tiếp tục tăng trade count, nên mở tiếp ở nhánh nào:
  - `pin_bar` đã có candidate mới tốt hơn trên bộ cache hiện tại; cần xác nhận robustness rộng hơn
  - `trend_body` hiện gần như không còn headroom khi chỉ refine hẹp
  - `engulfing / reversal` union cũng chưa ra winner
  - hay debug coverage theo regime / boundary trước

## Next recommended step

1. Không mở rộng thêm `displacement` bằng rule lỏng hơn lúc này
2. Không mở thêm union `engulfing / reversal` theo hướng hiện tại nữa
3. Nếu muốn vá quality trước:
   - patch guard `displacement close still inside FVG`
4. Nếu mục tiêu chính vẫn là tăng trade count:
   - nhánh còn đáng giữ nhất vẫn là `pin_bar` current winner
   - bước tiếp theo nên là:
     - chạy rộng hơn trên thêm windows / thêm symbol để kiểm tra robustness thật
     - hoặc inspect coverage theo regime / boundary thay vì mở thêm candle type mới
5. Song song, inspect trade short thua lớn ở recent continuous vì đây vẫn là nguồn kéo PnL xuống mạnh nhất

## Related files

- `docs/research/smc_fvg_pinbar_backtest_results.md`
- `docs/notes/smc_fvg_pinbar_notes.md`
- `docs/plans/smc_fvg_pinbar_autoresearch_plan.md`
