import json
import pickle
from pathlib import Path

import numpy as np

from jesse.research.backtest import backtest
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar


CACHES = [
    "1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle",
]
BASELINE_CACHE = CACHES[0]
EXCHANGE = "Binance Perpetual Futures"
SYMBOL = "BTC-USDT"
TIMEFRAME = "1h"


def load_candles(cache_name: str):
    path = Path("storage/temp") / cache_name
    with path.open("rb") as f:
        candles_arr = np.array(pickle.load(f), dtype=float)
    return {
        f"{EXCHANGE}-{SYMBOL}": {
            "exchange": EXCHANGE,
            "symbol": SYMBOL,
            "candles": candles_arr,
        }
    }


def _pin_bar_core(
    self,
    is_bullish: bool,
    *,
    body_ratio: float,
    wick_to_body: float,
    close_extreme_ratio: float,
    require_color: bool,
):
    open_price, close_price, high_price, low_price = self._get_candle(0)

    body = abs(close_price - open_price)
    upper_wick = high_price - max(close_price, open_price)
    lower_wick = min(close_price, open_price) - low_price
    total_range = high_price - low_price

    if total_range == 0:
        return False

    if is_bullish:
        close_near_high = close_price >= high_price - total_range * close_extreme_ratio
        body_in_upper_range = min(open_price, close_price) >= low_price + total_range * (1 - body_ratio)
        return (
            (close_price > open_price if require_color else close_price >= open_price)
            and lower_wick >= wick_to_body * body
            and upper_wick <= body
            and body <= total_range * body_ratio
            and close_near_high
            and body_in_upper_range
        )

    close_near_low = close_price <= low_price + total_range * close_extreme_ratio
    body_in_lower_range = max(open_price, close_price) <= high_price - total_range * (1 - body_ratio)
    return (
        (close_price < open_price if require_color else close_price <= open_price)
        and upper_wick >= wick_to_body * body
        and lower_wick <= body
        and body <= total_range * body_ratio
        and close_near_low
        and body_in_lower_range
    )


def current_pin_bar(self, is_bullish: bool):
    return _pin_bar_core(
        self,
        is_bullish,
        body_ratio=self.PIN_BAR_BODY_RATIO,
        wick_to_body=self.PIN_BAR_WICK_TO_BODY,
        close_extreme_ratio=self.PIN_BAR_CLOSE_EXTREME_RATIO,
        require_color=True,
    )


def pin_bar_wick_1_75(self, is_bullish: bool):
    return _pin_bar_core(
        self,
        is_bullish,
        body_ratio=self.PIN_BAR_BODY_RATIO,
        wick_to_body=1.75,
        close_extreme_ratio=self.PIN_BAR_CLOSE_EXTREME_RATIO,
        require_color=True,
    )


def pin_bar_close_0_30(self, is_bullish: bool):
    return _pin_bar_core(
        self,
        is_bullish,
        body_ratio=self.PIN_BAR_BODY_RATIO,
        wick_to_body=self.PIN_BAR_WICK_TO_BODY,
        close_extreme_ratio=0.30,
        require_color=True,
    )


def pin_bar_no_color(self, is_bullish: bool):
    return _pin_bar_core(
        self,
        is_bullish,
        body_ratio=self.PIN_BAR_BODY_RATIO,
        wick_to_body=self.PIN_BAR_WICK_TO_BODY,
        close_extreme_ratio=self.PIN_BAR_CLOSE_EXTREME_RATIO,
        require_color=False,
    )


def pin_bar_intent_relaxed(self, is_bullish: bool):
    return _pin_bar_core(
        self,
        is_bullish,
        body_ratio=0.33,
        wick_to_body=1.75,
        close_extreme_ratio=0.30,
        require_color=False,
    )


VARIANTS = {
    "current_winner": current_pin_bar,
    "pin_bar_wick_1_75": pin_bar_wick_1_75,
    "pin_bar_close_0_30": pin_bar_close_0_30,
    "pin_bar_no_color": pin_bar_no_color,
    "pin_bar_intent_relaxed": pin_bar_intent_relaxed,
}


def run_variant(cache_name: str, name: str, pin_bar_fn):
    candles = load_candles(cache_name)
    original = SMC_FVG_PinBar._is_pin_bar
    SMC_FVG_PinBar._is_pin_bar = pin_bar_fn
    try:
        result = backtest(
            config={
                "starting_balance": 10_000,
                "fee": 0.0004,
                "type": "futures",
                "futures_leverage": 1,
                "futures_leverage_mode": "cross",
                "exchange": EXCHANGE,
                "warm_up_candles": 0,
            },
            routes=[
                {
                    "exchange": EXCHANGE,
                    "strategy": "SMC_FVG_PinBar",
                    "symbol": SYMBOL,
                    "timeframe": TIMEFRAME,
                }
            ],
            data_routes=[],
            candles=candles,
            warmup_candles=None,
            generate_equity_curve=False,
            fast_mode=False,
        )
    finally:
        SMC_FVG_PinBar._is_pin_bar = original

    metrics = result["metrics"]
    trades = result.get("trades", [])
    return {
        "cache": cache_name,
        "variant": name,
        "trades_count": len(trades),
        "net_profit_percentage": metrics.get("net_profit_percentage"),
        "max_drawdown": metrics.get("max_drawdown"),
        "win_rate": metrics.get("win_rate"),
        "first_three_trades": trades[:3],
    }


def summarize(rows):
    summary = []
    for variant in VARIANTS:
        variant_rows = [row for row in rows if row["variant"] == variant]
        baseline_row = next(row for row in variant_rows if row["cache"] == BASELINE_CACHE)
        summary.append(
            {
                "variant": variant,
                "trade_windows": sum(1 for row in variant_rows if row["trades_count"] > 0),
                "total_trades_all_caches": sum(row["trades_count"] for row in variant_rows),
                "baseline_cache_result": baseline_row,
                "positive_windows": [
                    row["cache"]
                    for row in variant_rows
                    if row["trades_count"] > 0 and (row["net_profit_percentage"] or 0) > 0
                ],
            }
        )
    return summary


def main():
    rows = []
    for cache_name in CACHES:
        for variant_name, pin_bar_fn in VARIANTS.items():
            rows.append(run_variant(cache_name, variant_name, pin_bar_fn))

    print(
        json.dumps(
            {
                "summary": summarize(rows),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
