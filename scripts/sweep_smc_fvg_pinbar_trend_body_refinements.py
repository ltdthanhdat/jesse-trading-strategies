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


def trend_body_core(
    self,
    is_bullish: bool,
    *,
    body_ratio_min: float,
    close_extreme_ratio: float,
    dominant_wick_max: float,
    opposite_wick_max: float,
):
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
            and body_ratio >= body_ratio_min
            and close_price >= high_price - total_range * close_extreme_ratio
            and upper_wick <= total_range * dominant_wick_max
            and lower_wick <= total_range * opposite_wick_max
        )

    return (
        close_price < open_price
        and body_ratio >= body_ratio_min
        and close_price <= low_price + total_range * close_extreme_ratio
        and lower_wick <= total_range * dominant_wick_max
        and upper_wick <= total_range * opposite_wick_max
    )


def trend_body_default(self, is_bullish: bool):
    return trend_body_core(
        self,
        is_bullish,
        body_ratio_min=0.55,
        close_extreme_ratio=0.15,
        dominant_wick_max=0.15,
        opposite_wick_max=0.2,
    )


def trend_body_body_050(self, is_bullish: bool):
    return trend_body_core(
        self,
        is_bullish,
        body_ratio_min=0.50,
        close_extreme_ratio=0.15,
        dominant_wick_max=0.15,
        opposite_wick_max=0.2,
    )


def trend_body_close_020(self, is_bullish: bool):
    return trend_body_core(
        self,
        is_bullish,
        body_ratio_min=0.55,
        close_extreme_ratio=0.20,
        dominant_wick_max=0.15,
        opposite_wick_max=0.2,
    )


def trend_body_body_050_close_020(self, is_bullish: bool):
    return trend_body_core(
        self,
        is_bullish,
        body_ratio_min=0.50,
        close_extreme_ratio=0.20,
        dominant_wick_max=0.15,
        opposite_wick_max=0.2,
    )


def overlap_fvg(self, is_bullish, fvg):
    if is_bullish != fvg.is_bullish:
        return False
    return self.high >= fvg.bottom and self.low <= fvg.top


def wick_reclaim_core(self, is_bullish, fvg, *, touch_ratio: float, close_ratio: float):
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


def in_fvg_default(self, is_bullish, fvg):
    signal_kind = self.vars.get("entry_signal_kind")
    if signal_kind != "trend_body":
        return ORIGINAL_IN_FVG(self, is_bullish, fvg)
    return wick_reclaim_core(self, is_bullish, fvg, touch_ratio=0.35, close_ratio=0.65)


def in_fvg_touch_040_close_060(self, is_bullish, fvg):
    signal_kind = self.vars.get("entry_signal_kind")
    if signal_kind != "trend_body":
        return ORIGINAL_IN_FVG(self, is_bullish, fvg)
    return wick_reclaim_core(self, is_bullish, fvg, touch_ratio=0.40, close_ratio=0.60)


def in_fvg_touch_045_close_055(self, is_bullish, fvg):
    signal_kind = self.vars.get("entry_signal_kind")
    if signal_kind != "trend_body":
        return ORIGINAL_IN_FVG(self, is_bullish, fvg)
    return wick_reclaim_core(self, is_bullish, fvg, touch_ratio=0.45, close_ratio=0.55)


VARIANTS = {
    "current_winner": (trend_body_default, in_fvg_default),
    "trend_body_body_050": (trend_body_body_050, in_fvg_default),
    "trend_body_close_020": (trend_body_close_020, in_fvg_default),
    "trend_body_body_050_close_020": (trend_body_body_050_close_020, in_fvg_default),
    "trend_body_touch_040_close_060": (trend_body_default, in_fvg_touch_040_close_060),
    "trend_body_touch_045_close_055": (trend_body_default, in_fvg_touch_045_close_055),
    "trend_body_body_050_touch_040_close_060": (trend_body_body_050, in_fvg_touch_040_close_060),
}


ORIGINAL_TREND_BODY = SMC_FVG_PinBar._is_trend_body
ORIGINAL_IN_FVG = SMC_FVG_PinBar._is_pin_bar_in_fvg


def run_variant(cache_name: str, name: str, trend_body_fn, in_fvg_fn):
    candles = load_candles(cache_name)
    SMC_FVG_PinBar._is_trend_body = trend_body_fn
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
        SMC_FVG_PinBar._is_trend_body = ORIGINAL_TREND_BODY
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


def main():
    rows = []
    for cache_name in CACHES:
        for variant_name, (trend_body_fn, in_fvg_fn) in VARIANTS.items():
            rows.append(run_variant(cache_name, variant_name, trend_body_fn, in_fvg_fn))
    print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
