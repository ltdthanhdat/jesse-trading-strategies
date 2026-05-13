import json
import pickle
from pathlib import Path

import numpy as np

from jesse.research.backtest import backtest
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar


CACHE_PATH = Path(
    "storage/temp/1704067200000-1709337540000-Binance Perpetual Futures-BTC-USDT.pickle"
)
EXCHANGE = "Binance Perpetual Futures"
SYMBOL = "BTC-USDT"
TIMEFRAME = "1h"


def baseline(self, pin_bar_is_bullish, fvg):
    if pin_bar_is_bullish != fvg.is_bullish:
        return False
    return self.low >= fvg.bottom and self.high <= fvg.top


def body_in_fvg(self, pin_bar_is_bullish, fvg):
    if pin_bar_is_bullish != fvg.is_bullish:
        return False

    open_price, close_price, _, _ = self._get_candle(0)
    body_low = min(open_price, close_price)
    body_high = max(open_price, close_price)
    return body_low >= fvg.bottom and body_high <= fvg.top


def close_in_fvg_with_wick_touch(self, pin_bar_is_bullish, fvg):
    if pin_bar_is_bullish != fvg.is_bullish:
        return False

    _, close_price, _, _ = self._get_candle(0)
    close_in_fvg = fvg.bottom <= close_price <= fvg.top

    if pin_bar_is_bullish:
        return close_in_fvg and self.low <= fvg.top
    return close_in_fvg and self.high >= fvg.bottom


def overlap_fvg(self, pin_bar_is_bullish, fvg):
    if pin_bar_is_bullish != fvg.is_bullish:
        return False
    return self.high >= fvg.bottom and self.low <= fvg.top


VARIANTS = {
    "baseline_full_candle": baseline,
    "body_in_fvg": body_in_fvg,
    "close_in_fvg_with_wick_touch": close_in_fvg_with_wick_touch,
    "overlap_fvg": overlap_fvg,
}


def load_candles():
    with CACHE_PATH.open("rb") as f:
        candles_arr = np.array(pickle.load(f), dtype=float)
    return {
        f"{EXCHANGE}-{SYMBOL}": {
            "exchange": EXCHANGE,
            "symbol": SYMBOL,
            "candles": candles_arr,
        }
    }


def run_variant(name, fn, candles):
    original = SMC_FVG_PinBar._is_pin_bar_in_fvg
    SMC_FVG_PinBar._is_pin_bar_in_fvg = fn

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
        SMC_FVG_PinBar._is_pin_bar_in_fvg = original

    metrics = result["metrics"]
    trades = result.get("trades", [])
    return {
        "variant": name,
        "trades_count": len(trades),
        "total": metrics.get("total"),
        "net_profit_percentage": metrics.get("net_profit_percentage"),
        "max_drawdown": metrics.get("max_drawdown"),
        "win_rate": metrics.get("win_rate"),
        "first_trade": trades[0] if trades else None,
    }


def main():
    candles = load_candles()
    rows = []
    for name, fn in VARIANTS.items():
        rows.append(run_variant(name, fn, candles))
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
