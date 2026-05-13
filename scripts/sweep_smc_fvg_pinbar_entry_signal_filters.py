import json
import pickle
from pathlib import Path

import numpy as np

from jesse.research.backtest import backtest
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar


CACHE_GLOB = "storage/temp/*-Binance Perpetual Futures-BTC-USDT.pickle"
BASELINE_CACHE = "1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle"
EXCHANGE = "Binance Perpetual Futures"
SYMBOL = "BTC-USDT"
TIMEFRAME = "1h"


def overlap_fvg(self, is_bullish, fvg):
    if is_bullish != fvg.is_bullish:
        return False
    return self.high >= fvg.bottom and self.low <= fvg.top


def current_pin_bar(self, is_bullish):
    open_price, close_price, high_price, low_price = self._get_candle(0)

    body = abs(close_price - open_price)
    upper_wick = high_price - max(close_price, open_price)
    lower_wick = min(close_price, open_price) - low_price
    total_range = high_price - low_price

    if total_range == 0:
        return False

    if is_bullish:
        close_near_high = close_price >= high_price - total_range * self.PIN_BAR_CLOSE_EXTREME_RATIO
        body_in_upper_range = min(open_price, close_price) >= low_price + total_range * (1 - self.PIN_BAR_BODY_RATIO)
        return (
            close_price > open_price
            and lower_wick >= self.PIN_BAR_WICK_TO_BODY * body
            and upper_wick <= body
            and body <= total_range * self.PIN_BAR_BODY_RATIO
            and close_near_high
            and body_in_upper_range
        )

    close_near_low = close_price <= low_price + total_range * self.PIN_BAR_CLOSE_EXTREME_RATIO
    body_in_lower_range = max(open_price, close_price) <= high_price - total_range * (1 - self.PIN_BAR_BODY_RATIO)
    return (
        close_price < open_price
        and upper_wick >= self.PIN_BAR_WICK_TO_BODY * body
        and lower_wick <= body
        and body <= total_range * self.PIN_BAR_BODY_RATIO
        and close_near_low
        and body_in_lower_range
    )


def trend_body(self, is_bullish):
    open_price, close_price, high_price, low_price = self._get_candle(0)

    body = abs(close_price - open_price)
    upper_wick = high_price - max(close_price, open_price)
    lower_wick = min(close_price, open_price) - low_price
    total_range = high_price - low_price

    if total_range == 0:
        return False

    body_ratio = body / total_range
    if is_bullish:
        return (
            close_price > open_price
            and body_ratio >= 0.55
            and close_price >= high_price - total_range * 0.15
            and upper_wick <= total_range * 0.15
            and lower_wick <= total_range * 0.2
        )

    return (
        close_price < open_price
        and body_ratio >= 0.55
        and close_price <= low_price + total_range * 0.15
        and lower_wick <= total_range * 0.15
        and upper_wick <= total_range * 0.2
    )


def close_in_strong_fvg_zone(self, is_bullish, fvg):
    if not overlap_fvg(self, is_bullish, fvg):
        return False

    _, close_price, _, _ = self._get_candle(0)
    fvg_height = fvg.top - fvg.bottom
    if fvg_height <= 0:
        return False

    if is_bullish:
        return close_price >= fvg.bottom + fvg_height * 0.7
    return close_price <= fvg.bottom + fvg_height * 0.3


def wick_reclaim_in_fvg(self, is_bullish, fvg):
    if not overlap_fvg(self, is_bullish, fvg):
        return False

    _, close_price, _, _ = self._get_candle(0)
    fvg_height = fvg.top - fvg.bottom
    if fvg_height <= 0:
        return False

    if is_bullish:
        return self.low <= fvg.bottom + fvg_height * 0.35 and close_price >= fvg.bottom + fvg_height * 0.65
    return self.high >= fvg.top - fvg_height * 0.35 and close_price <= fvg.bottom + fvg_height * 0.35


def body_not_too_large_vs_fvg(self, is_bullish, fvg):
    if not overlap_fvg(self, is_bullish, fvg):
        return False

    open_price, close_price, _, _ = self._get_candle(0)
    body = abs(close_price - open_price)
    fvg_height = fvg.top - fvg.bottom
    if fvg_height <= 0:
        return False

    return body <= fvg_height * 1.25


def fresh_fvg_8(self, is_bullish, fvg):
    if not overlap_fvg(self, is_bullish, fvg):
        return False

    age = (len(self.candles) - 1) - fvg.bar_index
    return age <= 8


