# SMC_FVG_PinBar Backtest Results

Ngày cập nhật: 2026-05-13

Mục đích:
- lưu kết quả backtest và sweep
- append log theo từng experiment
- không trộn với debug note hoặc current state summary

Current state summary:
- xem `docs/state/smc_fvg_pinbar_state.md`

## Baseline

Code state:
- FVG lifecycle bám Pine hơn
  - không có `FVG_LOOKBACK`
  - FVG chỉ bị remove khi mitigated hoàn toàn
- Entry containment:
  - `overlap FVG`
  - `high >= fvg.bottom`
  - `low <= fvg.top`

Dataset:
- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Backtest setup:
- exchange: `Binance Perpetual Futures`
- symbol: `BTC-USDT`
- timeframe: `1h`
- `warm_up_candles = 0`

Baseline result:
- `trades_count = 4`
- `total = 4`
- `win_rate = 0.75`
- `net_profit_percentage = 0.73935024987001`
- `max_drawdown = -0.13520595720001305`
- `sharpe_ratio = 2.1102751027736897`
- `calmar_ratio = 30.072885907390187`

Sample trades:
1. `short`
   - entry: `43950.0`
   - exit: `42839.0`
   - qty: `0.056814`
   - pnl: `61.148021901600416`
2. `short`
   - entry: `44108.2`
   - exit: `43948.3`
   - pnl: `7.101125994400084`
3. `long`
   - entry: `42767.8`
   - exit: `43021.9`
   - pnl: `12.910558777040343`
4. `long`
   - entry: `47337.2`
   - exit: `47239.0`
   - pnl: `-7.2285236767198455`

## Experiment Log

### Experiment 2026-05-13 A: Entry Containment Sweep

Experiment:
- hypothesis: rule `pin bar trong FVG` đang quá chặt, cần thử vài containment variant
- file_changed: `strategies/SMC_FVG_PinBar/__init__.py`

Dataset:
- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
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

Conclusion:
- keep_or_discard: `keep overlap_fvg`
- notes: chỉ `overlap_fvg` tạo thêm trade thật; 3 variant còn lại không khác baseline cũ

### Experiment 2026-05-13 B: Warmup Sweep

Experiment:
- hypothesis: strategy có thể còn nhạy với `warm_up_candles`
- file_changed: `none`

Dataset:
- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `warm_up_candles = 0`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
- `warm_up_candles = 24`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
- `warm_up_candles = 60`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
- `warm_up_candles = 120`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
- `warm_up_candles = 240`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`

Conclusion:
- keep_or_discard: `keep current behavior`
- notes: strategy không còn nhạy với `warm_up_candles` trên baseline dataset này

### Experiment 2026-05-13 C: Cross-Window Cache Sweep

Experiment:
- hypothesis: rule hiện tại có thể chỉ chạy được trên một market window hẹp
- file_changed: `none`

Datasets:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 3`
  - `net_profit_percentage = 0.6683005700192093`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `trades_count = 0`

Conclusion:
- keep_or_discard: `discard hypothesis that current rule is broadly robust`
- notes: rule mới robust hơn theo `warm_up_candles`, nhưng trade frequency vẫn thấp trên nhiều market window khác

### Experiment 2026-05-13 D: Candle Signal Variant Sweep

Experiment:
- hypothesis: có thể thay `pin bar` bằng vài candle type khác hoặc union nhiều type để tăng trade frequency mà không làm quality sụp
- file_changed: `scripts/sweep_smc_fvg_pinbar_signal_variants.py`

