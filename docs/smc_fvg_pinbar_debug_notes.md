# SMC_FVG_PinBar Debug Notes

Ngày cập nhật: 2026-05-13

## Mục tiêu

Lưu lại trạng thái debug hiện tại của strategy `strategies/SMC_FVG_PinBar/__init__.py` để lần sau tiếp tục nhanh.

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

- `docs/_templates/pine-template/script.pine`

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

## Cách backtest đã dùng

Do DB local hiện không có đầy đủ candle usable cho lần debug này, backtest được chạy từ cache pickle trong:

- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `storage/temp/1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`

Exchange dùng trong research backtest:

- `Binance Perpetual Futures`

Timeframe route:

- `1h`

## Kết quả backtest hiện tại

### Với `warm_up_candles = 0`

Full dataset cache:

- `elapsed_seconds ~= 2.04`
- `total = 3`
- `win_rate = 0.6666666666666666`
- `net_profit_percentage = 0.6683005700192093`
- `max_drawdown = -0.13520595720001305`
- `sharpe_ratio = 2.1102751027736897`
- `calmar_ratio = 30.072885907390187`
- `trades_count = 3`

Các trade:

1. `short`
- entry: `43950.0`
- exit: `42839.0`
- qty: `0.056814`
- pnl: `61.148021901600416`

2. `long`
- entry: `42767.8`
- exit: `43021.9`
- pnl: `12.910558777040343`

3. `long`
- entry: `47337.2`
- exit: `47239.0`
- pnl: `-7.2285236767198455`

### Sweep entry variants

Baseline dataset:

- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Kết quả:

- `baseline_full_candle`
  - `trades_count = 1`
  - `net_profit_percentage = 0.6114802190160041`
- `body_in_fvg`
  - `trades_count = 1`
  - `net_profit_percentage = 0.6114802190160041`
- `close_in_fvg_with_wick_touch`
  - `trades_count = 1`
  - `net_profit_percentage = 0.6114802190160041`
- `overlap_fvg`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`

### Sweep `warm_up_candles`

Kết quả:

- `warm_up_candles = 0`
  - có `3 trade`
- `warm_up_candles = 24`
  - có `3 trade`
- `warm_up_candles = 60`
  - có `3 trade`
- `warm_up_candles = 120`
  - có `3 trade`
- `warm_up_candles = 240`
  - có `3 trade`

Kết luận mới:

- sau khi bỏ `FVG_LOOKBACK` và đổi sang `overlap FVG`
- strategy không còn nhạy với `warm_up_candles` trên baseline dataset này nữa

### Sweep qua các cache window khác

Kết quả nhanh:

- `1703689200000-1704067140000...`
  - `0 trade`
- `1703878200000-1704067140000...`
  - `0 trade`
- `1704067200000-1709337540000...`
  - `3 trade`
- `1740495600000-1740873540000...`
  - `0 trade`
- `1740873600000-1740959940000...`
  - `0 trade`
- `1740873600000-1741046340000...`
  - `0 trade`
- `1748617200000-1748995140000...`
  - `0 trade`

Kết luận:

- rule mới robust hơn theo `warm_up_candles`
- nhưng trade frequency vẫn thấp trên nhiều market window khác
- vấn đề còn lại có khả năng nằm ở pin bar detection hoặc bản chất setup quá hiếm

## Kết luận hiện tại

Strategy hiện:

- đã chạy nhanh
- đã có thể phát sinh trade thật
- đã bám Pine hơn ở phần lifecycle của FVG
- entry rule đã được nới sang `overlap FVG`
- không còn nhạy với `warm_up_candles` trên baseline
- nhưng vẫn có trade frequency thấp trên nhiều window khác

Nói ngắn gọn:

- vấn đề tốc độ: đã xử lý
- vấn đề logic còn lại:
  - trade frequency vẫn thấp
  - cần kiểm tra tiếp pin bar detection
  - cần kiểm tra thêm liệu `overlap FVG` có giữ chất lượng khi mở rộng dataset hay không

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

## Việc nên làm tiếp theo

Ưu tiên cao:

1. Làm strategy bớt nhạy với alignment
2. Test tiếp pin bar detection
3. Mở rộng backtest dataset để xem `overlap FVG` có còn ổn không

Ưu tiên phụ:

4. Tạo script backtest riêng để sweep:

- `warm_up_candles`
- timeframe
- rule entry variant

5. Nếu tiếp tục dùng `1h`, cần xác định rõ Jesse đang resample candle theo phase nào trong từng mode/backtest setup.

## Lưu ý

File strategy hiện đã có thay đổi local chưa commit:

- `strategies/SMC_FVG_PinBar/__init__.py`

Nếu quay lại debug tiếp, nên bắt đầu từ:

- backtest `warm_up_candles = 0` với rule `overlap FVG`
- sau đó test robustness trên:
  - `warm_up_candles`
  - dataset dài hơn
  - nếu cần, pin bar detection variants
