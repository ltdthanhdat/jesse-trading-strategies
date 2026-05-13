# Storage

## Layout

- `temp/`
  - legacy BTC research caches
  - giữ nguyên để không làm vỡ path cũ trong docs research

- `cache/all_futures/`
  - cache `1m` cho all-futures runs
  - file name:
    - `{start_ms}-{end_ms}-Binance Perpetual Futures-{symbol}.pickle`

- `results/all_futures/`
  - JSON / CSV kết quả all-futures

- `logs/`
  - log do Jesse sinh ra

## Seed data

- BTC research windows:
  - `uv run python scripts/seed_smc_fvg_pinbar_data.py --scope btc-research`

- all futures windows:
  - `uv run python scripts/seed_smc_fvg_pinbar_data.py --scope all-futures`

- chỉ seed 1 window:
  - `uv run python scripts/seed_smc_fvg_pinbar_data.py --scope all-futures --window recent_2026_03_01_to_2026_04_30`
