# SMC_FVG_PinBar Notes

Ngày cập nhật: 2026-05-13

## Mục tiêu

Lưu lại debug history và các phát hiện kỹ thuật của strategy `strategies/SMC_FVG_PinBar/__init__.py`.

## Những lỗi đã tìm thấy và đã sửa

### 1. Đọc candle sai cột

Ban đầu strategy đọc candle như thể:

- `candle[0] = open`
- `candle[1] = close`
- `candle[2] = high`
- `candle[3] = low`

Nhưng trong Jesse format thực là:

- `candle[0] = timestamp`
- `candle[1] = open`
- `candle[2] = close`
- `candle[3] = high`
- `candle[4] = low`
- `candle[5] = volume`

Đã sửa toàn bộ phần FVG detection, mitigation, pin bar để dùng đúng format này.

### 2. `_get_candle(0)` trả sai bar

Bug lớn nhất ở logic entry:

- `_get_candle(0)` từng trả `self.candles[0]`
- nghĩa là lấy cây nến đầu tiên trong history hiện có
- thay vì cây nến hiện tại

Hệ quả:

- `_is_pin_bar()` gần như luôn check sai candle
- `should_long()` và `should_short()` không phát tín hiệu đúng

Đã sửa để:

- `offset=0` map sang current candle
- guard check trong `_get_candle()` cũng đã sửa lại để không trả `None` sai khi chỉ có 1 candle

### 3. Backtest quá chậm

Ban đầu strategy timeout rất nặng vì:

- `_get_all_fvgs()` scan từ đầu tới hiện tại
- hàm này bị gọi lặp lại trong:
  - `should_long()`
  - `should_short()`
  - `go_long()`
  - `go_short()`
  - `update_position()`
  - `after()`

Đã refactor sang state incremental trong `self.vars["fvg_state"]`:

- `active_bullish`
- `active_bearish`
- `recent_fvgs`
- `signal_bullish_fvg`
- `signal_bearish_fvg`
- `last_candle_ts`

Và thêm `_refresh_fvg_state()` để chỉ update 1 lần mỗi candle.

### 4. FVG lifecycle lệch Pine

Trước đó strategy có thêm rule riêng:

- FVG chỉ còn hiệu lực trong `FVG_LOOKBACK` nến

Nhưng Pine template trong:

- `docs/reference/pine-template/script.pine`

không hề có expiry theo số nến.

Pine chỉ:

- tạo FVG khi có gap
- giữ FVG active cho tới khi bị fill hoàn toàn
- có thể đánh dấu mitigated một phần
- giới hạn số box để hiển thị, nhưng đó là logic UI chứ không phải logic entry

Đã sửa lại cho bám Pine hơn:

- bỏ hoàn toàn `FVG_LOOKBACK`
- active FVG chỉ bị remove khi bị mitigated hoàn toàn

### 5. Entry rule “pin bar trong FVG” quá chặt

Sau khi bỏ `FVG_LOOKBACK`, strategy vẫn chỉ có `1 trade` trên dataset baseline.

Đã sweep 4 variant entry:

- full candle in FVG
- body in FVG
- close in FVG + wick touch
- overlap FVG

Kết quả:

- 3 variant đầu không khác baseline
- chỉ variant `overlap FVG` làm tăng số trade thật

Đã sửa rule entry từ:

- `low >= fvg.bottom` và `high <= fvg.top`

sang:

- `high >= fvg.bottom` và `low <= fvg.top`

Tức là chỉ cần candle overlap với FVG.

## Hiệu năng sau khi sửa

Backtest offline trên cache pickle:

- trước khi fix hiệu năng:
  - 12 giờ timeout `30s`
  - 3 ngày timeout `90s`
- sau khi fix:
  - 12 giờ khoảng `0.05s`
  - 3 ngày khoảng `0.15s`
  - full dataset cache khoảng `2.0s`

## Kết quả research

Kết quả backtest và sweep đã được tách ra riêng:

- `docs/research/smc_fvg_pinbar_backtest_results.md`

Kết luận working state hiện tại được tách riêng:

- `docs/state/smc_fvg_pinbar_state.md`

## Update research mới

Đã test thêm hướng:

- bỏ hẳn pin bar để dùng `trend_body`
- nới `pin bar` thành `loose_pin_bar`
- union nhiều type:
  - `loose_pin_bar OR trend_body`
  - `current pin bar OR trend_body`

Kết luận nhanh:

- `loose_pin_bar`: quá noisy, bỏ
- `trend_body`: có mở thêm vài window có trade, nhưng drawdown xấu hơn baseline nhiều, chưa giữ
- union type: coverage tăng mạnh nhưng drawdown degrade rõ

Tức là:

- vấn đề đúng là không chỉ nằm ở chuyện pin bar quá chặt
- khi mở entry rộng hơn, strategy nhận thêm nhiều trade rác
- baseline `pin bar` hiện tại vẫn sạch nhất trong các variant đã test

Script đã thêm để chạy sweep:

- `scripts/sweep_smc_fvg_pinbar_signal_variants.py`
- `scripts/sweep_smc_fvg_pinbar_entry_signal_filters.py`

Update mới nhất:

- winner đã chốt cho phase entry signal:
  - `pin_bar OR trend_body_wick_reclaim`
- refinement quanh winner:
  - thêm freshness filter không giúp
  - thêm body cap làm mất lợi thế mới
- strategy thật đã patch theo winner và verify lại trên cache windows

## Phát hiện quan trọng về alignment

Trong lúc debug có thấy behavior như sau:

- khi có warmup, timestamp của candle `1h` trong engine có thể lệch phase so với cách aggregate tay ban đầu
- điều này làm setup FVG + pin bar biến mất hoàn toàn

Vì thế ở trạng thái hiện tại, strategy phụ thuộc mạnh vào cách Jesse bucket nến `1h`.

## Những gì đã kiểm tra trong quá trình debug

Đã kiểm tra:

- số lượng FVG trên dataset
- số lượng pin bar bullish / bearish
- số lượng pin bar nằm trong active FVG
- monkey-patch `should_long()`, `should_short()`, `go_long()`, `go_short()` để xem engine có phát tín hiệu thật không
- soi trực tiếp candle runtime của Jesse để xác nhận bug `_get_candle(0)`

## Nơi xem kết luận hiện tại

- current conclusion / open questions / next step:
  - `docs/state/smc_fvg_pinbar_state.md`
- raw metrics và experiment log:
  - `docs/research/smc_fvg_pinbar_backtest_results.md`

## Lưu ý

Nếu quay lại debug tiếp, nên bắt đầu từ:

- backtest `warm_up_candles = 0` với rule `overlap FVG`
- sau đó test robustness trên:
  - `warm_up_candles`
  - dataset dài hơn
  - nếu cần, pin bar detection variants