Datasets:
- baseline cache:
  - `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- cross-window caches:
  - `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `baseline_pin_bar`
  - `trades_count = 3` trên baseline
  - `net_profit_percentage = 0.6683005700192093`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.6666666666666666`
  - `windows_with_trades = 1/7`
- `loose_pin_bar`
  - `trades_count = 17` trên baseline
  - `net_profit_percentage = -0.2702986514595835`
  - `max_drawdown = -1.1150757736605343`
  - `win_rate = 0.4117647058823529`
  - `windows_with_trades = 3/7`
  - `keep_or_discard = discard`
  - notes: tăng trade mạnh nhưng quality giảm rõ, không có window nào profit dương
- `trend_body`
  - `trades_count = 11` trên baseline
  - `net_profit_percentage = 0.065543683033595`
  - `max_drawdown = -1.2061646884020227`
  - `win_rate = 0.5454545454545454`
  - `windows_with_trades = 5/7`
  - `keep_or_discard = discard`
  - notes: có thêm trade và mở được thêm window, nhưng drawdown baseline xấu hơn nhiều; profit baseline gần như flat
- `rejection_or_trend_union`
  - `trades_count = 25` trên baseline
  - `net_profit_percentage = 0.8798979755767935`
  - `max_drawdown = -1.2918460573037804`
  - `win_rate = 0.52`
  - `windows_with_trades = 6/7`
  - `keep_or_discard = discard`
  - notes: tăng coverage mạnh nhất, baseline profit nhỉnh hơn nhưng drawdown xấu đi gần 10 lần và thêm nhiều losing window
- `current_pin_bar_or_trend_body`
  - `trades_count = 14` trên baseline
  - `net_profit_percentage = 0.7342860715200159`
  - `max_drawdown = -1.2061573219687483`
  - `win_rate = 0.5714285714285714`
  - `windows_with_trades = 5/7`
  - `keep_or_discard = discard`
  - notes: là union sạch nhất trong nhóm test, nhưng drawdown vẫn xấu hơn baseline quá nhiều

Conclusion:
- keep_or_discard: `discard all tested candle replacements / unions`
- notes:
  - `pin bar` hiện tại vẫn là rule sạch nhất theo risk-adjusted quality trên cache đang có
  - loại nến `trend_body` đáng nhớ vì mở thêm window thật
  - chưa có variant candle hoặc union nào đủ tốt để patch vào strategy

### Experiment 2026-05-13 E: Trend Body Filter Sweep

Experiment:
- hypothesis: nếu giữ `trend_body`, cần một filter nhỏ trong FVG để tránh noisy entries
- file_changed: `scripts/sweep_smc_fvg_pinbar_entry_signal_filters.py`

Datasets:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `trend_body_only`
  - baseline: `11 trades`
  - `net_profit_percentage = 0.065543683033595`
  - `max_drawdown = -1.2061646884020227`
- `trend_body_close_zone`
  - gần như không khác `trend_body_only`
- `trend_body_wick_reclaim`
  - baseline: `1 trade`
  - `net_profit_percentage = 0.07057987614000083`
  - `max_drawdown = 0.0`
  - `win_rate = 1.0`
- `trend_body_small_vs_fvg`
  - baseline: `8 trades`
  - `net_profit_percentage = -0.44801580622160625`
- `trend_body_fresh_fvg_8`
  - baseline: `6 trades`
  - `net_profit_percentage = 0.6236300518096052`
  - `max_drawdown = -0.6608367445832819`

Conclusion:
- keep_or_discard: `keep wick_reclaim as the only promising trend_body filter`
- notes:
  - `close_zone` gần như vô dụng
  - `body_vs_fvg` không giúp quality
  - `fresh_fvg_8` tốt hơn `trend_body_only` nhưng vẫn xấu hơn baseline pin bar
  - `wick_reclaim` là filter cắt noise mạnh nhất

### Experiment 2026-05-13 F: Winner Refinement Around Wick Reclaim

Experiment:
- hypothesis: `pin_bar OR trend_body_wick_reclaim` có thể là winner; cần test thêm vài refinement nhỏ quanh nó
- file_changed: `strategies/SMC_FVG_PinBar/__init__.py`

Datasets:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `pin_bar_or_trend_wick_reclaim`
  - baseline: `4 trades`
  - `net_profit_percentage = 0.73935024987001`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.75`
  - positive windows:
    - baseline window
    - `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `pin_bar_or_trend_wick_reclaim_fresh5`
  - baseline giữ nguyên như trên
  - mất positive window ngoài baseline
- `pin_bar_or_trend_wick_reclaim_fresh8`
  - baseline giữ nguyên như trên
  - mất positive window ngoài baseline
- `pin_bar_or_trend_wick_reclaim_body1_25`
  - quay về đúng baseline cũ `3 trades`
- `pin_bar_or_trend_wick_reclaim_body1_0`
  - quay về đúng baseline cũ `3 trades`

Conclusion:
- keep_or_discard: `keep pin_bar_or_trend_wick_reclaim`
- notes:
  - so với baseline cũ:
    - `trades_count`: `3 -> 4`
    - `net_profit_percentage`: `0.6683005700192093 -> 0.73935024987001`
    - `max_drawdown`: giữ nguyên `-0.13520595720001305`
    - `win_rate`: `0.6666666666666666 -> 0.75`
  - refinement bằng age/body cap không cải thiện thêm
  - chốt phase entry signal tại đây

### Experiment 2026-05-13 G: Winner Warmup Robustness Sweep

Experiment:
- hypothesis: winner `pin_bar OR trend_body_wick_reclaim` có thể vẫn còn nhạy với `warm_up_candles`
- file_changed: `none`

Datasets:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `warm_up_candles = 0, 24, 60, 120, 240`
  - tất cả cache đều cho đúng cùng một kết quả ở mọi mức warmup
- baseline cache `1704067200000-1709337540000-...`
  - `trades_count = 4`
  - `net_profit_percentage = 0.73935024987001`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.75`
