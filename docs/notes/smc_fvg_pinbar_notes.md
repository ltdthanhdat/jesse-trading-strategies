# SMC_FVG_PinBar Notes

Ngày cập nhật: 2026-05-14

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

Update 2026-05-13:

- có test thêm hướng lấy từ FVG docs ngoài repo:
  - chờ candle `displacement` đóng mạnh rời khỏi FVG sau khi có reclaim
  - gần ý `rejection candle / strong close / displacement confirmation`
- variant `engulfing reclaim` bị loại:
  - tăng lệnh nhưng phá baseline quá mạnh
- variant `displacement_break_wick_reclaim` được giữ tạm:
  - baseline giữ nguyên `4 trades`, profit và drawdown không xấu hơn
  - `2026-04` standalone cải thiện từ `3 trades / 0.0275%` lên `5 trades / 0.4258%`
  - `2026-03 -> 2026-04` continuous cải thiện từ `-0.4411%` lên `-0.0447%`
  - đổi lại có thêm `1` losing short ở cache `1740495600000-1740873540000-...`
- kết luận:
  - đây là union đầu tiên tăng coverage mà không làm baseline xấu đi
  - nhưng chưa thể xem là solved vì trade mới vẫn chưa sạch hoàn toàn

Update 2026-05-14:

- đã inspect lại cụm trade mới quanh `displacement`
- xác nhận:
  - losing short ở cache `1740495600000-1740873540000-...` là trade `displacement`
  - 2 trade thắng mới quan trọng trong `2026-04` vẫn giữ được khi thêm guard hẹp cho displacement
- 3 guard hẹp đã test:
  - `close vẫn nằm trong FVG`
  - `FVG age >= 5`
  - `overshoot <= 0.2 * FVG height`
- cả 3 cho ra cùng kết quả trên bộ cache đã test:
  - loại losing short cũ
  - không làm mất baseline
  - không làm mất recent winners
- nhưng đây là hướng tăng quality, không phải tăng trade count
- đã test nới nhẹ `displacement_break`:
  - `body_ratio 0.6 -> 0.55`: không thêm trade
  - `close near extreme 0.2 -> 0.25`: có thêm trade trên recent data, nhưng quality giảm rõ
- kết luận mới:
  - chưa có `displacement` variant nào vừa tăng trade count vừa giữ quality đủ tốt
  - trade short thua lớn ở recent continuous vẫn là trade `pin_bar`, không phải `displacement`

Update 2026-05-14 thêm:

- đã sweep tiếp `pin_bar` hẹp ngay trên winner hiện tại, tức là:
  - chỉ đổi branch `pin_bar`
  - giữ nguyên `trend_body` và `displacement`
- các relax nhỏ đơn lẻ:
  - `wick_to_body 2.0 -> 1.75`
  - `close_extreme_ratio 0.25 -> 0.30`
  - bỏ ràng buộc màu nến
  - đều không tạo thêm trade nào trên bộ cache đã test
- theo intent hiện tại, `pin_bar` được chấp nhận không cần cùng màu với hướng trade
- trên bộ cache đã test, thay đổi này không làm đổi metrics
- chỉ variant `pin_bar_intent_relaxed` tạo thêm trade thật:
  - baseline `4 -> 5`
  - recent continuous `7 -> 10`
  - recent `2026-04` `5 -> 7`
- nhưng variant này làm baseline xấu đi rõ:
  - profit giảm
  - drawdown tăng mạnh
  - win rate giảm
- kết luận:
  - relax pin bar kiểu đơn biến đã gần chạm trần, không còn tín hiệu
  - nếu muốn đi tiếp nhánh pin bar, nên inspect các trade mới của `pin_bar_intent_relaxed` rồi thêm filter hẹp

Update 2026-05-14 thêm nữa:

- đã sweep tiếp nhánh `trend_body` quanh winner hiện tại
- các nới lỏng nhỏ ở shape:
  - `body_ratio 0.55 -> 0.50`
  - `close near extreme 0.15 -> 0.20`
  - hoặc kết hợp 2 cái
  - đều không đổi kết quả trên bộ cache đã test
