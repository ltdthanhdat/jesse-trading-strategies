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

### Experiment 2026-05-14 K: Displacement Guard Sweep

Experiment:
- hypothesis: trade thua mới ở cache `1740495600000-1740873540000-...` có thể bị loại bằng một guard hẹp chỉ áp vào `displacement`, mà không làm mất các trade thắng mới
- file_changed: `scripts/sweep_smc_fvg_pinbar_displacement_variants.py`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `current_winner`
  - baseline: `4 trades / 0.73935024987001% / max_drawdown -0.13520595720001305 / win_rate 0.75`
  - old losing cache `1740495600000-1740873540000-...`: `1 trade / -0.21995973902560087%`
  - recent continuous `2026-03 -> 2026-04`: `7 trades / -0.04465644600880868%`
  - recent `2026-04`: `5 trades / 0.42577161733199426%`
- `displacement_close_inside_fvg`
  - baseline giữ nguyên
  - old losing cache: `0 trade`
  - recent continuous giữ nguyên `7 trades / -0.04465644600880868%`
  - recent `2026-04` giữ nguyên `5 trades / 0.42577161733199426%`
- `displacement_age_ge_5`
  - kết quả giống `displacement_close_inside_fvg` trên toàn bộ cache đã test
- `displacement_overshoot_le_0_2h`
  - kết quả cũng giống `displacement_close_inside_fvg` trên toàn bộ cache đã test
- `displacement_close_inside_and_age_ge_5`
  - kết quả cũng giống `displacement_close_inside_fvg` trên toàn bộ cache đã test

Conclusion:
- keep_or_discard: `discard as trade-count improvement, keep in mind as quality guard`
- notes:
  - losing short cũ đúng là trade `displacement`
  - cả 4 guard hẹp đều loại được trade thua đó mà không đụng baseline hay 2 trade thắng mới ở `2026-04`
  - nhưng chúng không tăng trade count trên bộ cache đang theo dõi
  - guard đơn giản và dễ giải thích nhất là:
    - với `displacement`, yêu cầu close vẫn nằm trong FVG

### Experiment 2026-05-14 L: Looser Displacement Signal Sweep

Experiment:
- hypothesis: có thể nới rất nhẹ `displacement_break` để lấy thêm trade mới, miễn là giữ guard `close inside FVG`
- file_changed: `none`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `disp_close_inside_body055`
  - không khác `displacement_close_inside_fvg`
  - baseline giữ nguyên `4 trades`
  - recent continuous giữ nguyên `7 trades / -0.04465644600880868%`
  - recent `2026-04` giữ nguyên `5 trades / 0.42577161733199426%`
- `disp_close_inside_extreme025`
  - baseline giữ nguyên `4 trades / 0.73935024987001%`
  - old losing cache vẫn `0 trade`
  - recent continuous: `7 -> 8 trades`, nhưng `-0.04465644600880868% -> -0.21800460701361077%`
  - recent `2026-04`: `5 -> 6 trades`, nhưng `0.42577161733199426% -> 0.2515960865055922%`
  - `win_rate`: `0.7142857142857143 -> 0.625` trên recent continuous
- `disp_close_inside_body055_extreme025`
  - giống hệt `disp_close_inside_extreme025` trên toàn bộ cache đã test

Conclusion:
- keep_or_discard: `discard looser displacement variants`
- notes:
  - nới `body_ratio` từ `0.6 -> 0.55` không đem thêm trade nào
  - nới `close near extreme` từ `0.2 -> 0.25` có tăng trade:
    - recent continuous `7 -> 8`
    - recent `2026-04` `5 -> 6`
  - nhưng quality xấu đi rõ:
    - net profit recent continuous tệ hơn
    - net profit recent `2026-04` giảm
    - win rate recent giảm
  - chưa có `displacement` variant nào vừa tăng trade count vừa giữ quality đủ tốt

### Experiment 2026-05-14 M: Narrow Pin Bar Sweep On Current Winner

Experiment:
- hypothesis: có thể nới rất nhẹ nhánh `pin_bar` bên trong winner hiện tại để tăng trade count, trong khi vẫn giữ `trend_body` và `displacement` như cũ
- file_changed: `scripts/sweep_smc_fvg_pinbar_narrow_pinbar_variants.py`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `pin_bar_wick_1_75`
  - không khác `current_winner` trên toàn bộ cache đã test
- `pin_bar_close_0_30`
  - không khác `current_winner` trên toàn bộ cache đã test
- `pin_bar_no_color`
  - không khác `current_winner` trên toàn bộ cache đã test