- positive window ngoài baseline `1740873600000-1741046340000-...`
  - `trades_count = 1`
  - `net_profit_percentage = 0.8326383061788064`
  - `max_drawdown = 0.0`
  - `win_rate = 1.0`
- 5 cache còn lại
  - `trades_count = 0` ở mọi mức warmup

Conclusion:
- keep_or_discard: `keep current winner unchanged`
- notes:
  - `warm_up_candles` không còn là nguồn biến động trên bộ cache hiện có
  - robustness theo warmup đã ổn hơn kết luận debug cũ
  - điểm yếu còn lại là market coverage thấp:
    - chỉ có trade trên `2/7` cache

### Experiment 2026-05-13 H: Baseline Internal Time-Window Sweep

Experiment:
- hypothesis: baseline 2 tháng có thể che mất việc winner chỉ hoạt động ở vài cụm thời gian ngắn
- file_changed: `none`

Dataset:
- baseline cache `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `7d non-overlapping windows`
  - `2024-01-01 -> 2024-01-07`
    - `trades_count = 2`
    - `net_profit_percentage = 0.682491478960005`
    - `max_drawdown = -0.13520595720001305`
    - `win_rate = 1.0`
  - `2024-02-05 -> 2024-02-11`
    - `trades_count = 2`
    - `net_profit_percentage = 0.056475100145208776`
    - `max_drawdown = -0.07175378317448855`
    - `win_rate = 0.5`
  - `7/9` window còn lại
    - `trades_count = 0`
- `14d non-overlapping windows`
  - `2024-01-01 -> 2024-01-14`
    - `trades_count = 2`
    - `net_profit_percentage = 0.682491478960005`
    - `win_rate = 1.0`
  - `2024-01-29 -> 2024-02-11`
    - `trades_count = 2`
    - `net_profit_percentage = 0.056475100145208776`
    - `win_rate = 0.5`
  - `3/5` window còn lại
    - `trades_count = 0`

Conclusion:
- keep_or_discard: `keep current winner unchanged`
- notes:
  - 4 trade của baseline không phân bố đều trong 2 tháng
  - chúng tập trung vào 2 cụm thời gian ngắn:
    - đầu tháng 1
    - đầu tháng 2
  - ngay trong baseline cache, time coverage cũng thấp:
    - có trade ở `2/9` window 7 ngày
    - có trade ở `2/5` window 14 ngày

### Experiment 2026-05-13 I: Recent 2026-03 / 2026-04 Data Check

Experiment:
- hypothesis: cần kiểm tra winner trên data gần đây hơn, cụ thể các window UTC `2026-03-01 -> 2026-03-31` và `2026-04-01 -> 2026-04-30`
- file_changed: `none`

Datasets:
- `1772323200000-1775001540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `2026-03-01 00:00 -> 2026-03-31 23:59 UTC`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `2026-04-01 00:00 -> 2026-04-30 23:59 UTC`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `2026-03-01 00:00 -> 2026-04-30 23:59 UTC`

Results:
- `2026-03`
  - `trades_count = 1`
  - `net_profit_percentage = 0.19558363979519808`
  - `max_drawdown = -0.08218100700160269`
  - `win_rate = 1.0`
  - sample trade:
    - `long` `2026-03-17 00:00 -> 2026-03-17 01:11 UTC`
