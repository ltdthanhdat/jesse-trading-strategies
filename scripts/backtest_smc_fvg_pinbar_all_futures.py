import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

import numpy as np

from jesse.research.backtest import backtest
from smc_fvg_pinbar_data import (
    ALL_FUTURES_CACHE_DIR,
    ALL_FUTURES_RESULTS_DIR,
    ALL_FUTURES_WINDOWS,
    EXCHANGE,
    ROUTE_TIMEFRAME,
    Window,
    cache_path,
    format_utc,
    get_archive_symbols,
    load_cache,
    seed_symbol_windows,
)


def run_backtest(symbol: str, candles: np.ndarray) -> Dict:
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
                "symbol": symbol,
                "timeframe": ROUTE_TIMEFRAME,
            }
        ],
        data_routes=[],
        candles={
            f"{EXCHANGE}-{symbol}": {
                "exchange": EXCHANGE,
                "symbol": symbol,
                "candles": candles,
            }
        },
        warmup_candles=None,
        generate_equity_curve=False,
        fast_mode=False,
    )

    metrics = result["metrics"]
    trades = result.get("trades", [])
    return {
        "trades_count": len(trades),
        "net_profit_percentage": metrics.get("net_profit_percentage", 0),
        "max_drawdown": metrics.get("max_drawdown"),
        "win_rate": metrics.get("win_rate", 0),
    }


def summarize(rows: List[Dict], windows: List[Window]) -> Dict[str, Dict]:
    summary: Dict[str, Dict] = {}
    for window in windows:
        window_rows = [row for row in rows if row["window"] == window.name and row["status"] == "ok"]
        profitable = [row for row in window_rows if row["net_profit_percentage"] > 0]
        traded = [row for row in window_rows if row["trades_count"] > 0]
        summary[window.name] = {
            "symbols_tested": len(window_rows),
            "symbols_with_trades": len(traded),
            "profitable_symbols": len(profitable),
            "top_10_net_profit": sorted(
                [
                    {
                        "symbol": row["symbol"],
                        "net_profit_percentage": row["net_profit_percentage"],
                        "trades_count": row["trades_count"],
                        "win_rate": row["win_rate"],
                    }
                    for row in window_rows
                ],
                key=lambda item: item["net_profit_percentage"],
                reverse=True,
            )[:10],
            "bottom_10_net_profit": sorted(
                [
                    {
                        "symbol": row["symbol"],
                        "net_profit_percentage": row["net_profit_percentage"],
                        "trades_count": row["trades_count"],
                        "win_rate": row["win_rate"],
                    }
                    for row in window_rows
                ],
                key=lambda item: item["net_profit_percentage"],
            )[:10],
        }
    return summary


def write_results(rows: List[Dict], selected_windows: List) -> None:
    summary = summarize(rows, selected_windows)
    json_path = ALL_FUTURES_RESULTS_DIR / "smc_fvg_pinbar_all_futures_results.json"
    csv_path = ALL_FUTURES_RESULTS_DIR / "smc_fvg_pinbar_all_futures_results.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"windows": [window.__dict__ for window in selected_windows], "summary": summary, "rows": rows},
            f,
            ensure_ascii=False,
            indent=2,
        )

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--window",
        action="append",
        dest="windows",
        help="Run only selected window name. Can be passed multiple times.",
    )
    args = parser.parse_args()

    selected_windows = ALL_FUTURES_WINDOWS
    if args.windows:
        wanted = set(args.windows)
        selected_windows = [window for window in ALL_FUTURES_WINDOWS if window.name in wanted]
        if not selected_windows:
            raise ValueError(f"No matching windows. Available: {[window.name for window in ALL_FUTURES_WINDOWS]}")

    ALL_FUTURES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ALL_FUTURES_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    import requests
    with requests.Session() as session:
        symbols = get_archive_symbols(session)

    print(f"Found {len(symbols)} Binance USDT perpetual symbols in archive.")
    for window in selected_windows:
        print(f"- {window.name}: {format_utc(window.start_ms)} -> {format_utc(window.end_ms)}")

    rows: List[Dict] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(seed_symbol_windows, symbol, selected_windows, ALL_FUTURES_CACHE_DIR): symbol
            for symbol in symbols
        }

        for future in as_completed(future_map):
            symbol = future_map[future]
            completed += 1
            try:
                symbol_windows = future.result()
            except Exception as exc:
                for window in selected_windows:
                    rows.append(
                        {
                            "symbol": symbol,
                            "window": window.name,
                            "status": "fetch_error",
                            "error": str(exc),
                        }
                    )
                print(f"[{completed}/{len(symbols)}] {symbol}: fetch_error")
                continue

            per_symbol_status = []
            for window in selected_windows:
                window_result = symbol_windows[window.name]
                if "error" in window_result:
                    rows.append(
                        {
                            "symbol": symbol,
                            "window": window.name,
                            "status": "no_data",
                            "error": window_result["error"],
                        }
                    )
                    per_symbol_status.append(f"{window.name}=no_data")
                    continue

                path = Path(window_result["cache_path"])
                candles = load_cache(path)

                try:
                    metrics = run_backtest(symbol, candles)
                    rows.append(
                        {
                            "symbol": symbol,
                            "window": window.name,
                            "status": "ok",
                            "candles_count": window_result["count"],
                            "first_ts": window_result["first_ts"],
                            "last_ts": window_result["last_ts"],
                            "cache_path": window_result["cache_path"],
                            **metrics,
                        }
                    )
                    source_label = "cache" if window_result.get("from_cache") else "fetched"
                    per_symbol_status.append(
                        f"{window.name}={metrics['net_profit_percentage']:.4f}%/{metrics['trades_count']}t/{source_label}"
                    )
                except Exception as exc:
                    rows.append(
                        {
                            "symbol": symbol,
                            "window": window.name,
                            "status": "backtest_error",
                            "candles_count": window_result["count"],
                            "first_ts": window_result["first_ts"],
                            "last_ts": window_result["last_ts"],
                            "cache_path": window_result["cache_path"],
                            "error": str(exc),
                        }
                    )
                    per_symbol_status.append(f"{window.name}=backtest_error")

            print(f"[{completed}/{len(symbols)}] {symbol}: " + ", ".join(per_symbol_status))
            if completed % 25 == 0:
                write_results(rows, selected_windows)

    write_results(rows, selected_windows)
    summary = summarize(rows, selected_windows)

    print(f"Saved JSON results to {ALL_FUTURES_RESULTS_DIR / 'smc_fvg_pinbar_all_futures_results.json'}")
    print(f"Saved CSV results to {ALL_FUTURES_RESULTS_DIR / 'smc_fvg_pinbar_all_futures_results.csv'}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