- `pin_bar_intent_relaxed`
  - baseline:
    - `4 -> 5 trades`
    - `0.73935024987001% -> 0.41003236528600734%`
    - `max_drawdown -0.13520595720001305 -> -0.3269015171099343`
    - `win_rate 0.75 -> 0.6`
  - old losing cache `1740495600000-1740873540000-...`
    - giữ nguyên `1 trade / -0.21995973902560087%`
  - recent continuous `2026-03 -> 2026-04`:
    - `7 -> 10 trades`
    - `-0.04465644600880868% -> 0.7134234949907934%`
    - `win_rate 0.7142857142857143 -> 0.8`
    - `max_drawdown` gần như giữ nguyên
  - recent `2026-04`:
    - `5 -> 7 trades`
    - `0.42577161733199426% -> 0.8749591917543952%`
    - `win_rate 0.8 -> 0.8571428571428571`
    - `max_drawdown` gần như giữ nguyên

Conclusion:
- keep_or_discard: `discard as global winner, keep as promising recent-data branch`
- notes:
  - 3 variant hẹp đầu không thêm bất kỳ trade nào
  - `pin_bar_intent_relaxed` là variant pin bar đầu tiên tăng trade count thật trên bộ cache current winner:
    - baseline `4 -> 5`
    - recent continuous `7 -> 10`
    - recent `2026-04` `5 -> 7`
  - nhưng baseline degrade rõ:
    - profit giảm mạnh
    - drawdown xấu hơn khoảng `2.4x`
    - win rate giảm
  - đây chưa phải winner để patch vào strategy chung
  - nhưng đáng giữ lại như một nhánh research nếu muốn tối ưu cho regime recent hơn là giữ baseline cũ

### Experiment 2026-05-14 N: Trend Body Refinement Sweep

Experiment:
- hypothesis: có thể nới rất nhẹ nhánh `trend_body + wick_reclaim` để tăng trade count mà không làm winner hiện tại gãy
- file_changed: `scripts/sweep_smc_fvg_pinbar_trend_body_refinements.py`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `trend_body_body_050`
  - không khác `current_winner` trên toàn bộ cache đã test
- `trend_body_close_020`
  - không khác `current_winner`
- `trend_body_body_050_close_020`
  - không khác `current_winner`
- `trend_body_touch_040_close_060`
  - không khác `current_winner`
- `trend_body_body_050_touch_040_close_060`
  - không khác `current_winner`
- `trend_body_touch_045_close_055`
  - baseline giữ nguyên `4 trades / 0.73935024987001%`
  - old losing cache giữ nguyên `1 trade / -0.21995973902560087%`
  - recent continuous `2026-03 -> 2026-04`:
    - `7 -> 8 trades`
    - `-0.04465644600880868% -> -0.5054223026332088%`
    - `max_drawdown -0.7070645131663 -> -1.1206365181369415`
    - `win_rate 0.7142857142857143 -> 0.625`
  - recent `2026-04`:
    - `5 -> 6 trades`
    - `0.42577161733199426% -> -0.03718914604960579%`
    - `max_drawdown -0.19404387607621087 -> -0.4609969101599942`
    - `win_rate 0.8 -> 0.6666666666666666`

Conclusion:
- keep_or_discard: `discard all tested trend_body refinements`
- notes:
  - trend body shape hiện tại khá ổn định; các nới lỏng nhỏ không mở thêm trade
  - chỉ khi nới `wick_reclaim` khá mạnh sang `touch 0.45 / close 0.55` mới tăng trade count
  - nhưng quality recent xấu đi rất rõ, nên không giữ
  - chưa có `trend_body` refinement nào thắng current winner

### Experiment 2026-05-14 O: Salvage Pin Bar Intent Relaxed With Stronger Wick Ratio

Experiment:
- hypothesis: `pin_bar_intent_relaxed` chỉ hỏng vì thêm một trade baseline có wick/body chưa đủ mạnh; nếu siết lại riêng `wick/body`, có thể giữ được recent gains mà không làm baseline xấu đi
- file_changed: `strategies/SMC_FVG_PinBar/__init__.py`

Datasets:
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `pin_bar_intent_relaxed`
  - baseline:
    - `5 trades`
    - `net_profit_percentage = 0.41003236528600734`
    - `max_drawdown = -0.3269015171099343`
    - `win_rate = 0.6`
  - recent continuous:
    - `10 trades`
    - `net_profit_percentage = 0.7134234949907934`
  - recent `2026-04`:
    - `7 trades`
    - `net_profit_percentage = 0.8749591917543952`
