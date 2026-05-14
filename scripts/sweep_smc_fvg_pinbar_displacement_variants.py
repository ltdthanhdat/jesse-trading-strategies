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
ORIGINAL_IN_FVG = SMC_FVG_PinBar._is_pin_bar_in_fvg


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


def base_displacement_filter(self, is_bullish, fvg):
    if not ORIGINAL_IN_FVG(self, is_bullish, fvg):
        return False
    return self.vars.get("entry_signal_kind") == "displacement"


def displacement_close_inside_fvg(self, is_bullish, fvg):
    if not base_displacement_filter(self, is_bullish, fvg):
        return False

    _, close_price, _, _ = self._get_candle(0)
    if is_bullish:
        return close_price <= fvg.top
    return close_price >= fvg.bottom


def displacement_age_ge_5(self, is_bullish, fvg):
    if not base_displacement_filter(self, is_bullish, fvg):
        return False

    age = (len(self.candles) - 1) - fvg.bar_index
    return age >= 5


def displacement_overshoot_le_0_2h(self, is_bullish, fvg):
    if not base_displacement_filter(self, is_bullish, fvg):
        return False

    height = fvg.top - fvg.bottom
    if height <= 0:
        return False

    if is_bullish:
        return self.low >= fvg.bottom - height * 0.2
    return self.high <= fvg.top + height * 0.2 and self.low >= fvg.bottom - height * 0.2


def keep_all_non_displacement(extra_filter):
    def fn(self, is_bullish, fvg):
        signal_kind = self.vars.get("entry_signal_kind")
        if signal_kind != "displacement":
            return ORIGINAL_IN_FVG(self, is_bullish, fvg)
        return extra_filter(self, is_bullish, fvg)

    return fn


VARIANTS = {
    "current_winner": ORIGINAL_IN_FVG,
    "displacement_close_inside_fvg": keep_all_non_displacement(displacement_close_inside_fvg),
    "displacement_age_ge_5": keep_all_non_displacement(displacement_age_ge_5),
    "displacement_overshoot_le_0_2h": keep_all_non_displacement(displacement_overshoot_le_0_2h),
    "displacement_close_inside_and_age_ge_5": keep_all_non_displacement(
        lambda self, is_bullish, fvg: (
            displacement_close_inside_fvg(self, is_bullish, fvg)
            and displacement_age_ge_5(self, is_bullish, fvg)
        )
    ),
}


def run_variant(cache_name: str, name: str, in_fvg_fn):
    candles = load_candles(cache_name)
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
        for variant_name, in_fvg_fn in VARIANTS.items():
            rows.append(run_variant(cache_name, variant_name, in_fvg_fn))

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