- `2026-04`
  - `trades_count = 3`
  - `net_profit_percentage = 0.027487267938394205`
  - `max_drawdown = -0.19404310221111665`
  - `win_rate = 0.6666666666666666`
  - sample trades:
    - `long` `2026-04-16 12:00 -> 2026-04-16 13:19 UTC`
    - `long` `2026-04-27 20:00 -> 2026-04-27 23:50 UTC`
    - `long` `2026-04-29 18:00 -> 2026-04-29 18:09 UTC`
- `2026-03 + 2026-04` continuous
  - `trades_count = 5`
  - `net_profit_percentage = -0.44106663212560865`
  - `max_drawdown = -0.7070645131663`
  - `win_rate = 0.6`
  - notable extra trade:
    - `short` `2026-04-09 23:00 -> 2026-04-11 19:06 UTC`
    - `PNL = -66.4010268622801`
- `2026-04` with March passed as `warmup_candles`
  - kết quả không đổi so với `2026-04` standalone

Conclusion:
- keep_or_discard: `keep current winner unchanged`
- notes:
  - winner vẫn có trade trên data gần đây hơn, nhưng frequency vẫn thấp:
    - `1 trade` trong tháng 3
    - `3 trades` trong tháng 4
  - chất lượng theo tháng riêng lẻ chỉ dương nhẹ, không mạnh
  - khi chạy continuous 2 tháng, performance đảo sang âm vì xuất hiện thêm một `short` loss lớn ở `2026-04-09`
  - passing March vào `warmup_candles` cho April không tái tạo trade extra đó
  - cần coi đây là dấu hiệu tiếp theo của window-boundary / state-continuity sensitivity

### Experiment 2026-05-13 J: Web-Sourced Displacement Confirmation Union

Experiment:
- hypothesis: thêm `displacement_break` như một confirmation candle sau reclaim FVG có thể tăng trade coverage mà không làm baseline xấu đi; ý này lấy từ các FVG references ngoài repo nói về `rejection candle`, `engulfing`, hoặc `displacement confirmation`
- file_changed: `strategies/SMC_FVG_PinBar/__init__.py`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Result:
- baseline `1704067200000-1709337540000-...`
  - `trades_count = 4`
  - `net_profit_percentage = 0.73935024987001`
  - `max_drawdown = -0.13520595720001305`
  - `win_rate = 0.75`
  - notes: giữ nguyên so với winner cũ
- cache `1740495600000-1740873540000-...`
  - `trades_count = 1`
  - `net_profit_percentage = -0.21995973902560087`
  - `max_drawdown = -0.27752567552981056`
  - `win_rate = 0.0`
  - notes: có thêm `1 short` thua mới
- cache `1740873600000-1741046340000-...`
  - `trades_count = 1`
  - `net_profit_percentage = 0.8326383061788064`
  - `max_drawdown = 0.0`
  - `win_rate = 1.0`
  - notes: giữ nguyên positive window cũ
- cache `1772323200000-1777593540000-...`
  - `trades_count = 7`
  - `net_profit_percentage = -0.04465644600880868`
  - `max_drawdown = -0.7070645131663`
  - `win_rate = 0.7142857142857143`
  - notes:
    - cải thiện rõ từ `5 trades / -0.44106663212560865 / win_rate 0.6`
    - thêm `2` trade thắng mới trong nửa sau `2026-04`
- cache `1775001600000-1777593540000-...`
  - `trades_count = 5`
  - `net_profit_percentage = 0.42577161733199426`
  - `max_drawdown = -0.19404387607621087`
  - `win_rate = 0.8`
  - notes:
    - cải thiện từ `3 trades / 0.027487267938394205 / win_rate 0.6666666666666666`
    - drawdown gần như giữ nguyên

Conclusion:
- keep_or_discard: `keep displacement_break_wick_reclaim union`
- notes:
  - đây là union đầu tiên tăng frequency trên data gần đây mà không làm baseline xấu đi
  - quality tổng thể chưa hoàn hảo vì có thêm `1` losing window cũ
  - next step là inspect trực tiếp:
    - losing short mới ở `1740495600000-1740873540000-...`
    - hai trade thắng mới ở `2026-04`