- `pin_bar_intent_relaxed_wick_2_25`
  - baseline:
    - quay về đúng baseline winner cũ
    - `4 trades`
    - `net_profit_percentage = 0.73935024987001`
    - `max_drawdown = -0.13520595720001305`
    - `win_rate = 0.75`
  - old losing cache `1740495600000-1740873540000-...`
    - giữ nguyên `1 trade / -0.21995973902560087%`
  - positive cache `1740873600000-1741046340000-...`
    - giữ nguyên `1 trade / 0.8326383061788064%`
  - recent continuous:
    - giữ nguyên toàn bộ improvement của `intent_relaxed`
    - `10 trades`
    - `net_profit_percentage = 0.7134234949907934`
    - `max_drawdown = -0.7070672870937544`
    - `win_rate = 0.8`
  - recent `2026-04`:
    - giữ nguyên toàn bộ improvement của `intent_relaxed`
    - `7 trades`
    - `net_profit_percentage = 0.8749591917543952`
    - `max_drawdown = -0.19404624538188475`
    - `win_rate = 0.8571428571428571`
- `pin_bar_intent_relaxed_wick_2_50`
  - kết quả giống hệt `pin_bar_intent_relaxed_wick_2_25` trên toàn bộ cache đã test

Conclusion:
- keep_or_discard: `keep pin_bar_intent_relaxed_wick_2_25`
- notes:
  - trade baseline xấu của `intent_relaxed` là một bearish pin bar có `wick/body` khoảng `2.23`
  - siết `PIN_BAR_WICK_TO_BODY` lên `2.25` loại đúng trade này
  - đồng thời vẫn giữ được `3` trade mới có ích trên recent data
  - đây là candidate đầu tiên tăng trade count trên recent caches mà không làm baseline 5-cache đang theo dõi xấu đi

### Experiment 2026-05-14 P: Guarded Engulfing / Reversal Union Sweep

Experiment:
- hypothesis: nếu mục tiêu là mở thêm `start trade`, có thể union thêm một nhánh `engulfing / reversal reclaim` bám FVG mà vẫn giữ được quality tốt hơn các union lỏng trước đó
- file_changed: `scripts/sweep_smc_fvg_pinbar_engulfing_union.py`

Datasets:
- `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1775001540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1774245600000-1775001540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle`
- `1775001600000-1777679940000-Binance Perpetual Futures-BTC-USDT.pickle`

Results:
- `current_winner`
  - `trade_windows = 6/12`
  - `positive_windows = 6/12`
  - `total_trades_all_caches = 30`
  - baseline:
    - `4 trades`
    - `net_profit_percentage = 0.73935024987001`
    - `max_drawdown = -0.13520595720001305`
    - `win_rate = 0.75`
  - recent continuous `2026-03 -> 2026-04`:
    - `10 trades`
    - `net_profit_percentage = 0.7134234949907934`
    - `max_drawdown = -0.7070672870937544`
    - `win_rate = 0.8`
  - recent `2026-04`:
    - `7 trades`
    - `net_profit_percentage = 0.8749591917543952`
    - `max_drawdown = -0.19404624538188475`
    - `win_rate = 0.8571428571428571`
- `union_engulfing_strict`
  - `trade_windows = 6/12`
  - `positive_windows = 6/12`
  - `total_trades_all_caches = 32`
  - baseline:
    - `6 trades`
    - `net_profit_percentage = 0.022956172962008876`
    - `max_drawdown = -0.7111361310028985`
    - `win_rate = 0.5`
  - recent continuous:
    - giữ nguyên như `current_winner`
  - recent `2026-04`:
    - giữ nguyên như `current_winner`
- `union_engulfing_strict_fresh5`
  - baseline:
    - `5 trades`
    - `net_profit_percentage = 0.40858390981921183`
    - `max_drawdown = -0.3283393221435005`
    - `win_rate = 0.6`
  - recent continuous:
    - giữ nguyên như `current_winner`
  - recent `2026-04`:
    - giữ nguyên như `current_winner`
- `union_engulfing_strict_fresh8`
  - kết quả gần như giống `union_engulfing_strict`
- `union_engulfing_close_025`
  - `total_trades_all_caches = 35`
  - baseline:
    - `6 trades`
    - `net_profit_percentage = 0.022956172962008876`
    - `max_drawdown = -0.7111361310028985`
    - `win_rate = 0.5`
  - recent continuous `2026-03 -> 2026-04`:
    - `10 -> 11 trades`
    - `0.7134234949907934% -> 0.5387642517295912%`
    - `max_drawdown -0.7070672870937544 -> -0.8792701029526007`
    - `win_rate 0.8 -> 0.7272727272727273`
  - recent `2026-04`:
    - `7 -> 8 trades`
    - `0.8749591917543952% -> 0.7000223637779932%`
    - `win_rate 0.8571428571428571 -> 0.75`
