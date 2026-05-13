# SMC_FVG_PinBar All Futures Backtest

Ngày cập nhật: 2026-05-13

Window:
- `2026-03-01 00:00:00 UTC -> 2026-04-30 23:59:00 UTC`

Universe:
- nguồn dữ liệu: Binance public archive `data.binance.vision`
- market type: USDT futures symbols có archive monthly klines
- total symbols seen trong archive: `700`

Raw outputs:
- `storage/results/smc_fvg_pinbar_all_futures_results.json`
- `storage/results/smc_fvg_pinbar_all_futures_results.csv`
- cache 1m theo symbol:
  - `storage/temp/all_futures/`

Summary:
- `symbols_tested = 671`
- `symbols_with_trades = 571`
- `profitable_symbols = 267`
- `zero_trade_ok = 100`
- `no_data = 27`
- `backtest_error = 2`
- `mean_net_profit_percentage = -0.0636860636092628`
- `median_net_profit_percentage = 0.0`

BTC reference:
- `BTC-USDT`
  - `net_profit_percentage = -0.04465644600880868`
  - `trades_count = 7`
  - `win_rate = 0.7142857142857143`
  - `max_drawdown = -0.7070645131663`
  - rank theo `net_profit_percentage`: `375 / 671`

Top 10:
- `PLAY-USDT`
  - `net_profit_percentage = 8.499815258424777%`
  - `trades_count = 7`
  - `win_rate = 1.0`
  - `max_drawdown = 0.0`
- `BIO-USDT`
  - `net_profit_percentage = 6.970266609995574%`
  - `trades_count = 11`
  - `win_rate = 0.5454545454545454`
  - `max_drawdown = -2.413614650922713`
- `SPACE-USDT`
  - `net_profit_percentage = 5.7230347540327395%`
  - `trades_count = 9`
  - `win_rate = 0.8888888888888888`
  - `max_drawdown = -0.4871884140183247`
- `PENDLE-USDT`
  - `net_profit_percentage = 4.813122859272358%`
  - `trades_count = 13`
  - `win_rate = 0.7692307692307693`
  - `max_drawdown = -0.39493236894251327`
- `BR-USDT`
  - `net_profit_percentage = 4.577552113340003%`
  - `trades_count = 3`
  - `win_rate = 1.0`
  - `max_drawdown = -0.7982698926776166`
- `BASED-USDT`
  - `net_profit_percentage = 4.490961815137102%`
  - `trades_count = 4`
  - `win_rate = 0.75`
  - `max_drawdown = -1.0998025705948766`
- `D-USDT`
  - `net_profit_percentage = 4.481312071622559%`
  - `trades_count = 8`
  - `win_rate = 0.625`
  - `max_drawdown = -2.453798969922538`
- `YGG-USDT`
  - `net_profit_percentage = 3.7483353397921646%`
  - `trades_count = 8`
  - `win_rate = 1.0`
  - `max_drawdown = -0.21679112351861152`
- `STG-USDT`
  - `net_profit_percentage = 3.616183516039552%`
  - `trades_count = 6`
  - `win_rate = 0.8333333333333334`
  - `max_drawdown = -0.7727756078933501`
- `我踏马来了-USDT`
  - `net_profit_percentage = 3.5170985123991674%`
  - `trades_count = 6`
  - `win_rate = 0.8333333333333334`
  - `max_drawdown = -0.8884927022332456`

Bottom 10:
- `LAB-USDT`: `-7.2073902165432715%`, `7 trades`, `win_rate 0.0`
- `CYS-USDT`: `-6.670184179872988%`, `8 trades`, `win_rate 0.25`
- `API3-USDT`: `-5.919643181738969%`, `9 trades`, `win_rate 0.2222222222222222`
- `TRIA-USDT`: `-4.123428827425739%`, `9 trades`, `win_rate 0.2222222222222222`
- `HIGH-USDT`: `-4.036825747718506%`, `9 trades`, `win_rate 0.3333333333333333`
- `AKE-USDT`: `-4.025827975596901%`, `6 trades`, `win_rate 0.3333333333333333`
- `BSB-USDT`: `-3.779236214354399%`, `2 trades`, `win_rate 0.0`
- `MEGA-USDT`: `-3.75935928284855%`, `11 trades`, `win_rate 0.09090909090909091`
- `G-USDT`: `-3.6141094048767632%`, `8 trades`, `win_rate 0.125`
- `BB-USDT`: `-3.579976540898329%`, `6 trades`, `win_rate 0.3333333333333333`

Backtest errors:
- `ARIA-USDT`
- `Q-USDT`

Notes:
- `backtest_error` hiện là lỗi strategy-level do order price không hợp lệ trên một số coin giá rất nhỏ.
- file CSV/JSON mới là source đầy đủ để lọc tiếp theo: min trade count, max drawdown, hoặc loại symbol lỗi.
