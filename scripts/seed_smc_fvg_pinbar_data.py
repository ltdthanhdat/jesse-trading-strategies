import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from smc_fvg_pinbar_data import (
    ALL_FUTURES_CACHE_DIR,
    ALL_FUTURES_WINDOWS,
    BTC_RESEARCH_WINDOWS,
    EXCHANGE,
    LEGACY_BTC_RESEARCH_CACHE_DIR,
    Window,
    format_utc,
    get_archive_symbols,
    seed_symbol_windows,
)


def resolve_windows(scope: str, names: list[str] | None) -> list[Window]:
    windows = BTC_RESEARCH_WINDOWS if scope == "btc-research" else ALL_FUTURES_WINDOWS
    if not names:
        return windows

    wanted = set(names)
    selected = [window for window in windows if window.name in wanted]
    if not selected:
        raise ValueError(f"No matching windows for {scope}. Available: {[window.name for window in windows]}")
    return selected


def run_btc_research_seed(windows: list[Window]) -> None:
    symbol = "BTC-USDT"
    LEGACY_BTC_RESEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    results = seed_symbol_windows(symbol, windows, LEGACY_BTC_RESEARCH_CACHE_DIR)

    print(f"BTC research seed for {symbol}")
    for window in windows:
        result = results[window.name]
        if "error" in result:
            print(f"- {window.name}: {result['error']}")
            continue
        source = "cache" if result.get("from_cache") else "fetched"
        print(
            f"- {window.name}: {result['count']} candles, "
            f"{format_utc(result['first_ts'])} -> {format_utc(result['last_ts'])}, {source}"
        )


def run_all_futures_seed(windows: list[Window], max_workers: int) -> None:
    ALL_FUTURES_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        symbols = get_archive_symbols(session)

    print(f"All futures seed for {len(symbols)} symbols")
    for window in windows:
        print(f"- {window.name}: {format_utc(window.start_ms)} -> {format_utc(window.end_ms)}")

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(seed_symbol_windows, symbol, windows, ALL_FUTURES_CACHE_DIR): symbol
            for symbol in symbols
        }
        for future in as_completed(future_map):
            symbol = future_map[future]
            completed += 1
            try:
                results = future.result()
            except Exception as exc:
                print(f"[{completed}/{len(symbols)}] {symbol}: error {exc}")
                continue

            parts = []
            for window in windows:
                result = results[window.name]
                if "error" in result:
                    parts.append(f"{window.name}=no_data")
                    continue
                source = "cache" if result.get("from_cache") else "fetched"
                parts.append(f"{window.name}={result['count']}m/{source}")
            print(f"[{completed}/{len(symbols)}] {symbol}: " + ", ".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=["btc-research", "all-futures", "all"],
        default="all",
    )
    parser.add_argument(
        "--window",
        action="append",
        dest="windows",
        help="Window name. Repeat to select multiple windows.",
    )
    parser.add_argument("--max-workers", type=int, default=8)
    args = parser.parse_args()

    if args.scope in {"btc-research", "all"}:
        run_btc_research_seed(resolve_windows("btc-research", args.windows))

    if args.scope in {"all-futures", "all"}:
        run_all_futures_seed(resolve_windows("all-futures", args.windows), args.max_workers)


if __name__ == "__main__":
    main()
