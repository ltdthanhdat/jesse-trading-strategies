import json
import pickle
from pathlib import Path

import numpy as np

from jesse.research.backtest import backtest
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar


CACHES = [
    "1703689200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1703878200000-1704067140000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1740495600000-1740873540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1740873600000-1740959940000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1740873600000-1741046340000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1748617200000-1748995140000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1772323200000-1775001540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1772323200000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1774245600000-1775001540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1775001600000-1777593540000-Binance Perpetual Futures-BTC-USDT.pickle",
    "1775001600000-1777679940000-Binance Perpetual Futures-BTC-USDT.pickle",
]
BASELINE_CACHE = "1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle"
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


def overlap_fvg(self, is_bullish: bool, fvg):
    if is_bullish != fvg.is_bullish:
        return False
    return self.high >= fvg.bottom and self.low <= fvg.top


def wick_reclaim_filter(self, is_bullish: bool, fvg, *, touch_ratio: float, close_ratio: float):
    if not overlap_fvg(self, is_bullish, fvg):
        return False

    _, close_price, _, _ = self._get_candle(0)
    fvg_height = fvg.top - fvg.bottom
    if fvg_height <= 0:
        return False

    if is_bullish:
        return (
            self.low <= fvg.bottom + fvg_height * touch_ratio
            and close_price >= fvg.bottom + fvg_height * close_ratio
        )

    return (
        self.high >= fvg.top - fvg_height * touch_ratio
        and close_price <= fvg.bottom + fvg_height * (1 - close_ratio)
    )


def displacement_close_inside_filter(self, is_bullish: bool, fvg):
    if not wick_reclaim_filter(self, is_bullish, fvg, touch_ratio=0.35, close_ratio=0.65):
        return False

    _, close_price, _, _ = self._get_candle(0)
    if is_bullish:
        return close_price <= fvg.top
    return close_price >= fvg.bottom


def fvg_age_at_most(self, fvg, max_age: int):
    age = (len(self.candles) - 1) - fvg.bar_index
    return age <= max_age


def engulfing_core(
    self,
    is_bullish: bool,
    *,
    body_ratio_min: float,
    close_extreme_ratio: float,
    require_opposite_prev: bool,
    require_body_engulf: bool,
):
    if len(self.candles) < 2:
        return False

    open_price, close_price, high_price, low_price = self._get_candle(0)
    prev_open, prev_close, prev_high, prev_low = self._get_candle(-2)

    body = abs(close_price - open_price)
    total_range = high_price - low_price
    if total_range == 0:
        return False

    body_ratio = body / total_range
    bullish_now = close_price > open_price
    bearish_now = close_price < open_price
    bullish_prev = prev_close > prev_open
    bearish_prev = prev_close < prev_open

    if is_bullish:
        if not bullish_now:
            return False
        if require_opposite_prev and not bearish_prev:
            return False
        if body_ratio < body_ratio_min:
            return False
        if close_price < high_price - total_range * close_extreme_ratio:
            return False
        if require_body_engulf:
            return open_price <= prev_close and close_price >= prev_open
        return close_price >= max(prev_open, prev_close) and low_price <= prev_low

    if not bearish_now:
        return False
    if require_opposite_prev and not bullish_prev:
        return False
    if body_ratio < body_ratio_min:
        return False
    if close_price > low_price + total_range * close_extreme_ratio:
        return False
    if require_body_engulf:
        return open_price >= prev_close and close_price <= prev_open
    return close_price <= min(prev_open, prev_close) and high_price >= prev_high


def engulfing_reclaim_strict(self, is_bullish: bool):
    return engulfing_core(
        self,
        is_bullish,
        body_ratio_min=0.50,
        close_extreme_ratio=0.20,
        require_opposite_prev=True,
        require_body_engulf=True,
    )


def engulfing_reclaim_close_025(self, is_bullish: bool):
    return engulfing_core(
        self,
        is_bullish,
        body_ratio_min=0.50,
        close_extreme_ratio=0.25,
        require_opposite_prev=True,
        require_body_engulf=True,
    )


def reversal_reclaim_loose(self, is_bullish: bool):
    return engulfing_core(
        self,
        is_bullish,
        body_ratio_min=0.45,
        close_extreme_ratio=0.25,
        require_opposite_prev=False,
        require_body_engulf=False,
    )


def make_entry_signal(engulfing_signal):
    def signal(self, is_bullish: bool):
        if ORIGINAL_PIN_BAR(self, is_bullish):
            return "pin_bar"
        if ORIGINAL_TREND_BODY(self, is_bullish):
            return "trend_body"
        if ORIGINAL_DISPLACEMENT(self, is_bullish):
            return "displacement"
        if engulfing_signal(self, is_bullish):
            return "engulfing"
        return None

    return signal


