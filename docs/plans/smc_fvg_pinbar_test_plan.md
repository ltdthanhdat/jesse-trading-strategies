# SMC_FVG_PinBar Test Plan

Mục tiêu: kiểm tra 2 hướng chỉnh logic của `SMC_FVG_PinBar` mà không trộn scope.

Nguyên tắc:
- Test từng hướng một.
- Mỗi lần chỉ đổi 1 nhóm logic.
- Giữ nguyên dataset, exchange, timeframe khi so sánh.
- Ghi lại kết quả theo cùng một format để so ngang được.

Baseline hiện tại:
- Strategy: `SMC_FVG_PinBar`
- Exchange: `Binance Perpetual Futures`
- Symbol: `BTC-USDT`
- Timeframe: `1h`
- Dataset cache đang có:
  - `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- Kết quả hiện tại với code mới:
  - không có `FVG_LOOKBACK`
  - rule entry hiện tại là `overlap FVG`
  - `warm_up_candles = 0`
  - `3 trades`

## Plan 1: Sweep `FVG_LOOKBACK`

Trạng thái:
- done
- kết luận: không giữ `FVG_LOOKBACK` vì lệch Pine

Mục tiêu:
- Xác định `FVG_LOOKBACK` bao nhiêu thì strategy bắt đầu có trade.
- Xem trade xuất hiện có phải chỉ là trade quá cũ hay không.

Giả thuyết:
- Trade cũ trong debug note chỉ tồn tại khi cho phép FVG sống quá lâu.
- Nếu `FVG_LOOKBACK` nhỏ nhưng vẫn có trade, logic này vẫn còn giá trị.
- Nếu chỉ khi `FVG_LOOKBACK` rất lớn mới có trade, rule này đang quá chặt hoặc lệch ý tưởng setup.

Biến test:
- `FVG_LOOKBACK`: `20`, `30`, `50`, `80`, `120`, `240`, `99999`

Giữ nguyên:
- `warm_up_candles = 0`
- Logic pin bar hiện tại
- Logic containment hiện tại:
  - `low >= fvg.bottom`
  - `high <= fvg.top`

Ghi chú:
- plan này phản ánh hướng test cũ trước khi strategy quay về logic gần Pine hơn

Cần ghi lại cho mỗi lần chạy:
- `FVG_LOOKBACK`
- `trades_count`
- `net_profit_percentage`
- `max_drawdown`
- `win_rate`
- nếu có trade:
  - `type`
  - `entry_price`
  - `exit_price`
  - `opened_at`
  - FVG age tại lúc vào lệnh

Tiêu chí đọc kết quả:
- Nếu chỉ `99999` mới có trade:
  - setup hiện tại phụ thuộc FVG stale
- Nếu nhóm `50-120` bắt đầu có trade:
  - có thể chọn vùng lookback hợp lý hơn
- Nếu `20-240` đều không có trade:
  - vấn đề chính không nằm ở tuổi FVG

Kết luận cần chốt sau Plan 1:
- Giữ `FVG_LOOKBACK = 20`
- Tăng `FVG_LOOKBACK`
- Hoặc giữ lookback chặt và chuyển sang Plan 2

## Plan 2: Nới rule “Pin Bar trong FVG”

Trạng thái:
- done
- variant thắng: `overlap FVG`

Mục tiêu:
- Kiểm tra xem entry mất đi vì rule containment quá chặt hay không.

Giả thuyết:
- Rule hiện tại yêu cầu toàn bộ candle nằm trong FVG là quá hẹp.
- Setup thật có thể xuất hiện nếu chỉ cần body nằm trong FVG, hoặc close nằm trong FVG.

Giữ nguyên:
- không có `FVG_LOOKBACK`
- `warm_up_candles = 0`
- Pin bar detection hiện tại

Test theo thứ tự này:

### Variant A: Body nằm trong FVG

Rule:
- bullish:
  - `min(open, close) >= fvg.bottom`
  - `max(open, close) <= fvg.top`
- bearish:
  - dùng cùng rule body nằm trong biên FVG

Mục tiêu:
- nới điều kiện nhưng vẫn giữ candle body thật sự phản ứng trong gap

### Variant B: Close nằm trong FVG và wick chạm FVG

Rule gợi ý:
- bullish:
  - `close` nằm trong `[fvg.bottom, fvg.top]`
  - `low <= fvg.top`
- bearish:
  - `close` nằm trong `[fvg.bottom, fvg.top]`
  - `high >= fvg.bottom`

Mục tiêu:
- cho phép rejection wick xuyên ra ngoài một phần

### Variant C: Candle overlap FVG

Rule:
- candle overlap nếu:
  - `high >= fvg.bottom`
  - `low <= fvg.top`

Mục tiêu:
- đây là variant nới nhất
- chỉ dùng để đo sensitivity, không mặc định coi là rule cuối

Cần ghi lại cho mỗi variant:
- `variant_name`
- `trades_count`
- `net_profit_percentage`
- `max_drawdown`
- `win_rate`
- số lượng pin bar thỏa variant
- số lượng entry thực sự được khớp lệnh

Tiêu chí đọc kết quả:
- Nếu Variant A có trade còn B/C tăng quá mạnh:
  - ưu tiên A
- Nếu chỉ Variant C mới có trade:
  - rule có thể đang bị nới quá tay
- Nếu cả A/B/C vẫn `0 trade`:
  - vấn đề có thể nằm ở pin bar detection hoặc candle alignment

Kết luận cần chốt sau Plan 2:
- Chọn variant nào để implement thật
- Hoặc dừng ở đây và chuyển sang test pin bar logic

Kết luận đã chốt:
- chọn `overlap FVG`
- bước tiếp theo là test pin bar detection

## Thứ tự chạy đề xuất

1. Chạy Plan 1 trước.
   - verify: có xác định được trade phụ thuộc stale FVG hay không
2. Nếu Plan 1 không ra vùng lookback hợp lý:
   - chạy Plan 2 với `FVG_LOOKBACK = 20`
   - verify: có variant containment nào tạo setup hợp lệ không
3. Chỉ sau khi chốt 1 trong 2 hướng mới sửa code chính thức.
   - verify: backtest lại baseline và lưu kết quả mới vào `docs/notes/smc_fvg_pinbar_notes.md`

## Format log kết quả

Gợi ý format để ghi lại mỗi lần test:

```text
Test:
- plan: 1
- parameter: FVG_LOOKBACK=50

Result:
- trades_count:
- net_profit_percentage:
- max_drawdown:
- win_rate:
- notes:
```

```text
Test:
- plan: 2
- variant: body_in_fvg

Result:
- trades_count:
- net_profit_percentage:
- max_drawdown:
- win_rate:
- notes:
```
