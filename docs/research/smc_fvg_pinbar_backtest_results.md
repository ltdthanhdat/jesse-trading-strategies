# SMC_FVG_PinBar Backtest Results

Ngày cập nhật: 2026-05-13

Mục đích:
- lưu kết quả backtest và sweep
- không trộn với debug note hoặc test plan

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

## Current reading

Những gì đã rõ:
- issue `warm_up_candles` đã giảm mạnh
- lifecycle FVG đã gần Pine hơn
- entry rule `overlap_fvg` tốt hơn baseline cũ

Những gì chưa rõ:
- pin bar detection có đang quá chặt không
- setup vốn hiếm thật hay đang bỏ lỡ nhiều candle hợp lệ
