# Routes: symbol, timeframe, exchange, strategy.
# See: https://docs.jesse.trade/docs/routes

from strategies.EMA50_200 import EMA50_200
from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar

# Routes configuration
routes = [
    {
        "exchange": "Binance Futures",
        "strategy": EMA50_200,
        "symbol": "BTC-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "BTC-USDT",
        "timeframe": "1h",
    },
]
