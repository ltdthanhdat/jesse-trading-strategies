import argparse
import csv
import io
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree
import zipfile

import numpy as np
import requests

from jesse.research.backtest import backtest


EXCHANGE = "Binance Perpetual Futures"
ROUTE_TIMEFRAME = "1h"
SOURCE_TIMEFRAME = "1m"
ARCHIVE_BUCKET_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ARCHIVE_BASE_URL = "https://data.binance.vision/data/futures/um/monthly/klines"

OUTPUT_DIR = Path("storage/temp/all_futures")
RESULTS_DIR = Path("storage/results")


@dataclass(frozen=True)
class Window:
    name: str
    start_ms: int
    end_ms: int


WINDOWS: List[Window] = [
    Window(
        name="baseline_2024_01_01_to_2024_03_01",
        start_ms=1704067200000,
        end_ms=1709337540000,
    ),
    Window(
        name="recent_2026_03_01_to_2026_04_30",
        start_ms=1772323200000,
        end_ms=1777593540000,
    ),
]


def format_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def cache_path(symbol: str, window: Window) -> Path:
    filename = f"{window.start_ms}-{window.end_ms}-{EXCHANGE}-{symbol}.pickle"
    return OUTPUT_DIR / filename


def month_start(ms: int) -> datetime:
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def covered_months(window: Window) -> List[str]:
    months = []
    current = month_start(window.start_ms)
    end = month_start(window.end_ms)
    while current <= end:
        months.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months


def get_archive_symbols(session: requests.Session) -> List[str]:
    token = None
    dashy_symbols = []
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

    while True:
        params = {
            "list-type": "2",
            "delimiter": "/",
            "prefix": "data/futures/um/monthly/klines/",
        }
        if token:
            params["continuation-token"] = token

        response = session.get(ARCHIVE_BUCKET_URL, params=params, timeout=30)
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)

        for item in root.findall("s3:CommonPrefixes", ns):
            prefix = item.find("s3:Prefix", ns)
            if prefix is None:
                continue
            symbol = prefix.text.rstrip("/").split("/")[-1]
            if not symbol.endswith("USDT"):
                continue
            base = symbol[:-4]
            dashy_symbols.append(f"{base}-USDT")

        truncated = root.findtext("s3:IsTruncated", default="false", namespaces=ns) == "true"
        if not truncated:
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
        if not token:
            break

    return sorted(set(dashy_symbols))


def fetch_1m_candles(session: requests.Session, symbol: str, window: Window) -> Tuple[Optional[np.ndarray], Optional[str]]:
    dashless = symbol.replace("-", "")
    merged_rows = []

    for month in covered_months(window):
        url = f"{ARCHIVE_BASE_URL}/{dashless}/{SOURCE_TIMEFRAME}/{dashless}-{SOURCE_TIMEFRAME}-{month}.zip"
        response = session.get(url, timeout=60)
        if response.status_code == 404:
            continue
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for name in zf.namelist():
                with zf.open(name) as f:
                    for raw_line in f:
                        line = raw_line.decode("utf-8").strip()
                        if not line:
                            continue
                        parts = line.split(",")
                        if not parts[0].isdigit():
                            continue
                        open_time = int(parts[0])
                        if open_time < window.start_ms or open_time > window.end_ms:
                            continue
                        merged_rows.append(parts)

    if not merged_rows:
        return None, "no_candles"

    candles = np.array(
        [
            [
                float(row[0]),
                float(row[1]),
                float(row[4]),
                float(row[2]),
                float(row[3]),
                float(row[5]),
            ]
            for row in merged_rows
            if int(row[0]) <= window.end_ms
        ],
        dtype=float,
    )

    if len(candles) == 0:
        return None, "no_candles_in_window"

    return candles, None


def fetch_symbol_windows(symbol: str, windows: List[Window]) -> Dict[str, Dict]:
    session = requests.Session()
    results: Dict[str, Dict] = {}
    try:
        for window in windows:
            path = cache_path(symbol, window)
            if path.exists():
                with path.open("rb") as f:
                    cached = np.array(pickle.load(f), dtype=float)
                is_valid_1m_cache = len(cached) >= 2 and int(cached[1][0] - cached[0][0]) == 60_000
                if is_valid_1m_cache:
                    results[window.name] = {
                        "count": len(cached),
                        "first_ts": int(cached[0][0]) if len(cached) else None,
                        "last_ts": int(cached[-1][0]) if len(cached) else None,
                        "cache_path": str(path),
                        "from_cache": True,
                    }
                    continue
                path.unlink()

            candles, error = fetch_1m_candles(session, symbol, window)
            if candles is None:
                results[window.name] = {"error": error}
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as f:
                pickle.dump(candles.tolist(), f)

            results[window.name] = {
                "count": len(candles),
                "first_ts": int(candles[0][0]),
                "last_ts": int(candles[-1][0]),
                "cache_path": str(path),
                "from_cache": False,
            }
    finally:
        session.close()

    return results


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


def write_results(rows: List[Dict], selected_windows: List[Window]) -> None:
    summary = summarize(rows, selected_windows)
    json_path = RESULTS_DIR / "smc_fvg_pinbar_all_futures_results.json"
    csv_path = RESULTS_DIR / "smc_fvg_pinbar_all_futures_results.csv"

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

    selected_windows = WINDOWS
    if args.windows:
        wanted = set(args.windows)
        selected_windows = [window for window in WINDOWS if window.name in wanted]
        if not selected_windows:
            raise ValueError(f"No matching windows. Available: {[window.name for window in WINDOWS]}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    try:
        symbols = get_archive_symbols(session)
    finally:
        session.close()

    print(f"Found {len(symbols)} Binance USDT perpetual symbols in archive.")
    for window in selected_windows:
        print(f"- {window.name}: {format_utc(window.start_ms)} -> {format_utc(window.end_ms)}")

    rows: List[Dict] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(fetch_symbol_windows, symbol, selected_windows): symbol
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
                with path.open("rb") as f:
                    candles = np.array(pickle.load(f), dtype=float)

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

    print(f"Saved JSON results to {RESULTS_DIR / 'smc_fvg_pinbar_all_futures_results.json'}")
    print(f"Saved CSV results to {RESULTS_DIR / 'smc_fvg_pinbar_all_futures_results.csv'}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
