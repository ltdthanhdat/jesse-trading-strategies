import json
import pickle
from pathlib import Path

import numpy as np

from jesse.research.backtest import backtest
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar


BASELINE_CACHE = Path(
    "storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle"
)
CACHE_GLOB = "storage/temp/*-Binance Perpetual Futures-BTC-USDT.pickle"
EXCHANGE = "Binance Perpetual Futures"
SYMBOL = "BTC-USDT"
TIMEFRAME = "1h"


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


def loose_pin_bar(self, is_bullish):
    open_price, close_price, high_price, low_price = self._get_candle(0)

    body = abs(close_price - open_price)
    upper_wick = high_price - max(close_price, open_price)
    lower_wick = min(close_price, open_price) - low_price
    total_range = high_price - low_price

    if total_range == 0:
        return False

    if is_bullish:
        close_near_high = close_price >= high_price - total_range * 0.35
        body_in_upper_range = min(open_price, close_price) >= low_price + total_range * 0.5
        return (
            close_price >= open_price
            and body <= total_range * 0.4
            and lower_wick >= max(body * 1.5, total_range * 0.3)
            and upper_wick <= total_range * 0.25
            and close_near_high
            and body_in_upper_range
        )

    close_near_low = close_price <= low_price + total_range * 0.35
    body_in_lower_range = max(open_price, close_price) <= high_price - total_range * 0.5
    return (
        close_price <= open_price
        and body <= total_range * 0.4
        and upper_wick >= max(body * 1.5, total_range * 0.3)
        and lower_wick <= total_range * 0.25
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


def rejection_or_trend_union(self, is_bullish):
    return loose_pin_bar(self, is_bullish) or trend_body(self, is_bullish)


VARIANTS = {
    "baseline_pin_bar": current_pin_bar,
    "loose_pin_bar": loose_pin_bar,
    "trend_body": trend_body,
    "rejection_or_trend_union": rejection_or_trend_union,
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


def run_variant(cache_path: Path, name: str, fn):
    candles = load_candles(cache_path)
    original = SMC_FVG_PinBar._is_pin_bar
    SMC_FVG_PinBar._is_pin_bar = fn

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
        "cache": cache_path.name,
        "variant": name,
        "trades_count": len(trades),
        "total": metrics.get("total"),
        "net_profit_percentage": metrics.get("net_profit_percentage"),
        "max_drawdown": metrics.get("max_drawdown"),
        "win_rate": metrics.get("win_rate"),
        "first_three_trades": trades[:3],
    }


def summarize(rows):
    baseline_rows = {row["cache"]: row for row in rows if row["variant"] == "baseline_pin_bar"}
    summary = []

    for variant in VARIANTS:
        variant_rows = [row for row in rows if row["variant"] == variant]
        trade_windows = sum(1 for row in variant_rows if row["trades_count"] > 0)
        total_trades = sum(row["trades_count"] for row in variant_rows)
        baseline_trade_delta = sum(
            row["trades_count"] - baseline_rows[row["cache"]]["trades_count"]
            for row in variant_rows
        )
        baseline_result = next(
            (row for row in variant_rows if row["cache"] == BASELINE_CACHE.name),
            None,
        )
        summary.append(
            {
                "variant": variant,
                "trade_windows": trade_windows,
                "total_trades_all_caches": total_trades,
                "trade_delta_vs_baseline_all_caches": baseline_trade_delta,
                "baseline_cache_result": baseline_result,
            }
        )

    return summary


def main():
    cache_paths = sorted(Path(".").glob(CACHE_GLOB))
    rows = []
    for cache_path in cache_paths:
        for name, fn in VARIANTS.items():
            rows.append(run_variant(cache_path, name, fn))

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