- `union_reversal_loose`
  - `total_trades_all_caches = 37`
  - baseline:
    - `8 trades`
    - `net_profit_percentage = 0.5282855358792065`
    - `max_drawdown = -0.7111331257562581`
    - `win_rate = 0.625`
  - recent continuous:
    - giống `union_engulfing_close_025`
  - recent `2026-04`:
    - giống `union_engulfing_close_025`

Conclusion:
- keep_or_discard: `discard all tested engulfing / reversal unions`
- notes:
  - nhánh này đúng là tăng được `start trade`
  - nhưng phần tăng trade chủ yếu trả giá bằng baseline tệ hơn rõ:
    - drawdown baseline xấu hơn mạnh
    - win rate baseline giảm
    - profit baseline tụt rõ
  - variant salvage tốt nhất là `union_engulfing_strict_fresh5`
    - baseline chỉ còn xấu vừa phải hơn các variant khác
    - nhưng vẫn thua `current_winner` quá rõ
  - chưa có union `engulfing / reversal` nào thắng được winner hiện tại
  - trên bộ `12 cache`, winner hiện tại đang có trade ở `6/12` cache và tất cả `6` cache đó đều dương

### Experiment 2026-05-14 Q: Selected 11-Symbol Recent Multi-Timeframe Check

Experiment:
- hypothesis: winner hiện tại có thể giữ quality trên basket `11` symbol đã chọn ở `1h`, còn `15m` có thể tăng trade count nhưng degrade rõ
- file_changed:
  - `scripts/backtest_smc_fvg_pinbar_selected_symbols_recent.py`
- window:
  - `2026-03-01 00:00 UTC -> 2026-04-30 23:59 UTC`
- symbols:
  - `PLAY-USDT`
  - `BIO-USDT`
  - `SPACE-USDT`
  - `PENDLE-USDT`
  - `BR-USDT`
  - `BASED-USDT`
  - `D-USDT`
  - `YGG-USDT`
  - `STG-USDT`
  - `我踏马来了-USDT`
  - `BTC-USDT`
- raw outputs:
  - `storage/results/all_futures/smc_fvg_pinbar_selected_symbols_recent_multi_tf.json`
  - `storage/results/all_futures/smc_fvg_pinbar_selected_symbols_recent_multi_tf.csv`

Result:
- `1h`
  - profitable symbols: `11 / 11`
  - total trades: `94`
  - side mix: `56 long / 38 short`
  - avg net profit: `4.7545593374963335%`
  - avg max drawdown: `-1.1730067850778154`
  - avg win rate: `0.7958791208791208`
  - best: `BIO-USDT` `10.67593459333302%` `13 trades`
  - worst: `我踏马来了-USDT` `0.5060474614549526%` `8 trades`
- `15m`
  - profitable symbols: `6 / 11`
  - total trades: `352`
  - side mix: `199 long / 153 short`
  - avg net profit: `0.45942588374099474%`
  - avg max drawdown: `-3.101054111185131`
  - avg win rate: `0.5188035001960029`
  - best: `D-USDT` `11.357793514238562%` `34 trades`
  - worst: `PLAY-USDT` `-7.845956977004617%` `31 trades`
- per-symbol compare:
  - `15m` thắng `1h` rõ chỉ ở `D-USDT`
  - `SPACE-USDT`, `PENDLE-USDT`, `BR-USDT`, `BASED-USDT` vẫn dương ở `15m` nhưng thua `1h`
  - `PLAY-USDT`, `YGG-USDT`, `STG-USDT`, `我踏马来了-USDT`, `BTC-USDT` đảo từ dương ở `1h` sang âm ở `15m`
- keep_or_discard: `keep 1h as current robust timeframe; discard 15m as default expansion target for now`
- notes:
  - `15m` đúng là mở trade count rất mạnh: `94 -> 352`
  - nhưng quality giảm rõ trên basket đã chọn:
    - profitable symbols `11/11 -> 6/11`
    - avg drawdown xấu hơn mạnh
    - avg win rate tụt từ `~0.796 -> ~0.519`
  - nếu muốn nghiên cứu tiếp `15m`, không nên coi là port thẳng từ `1h`
  - cần xem nó như một nhánh strategy riêng với logic / guard riêng cho lower timeframe