- nới `wick_reclaim` nhẹ sang `touch 0.40 / close 0.60` cũng không đổi gì
- chỉ khi nới mạnh hơn sang `touch 0.45 / close 0.55` mới thêm trade
  - nhưng kéo quality recent xuống rõ
- kết luận:
  - `trend_body` hiện gần như không còn headroom nếu chỉ refine hẹp
  - nhánh còn đáng nghiên cứu hơn vẫn là inspect / salvage `pin_bar_intent_relaxed`

Update 2026-05-14 cuối:

- đã inspect `pin_bar_intent_relaxed` trade-by-trade
- sau đó đã test tiếp hướng đúng theo mục tiêu `tăng start trade`:
  - union thêm `engulfing / reversal reclaim`
  - chạy rộng trên `12 cache`
- kết quả:
  - nhánh này đúng là mở thêm lệnh
  - nhưng baseline degrade rõ gần như ở mọi variant
  - `engulfing_strict_fresh5` là bản salvage đỡ nhất
  - nhưng vẫn thua winner hiện tại:
    - baseline `4 trades / 0.7393% / DD -0.1352 / WR 0.75`
    - so với `5 trades / 0.4086% / DD -0.3283 / WR 0.6`
- kết luận mới:
  - nếu mục tiêu là tăng tỉ lệ vào lệnh, `union thêm start trade` là ý đúng để test
  - nhưng ít nhất với family `engulfing / reversal reclaim`, chưa ra winner
  - các nhánh mở rộng candle type mới đang cho pattern lặp lại:
    - trade count tăng
    - baseline quality hỏng nhanh
  - bước kế tiếp hợp lý hơn là:
    - kiểm tra robustness rộng hơn
    - hoặc debug coverage theo regime / boundary
- trade baseline làm hỏng variant này là một bearish pin bar có:
  - `body_ratio ~ 0.31`
  - `wick/body ~ 2.23`
- 3 trade recent mới có ích đều có `wick/body` mạnh hơn trade baseline xấu đó
- chỉ cần siết lại `PIN_BAR_WICK_TO_BODY` lên `2.25` là:
  - cắt đúng trade baseline xấu
  - vẫn giữ toàn bộ improvement trên recent caches
- `2.50` không cho thêm lợi ích so với `2.25`
- kết luận mới:
  - winner hiện tại đã chuyển sang nhánh pin bar mới:
    - `PIN_BAR_BODY_RATIO = 0.33`
    - `PIN_BAR_WICK_TO_BODY = 2.25`
    - `PIN_BAR_CLOSE_EXTREME_RATIO = 0.30`
    - không bắt buộc màu nến cùng hướng

## Phát hiện quan trọng về alignment

Trong lúc debug có thấy behavior như sau:

- khi có warmup, timestamp của candle `1h` trong engine có thể lệch phase so với cách aggregate tay ban đầu
- điều này làm setup FVG + pin bar biến mất hoàn toàn

Vì thế ở trạng thái hiện tại, strategy phụ thuộc mạnh vào cách Jesse bucket nến `1h`.

Update 2026-05-13:

- với winner hiện tại `pin_bar OR trend_body_wick_reclaim`, sweep lại `warm_up_candles = 0, 24, 60, 120, 240` trên toàn bộ 7 cache không còn cho ra khác biệt
- tức là issue `warm_up_candles` cũ hiện không còn tái hiện trên bộ cache đang dùng
- concern còn lại nghiêng về market coverage và alignment trên dataset khác, không phải warmup count đơn thuần
- cắt riêng baseline `2024-01-01` đến `2024-03-01` thành các window nhỏ cũng cho thấy coverage thấp:
  - trade chỉ xuất hiện ở cụm `2024-01-01 -> 2024-01-07`
  - và cụm `2024-02-05 -> 2024-02-11`
- test data gần đây hơn theo UTC:
  - `2026-03` có `1 trade`, dương nhẹ
  - `2026-04` có `3 trades`, gần như flat dương
  - nhưng run continuous `2026-03 -> 2026-04` lại sinh thêm `1 short` loss lớn ở `2026-04-09 -> 2026-04-11`
- passing March vào `warmup_candles` cho April không tái tạo trade extra đó
- đây là dấu hiệu cần debug tiếp theo ở boundary / continuity giữa window, không phải chỉ do warmup count

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