def make_signal_fn(allow_pin_bar, allow_trend_body):
    def signal(self, is_bullish):
        if allow_pin_bar and current_pin_bar(self, is_bullish):
            self.vars["_entry_signal_label"] = "pin_bar"
            return True
        if allow_trend_body and trend_body(self, is_bullish):
            self.vars["_entry_signal_label"] = "trend_body"
            return True

        self.vars["_entry_signal_label"] = None
        return False

    return signal


def make_in_fvg_fn(trend_filter):
    def in_fvg(self, is_bullish, fvg):
        if is_bullish != fvg.is_bullish:
            return False

        label = self.vars.get("_entry_signal_label")
        if label == "pin_bar":
            return overlap_fvg(self, is_bullish, fvg)
        if label == "trend_body":
            return trend_filter(self, is_bullish, fvg)
        return False

    return in_fvg


VARIANTS = {
    "baseline_pin_bar": (
        make_signal_fn(True, False),
        make_in_fvg_fn(overlap_fvg),
    ),
    "trend_body_only": (
        make_signal_fn(False, True),
        make_in_fvg_fn(overlap_fvg),
    ),
    "trend_body_close_zone": (
        make_signal_fn(False, True),
        make_in_fvg_fn(close_in_strong_fvg_zone),
    ),
    "trend_body_wick_reclaim": (
        make_signal_fn(False, True),
        make_in_fvg_fn(wick_reclaim_in_fvg),
    ),
    "trend_body_small_vs_fvg": (
        make_signal_fn(False, True),
        make_in_fvg_fn(body_not_too_large_vs_fvg),
    ),
    "trend_body_fresh_fvg_8": (
        make_signal_fn(False, True),
        make_in_fvg_fn(fresh_fvg_8),
    ),
    "pin_bar_or_trend_close_zone": (
        make_signal_fn(True, True),
        make_in_fvg_fn(close_in_strong_fvg_zone),
    ),
    "pin_bar_or_trend_wick_reclaim": (
        make_signal_fn(True, True),
        make_in_fvg_fn(wick_reclaim_in_fvg),
    ),
    "pin_bar_or_trend_small_vs_fvg": (
        make_signal_fn(True, True),
        make_in_fvg_fn(body_not_too_large_vs_fvg),
    ),
    "pin_bar_or_trend_fresh_fvg_8": (
        make_signal_fn(True, True),
        make_in_fvg_fn(fresh_fvg_8),
    ),
}


def load_candles(cache_path: Path):
    with cache_path.open("rb") as f:
        candles_arr = np.array(pickle.load(f), dtype=float)
    return {
        f"{EXCHANGE}-{SYMBOL}": {
            "exchange": EXCHANGE,
            "symbol": SYMBOL,
            "candles": candles_arr,
        }
    }


def run_variant(cache_path: Path, name: str, signal_fn, in_fvg_fn):
    candles = load_candles(cache_path)
    original_signal = SMC_FVG_PinBar._is_pin_bar
    original_in_fvg = SMC_FVG_PinBar._is_pin_bar_in_fvg

    SMC_FVG_PinBar._is_pin_bar = signal_fn
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
        SMC_FVG_PinBar._is_pin_bar = original_signal
        SMC_FVG_PinBar._is_pin_bar_in_fvg = original_in_fvg

    metrics = result["metrics"]
    trades = result.get("trades", [])
    return {
        "cache": cache_path.name,
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
        subset = [r for r in rows if r["variant"] == variant]
        baseline_row = next(r for r in subset if r["cache"] == BASELINE_CACHE)
        summary.append(
            {
                "variant": variant,
                "windows_with_trades": sum(1 for r in subset if r["trades_count"] > 0),
                "total_trades_all_caches": sum(r["trades_count"] for r in subset),
                "baseline": {
                    "trades_count": baseline_row["trades_count"],
                    "net_profit_percentage": baseline_row["net_profit_percentage"],
                    "max_drawdown": baseline_row["max_drawdown"],
                    "win_rate": baseline_row["win_rate"],
                },
                "positive_windows": [
                    {
                        "cache": r["cache"],
                        "trades_count": r["trades_count"],
                        "net_profit_percentage": r["net_profit_percentage"],
                    }
                    for r in subset
                    if r["trades_count"] > 0 and (r["net_profit_percentage"] or 0) > 0
                ],
            }
        )
    return summary


def main():
    cache_paths = sorted(Path(".").glob(CACHE_GLOB))
    rows = []
    for cache_path in cache_paths:
        for name, (signal_fn, in_fvg_fn) in VARIANTS.items():
            rows.append(run_variant(cache_path, name, signal_fn, in_fvg_fn))

    print(json.dumps({"summary": summarize(rows), "rows": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
