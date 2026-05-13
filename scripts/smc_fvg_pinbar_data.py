import io
import pickle
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree

import numpy as np
import requests


EXCHANGE = "Binance Perpetual Futures"
ROUTE_TIMEFRAME = "1h"
SOURCE_TIMEFRAME = "1m"
ARCHIVE_BUCKET_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ARCHIVE_BASE_URL = "https://data.binance.vision/data/futures/um/monthly/klines"

LEGACY_BTC_RESEARCH_CACHE_DIR = Path("storage/temp")
ALL_FUTURES_CACHE_DIR = Path("storage/cache/all_futures")
ALL_FUTURES_RESULTS_DIR = Path("storage/results/all_futures")


@dataclass(frozen=True)
class Window:
    name: str
    start_ms: int
    end_ms: int


BTC_RESEARCH_WINDOWS: List[Window] = [
    Window("btc_1703689200000_1704067140000", 1703689200000, 1704067140000),
    Window("btc_1703878200000_1704067140000", 1703878200000, 1704067140000),
    Window("baseline_2024_01_01_to_2024_03_01", 1704067200000, 1709337540000),
    Window("btc_1740495600000_1740873540000", 1740495600000, 1740873540000),
    Window("btc_1740873600000_1740959940000", 1740873600000, 1740959940000),
    Window("btc_1740873600000_1741046340000", 1740873600000, 1741046340000),
    Window("btc_1748617200000_1748995140000", 1748617200000, 1748995140000),
    Window("recent_2026_03_01_to_2026_03_31", 1772323200000, 1775001540000),
    Window("recent_2026_03_01_to_2026_04_30", 1772323200000, 1777593540000),
    Window("btc_1774245600000_1775001540000", 1774245600000, 1775001540000),
    Window("recent_2026_04_01_to_2026_04_30", 1775001600000, 1777593540000),
    Window("btc_1775001600000_1777679940000", 1775001600000, 1777679940000),
]

ALL_FUTURES_WINDOWS: List[Window] = [
    Window("baseline_2024_01_01_to_2024_03_01", 1704067200000, 1709337540000),
    Window("recent_2026_03_01_to_2026_04_30", 1772323200000, 1777593540000),
]


def format_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


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


def cache_path(cache_dir: Path, symbol: str, window: Window) -> Path:
    filename = f"{window.start_ms}-{window.end_ms}-{EXCHANGE}-{symbol}.pickle"
    return cache_dir / filename


def load_cache(path: Path) -> np.ndarray:
    with path.open("rb") as f:
        return np.array(pickle.load(f), dtype=float)


def is_valid_1m_cache(candles: np.ndarray) -> bool:
    return len(candles) >= 2 and int(candles[1][0] - candles[0][0]) == 60_000


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


def seed_symbol_windows(symbol: str, windows: List[Window], cache_dir: Path) -> Dict[str, Dict]:
    session = requests.Session()
    results: Dict[str, Dict] = {}
    try:
        for window in windows:
            path = cache_path(cache_dir, symbol, window)
            if path.exists():
                cached = load_cache(path)
                if is_valid_1m_cache(cached):
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
