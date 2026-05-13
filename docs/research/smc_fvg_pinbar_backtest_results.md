# SMC_FVG_PinBar Backtest Results

Ngày cập nhật: 2026-05-13

Mục đích:
- lưu kết quả backtest và sweep
- không trộn với debug note hoặc test plan

Current state summary:
- xem `docs/state/smc_fvg_pinbar_state.md`

## Baseline hiện tại

Code state hiện tại:
- FVG lifecycle bám Pine hơn
  - không có `FVG_LOOKBACK`
  - FVG chỉ bị remove khi mitigated hoàn toàn
- Entry rule hiện tại:
  - pin bar chỉ cần overlap FVG
  - `high >= fvg.bottom`
  - `low <= fvg.top`

Dataset baseline:
- `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`

Backtest setup:
- exchange: `Binance Perpetual Futures`
- symbol: `BTC-USDT`
- timeframe: `1h`
- `warm_up_candles = 0`

## Baseline result

- `total = 3`
- `win_rate = 0.6666666666666666`
- `net_profit_percentage = 0.6683005700192093`
- `max_drawdown = -0.13520595720001305`
- `sharpe_ratio = 2.1102751027736897`
- `calmar_ratio = 30.072885907390187`
- `trades_count = 3`

Trades:

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

## Entry Variant Sweep

Baseline dataset:
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
- chỉ `overlap_fvg` tạo thêm trade thật trên dataset baseline
- 3 variant còn lại không khác baseline cũ

## Warmup Sweep

Baseline dataset:
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
- strategy không còn nhạy với `warm_up_candles` trên baseline dataset này

## Cross-Window Cache Sweep

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
- rule mới robust hơn theo `warm_up_candles`
- nhưng trade frequency vẫn thấp trên nhiều market window khác

## Candle Signal Variant Sweep

Experiment:
- hypothesis: có thể thay `pin bar` bằng vài candle type khác hoặc union nhiều type để tăng trade frequency mà không làm quality sụp
- file_changed: `scripts/sweep_smc_fvg_pinbar_signal_variants.py`

Dataset:
- baseline cache:
  - `storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle`
- cross-window caches:
  - `1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle`
  - `1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle`

Variants tested:
- `baseline_pin_bar`
  - current rule
- `loose_pin_bar`
  - nới wick/body, nới close near extreme, cho thân nhỏ-vừa
- `trend_body`
  - thân dày, close gần extreme, bóng ngắn
- `rejection_or_trend_union`
  - `loose_pin_bar OR trend_body`
- `current_pin_bar_or_trend_body`
  - `current pin bar OR trend_body`

Result:
- `baseline_pin_bar`
  - trades_count: `3` trên baseline
  - net_profit_percentage: `0.6683005700192093`
  - max_drawdown: `-0.13520595720001305`
  - win_rate: `0.6666666666666666`
  - windows_with_trades: `1/7`

- `loose_pin_bar`
  - trades_count: `17` trên baseline
  - net_profit_percentage: `-0.2702986514595835`
  - max_drawdown: `-1.1150757736605343`
  - win_rate: `0.4117647058823529`
  - windows_with_trades: `3/7`
  - keep_or_discard: `discard`
  - notes: tăng trade mạnh nhưng quality giảm rõ, không có window nào profit dương

- `trend_body`
  - trades_count: `11` trên baseline
  - net_profit_percentage: `0.065543683033595`
  - max_drawdown: `-1.2061646884020227`
  - win_rate: `0.5454545454545454`
  - windows_with_trades: `5/7`
  - keep_or_discard: `discard`
  - notes: có thêm trade và mở được thêm window, nhưng drawdown baseline xấu hơn nhiều; profit baseline gần như flat

- `rejection_or_trend_union`
  - trades_count: `25` trên baseline
  - net_profit_percentage: `0.8798979755767935`
  - max_drawdown: `-1.2918460573037804`
  - win_rate: `0.52`
  - windows_with_trades: `6/7`
  - keep_or_discard: `discard`
  - notes: tăng coverage mạnh nhất, baseline profit nhỉnh hơn nhưng drawdown xấu đi gần 10 lần và thêm nhiều losing window

- `current_pin_bar_or_trend_body`
  - trades_count: `14` trên baseline
  - net_profit_percentage: `0.7342860715200159`
  - max_drawdown: `-1.2061573219687483`
  - win_rate: `0.5714285714285714`
  - windows_with_trades: `5/7`
  - keep_or_discard: `discard`
  - notes: là union sạch nhất trong nhóm test, nhưng drawdown vẫn xấu hơn baseline quá nhiều

Conclusion:
- `pin bar` hiện tại vẫn là rule sạch nhất theo risk-adjusted quality trên cache đang có
- loại nến `trend_body` đáng nhớ vì mở thêm window thật
- nhưng ở trạng thái hiện tại, chưa có variant candle hoặc union nào đủ tốt để patch vào strategy
