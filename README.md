# Jesse Trading — EMA 50/200

Project Jesse với strategy EMA 50/200 crossover. Interactive chart dùng **built-in của Jesse** (EMA 50/200 vẽ trên candle chart).

## Cấu trúc

```
├── pyproject.toml        # Dependency (uv)
├── .python-version       # Python 3.12
├── docker-compose.yml    # PostgreSQL + Redis
├── routes.py             # Route (exchange, symbol, timeframe, strategy)
├── strategies/
│   └── EMA50_200/
│       └── __init__.py   # Strategy + add_line_to_candle_chart (EMA 50/200)
├── storage/
├── .env.example
└── README.md
```

## Yêu cầu

- Python >= 3.10, <= 3.13
- [uv](https://docs.astral.sh/uv/) để quản lý dependency
- **Redis >= 5, PostgreSQL >= 10**: **Bắt buộc** khi chạy dashboard (`jesse run`). **Không cần** nếu chỉ dùng research mode (backtest trong Python script với synthetic candles).

**PostgreSQL**: Jesse lưu **nến** (candle) chủ yếu khung 1m, từ đó tạo các timeframe khác. Backtest trên dashboard đọc nến từ DB; import nến (CSV hoặc API sàn) cũng ghi vào đây.

**Redis**: Dùng cho **trạng thái runtime** của dashboard (process, session). Cần khi chạy `jesse run` để UI và backtest chạy ổn định.

**Research mode** (`jesse.research.backtest`): Pure function, không cần DB/Redis. Chỉ cần truyền candles (có thể synthetic) vào hàm. Xem [Research Backtest](https://docs.jesse.trade/docs/research/backtest.html).

## Thiết lập (uv)

```bash
# Cài uv (nếu chưa có): curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

Mọi lệnh chạy trong môi trường ảo của uv: `uv run python ...`, hoặc `uv run jesse run`.

## Chạy backtest và Interactive chart

1. Copy env: `cp .env.example .env` (đã cấu hình cho docker-compose).
2. Khởi động PostgreSQL + Redis: `docker compose up -d`.
   
   **Nếu không dùng Docker**: Sửa `.env` → `POSTGRES_HOST=localhost`, `REDIS_HOST=localhost` và cài PostgreSQL + Redis trên máy.
3. Chạy Jesse: `uv run jesse run`.
4. Mở http://localhost:9000 → tab **Backtest**.
5. Chọn route (EMA50_200, BTC-USDT, 1h), khoảng thời gian, **bật "Interactive charts"** rồi chạy backtest.
6. Sau khi chạy xong, mở **interactive chart**: chart nến hiển thị điểm mua/bán và **EMA 50, EMA 200** (strategy gọi `add_line_to_candle_chart` trong `after()`). Zoom/pan trực tiếp trên chart.

**Dừng services**: `docker compose down` (hoặc `docker compose down -v` để xóa data).

## Seed data nến

Cần nến trong DB thì backtest trên dashboard mới chạy được.

**Cách khuyến nghị (đơn giản)** — dùng ngay trong dashboard:

1. Chạy `uv run jesse run`, mở http://localhost:9000.
2. Vào trang **Import Candles**.
3. Chọn **Exchange** (vd: Binance Futures), **Symbol** (vd: BTC-USDT), **Start Date** (vd: 2024-01-01).
4. Bấm import. Jesse sẽ tải nến **1m** từ sàn đến **hôm nay**. Nến trùng sẽ bị bỏ qua nên có thể chạy lại để cập nhật.

**Lưu ý**: Jesse chỉ lưu nến **1m**; các timeframe khác (1h, 4h, …) được tạo từ 1m khi backtest.

Docs: [Importing Candles](https://docs.jesse.trade/docs/import-candles.html), [Research Candles](https://docs.jesse.trade/docs/research/candles.html).

## Strategy EMA50_200

- **Long**: khi EMA 50 > EMA 200 (golden cross).
- **Short**: khi EMA 50 < EMA 200 (death cross).
- **Position size**: risk 2% balance, tối đa 25% vốn mỗi lệnh; dùng `utils.risk_to_qty` và `fee_rate`.
- **Stop / take profit**: ATR (2x ATR stop, 3x ATR target).
- **Exit**: `update_position()` đóng lệnh khi tín hiệu đảo chiều (EMA cross ngược lại).

Docs: [Jesse Strategies](https://docs.jesse.trade/docs/strategies/), [Example strategies](https://github.com/jesse-ai/example-strategies).
