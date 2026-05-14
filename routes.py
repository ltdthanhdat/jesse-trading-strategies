# Routes: symbol, timeframe, exchange, strategy.
# See: https://docs.jesse.trade/docs/routes

from strategies.SMC_FVG_PinBar import SMC_FVG_PinBar

# Routes configuration
routes = [
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "BTC-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "PLAY-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "BIO-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "SPACE-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "PENDLE-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "BR-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "BASED-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "D-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "YGG-USDT",
        "timeframe": "1h",
    },
    {
        "exchange": "Binance Futures",
        "strategy": SMC_FVG_PinBar,
        "symbol": "STG-USDT",
        "timeframe": "1h",
    },
]