def make_in_fvg(engulfing_touch_ratio: float, engulfing_close_ratio: float):
    def in_fvg(self, is_bullish: bool, fvg):
        if is_bullish != fvg.is_bullish:
            return False

        signal_kind = self.vars.get("entry_signal_kind")
        if signal_kind == "pin_bar":
            return overlap_fvg(self, is_bullish, fvg)
        if signal_kind == "trend_body":
            return wick_reclaim_filter(self, is_bullish, fvg, touch_ratio=0.35, close_ratio=0.65)
        if signal_kind == "displacement":
            return displacement_close_inside_filter(self, is_bullish, fvg)
        if signal_kind == "engulfing":
            return wick_reclaim_filter(
                self,
                is_bullish,
                fvg,
                touch_ratio=engulfing_touch_ratio,
                close_ratio=engulfing_close_ratio,
            )
        return False

    return in_fvg


def make_in_fvg_with_engulfing_age(
    engulfing_touch_ratio: float,
    engulfing_close_ratio: float,
    engulfing_max_age: int,
):
    def in_fvg(self, is_bullish: bool, fvg):
        if is_bullish != fvg.is_bullish:
            return False

        signal_kind = self.vars.get("entry_signal_kind")
        if signal_kind == "pin_bar":
            return overlap_fvg(self, is_bullish, fvg)
        if signal_kind == "trend_body":
            return wick_reclaim_filter(self, is_bullish, fvg, touch_ratio=0.35, close_ratio=0.65)
        if signal_kind == "displacement":
            return displacement_close_inside_filter(self, is_bullish, fvg)
        if signal_kind == "engulfing":
            return (
                fvg_age_at_most(self, fvg, engulfing_max_age)
                and wick_reclaim_filter(
                    self,
                    is_bullish,
                    fvg,
                    touch_ratio=engulfing_touch_ratio,
                    close_ratio=engulfing_close_ratio,
                )
            )
        return False

    return in_fvg


VARIANTS = {
    "current_winner": (
        make_entry_signal(lambda self, is_bullish: False),
        make_in_fvg(0.35, 0.65),
    ),
    "union_engulfing_strict": (
        make_entry_signal(engulfing_reclaim_strict),
        make_in_fvg(0.35, 0.65),
    ),
    "union_engulfing_close_025": (
        make_entry_signal(engulfing_reclaim_close_025),
        make_in_fvg(0.35, 0.60),
    ),
    "union_engulfing_strict_fresh5": (
        make_entry_signal(engulfing_reclaim_strict),
        make_in_fvg_with_engulfing_age(0.35, 0.65, 5),
    ),
    "union_engulfing_strict_fresh8": (
        make_entry_signal(engulfing_reclaim_strict),
        make_in_fvg_with_engulfing_age(0.35, 0.65, 8),
    ),
    "union_reversal_loose": (
        make_entry_signal(reversal_reclaim_loose),
        make_in_fvg(0.40, 0.60),
    ),
}


ORIGINAL_ENTRY_SIGNAL = SMC_FVG_PinBar._entry_signal_kind
ORIGINAL_IN_FVG = SMC_FVG_PinBar._is_pin_bar_in_fvg
ORIGINAL_PIN_BAR = SMC_FVG_PinBar._is_pin_bar
ORIGINAL_TREND_BODY = SMC_FVG_PinBar._is_trend_body
ORIGINAL_DISPLACEMENT = SMC_FVG_PinBar._is_displacement_break


def run_variant(cache_name: str, name: str, entry_signal_fn, in_fvg_fn):
    candles = load_candles(cache_name)
    SMC_FVG_PinBar._entry_signal_kind = entry_signal_fn
    SMC_FVG_PinBar._is_pin_bar_in_fvg = in_fvg_fn
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
        SMC_FVG_PinBar._entry_signal_kind = ORIGINAL_ENTRY_SIGNAL
        SMC_FVG_PinBar._is_pin_bar_in_fvg = ORIGINAL_IN_FVG

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
                "positive_windows": sum(
                    1 for row in variant_rows if row["trades_count"] > 0 and (row["net_profit_percentage"] or 0) > 0
                ),
                "total_trades_all_caches": sum(row["trades_count"] for row in variant_rows),
                "baseline_cache_result": baseline_row,
            }
        )
    return summary


def main():
    rows = []
    for cache_name in CACHES:
        for variant_name, (entry_signal_fn, in_fvg_fn) in VARIANTS.items():
            rows.append(run_variant(cache_name, variant_name, entry_signal_fn, in_fvg_fn))

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
