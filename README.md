# jessie-trading-strategies

Bộ strategy cho [Jesse](https://docs.jesse.trade/) dùng để nghiên cứu và backtest trên `BTC-USDT` futures.

## Có gì trong repo

- `EMA50_200`: vào lệnh theo EMA 50/200 crossover, stop loss theo nến hiện tại, take profit `1R`.
- `SMC_FVG_PinBar`: vào lệnh theo Fair Value Gap + Pin Bar, stop loss theo biên FVG, take profit `1R`.
- `routes.py`: đang cấu hình cả hai strategy trên `Binance Futures`, timeframe `1h`.

## Yêu cầu

- Python `>=3.10,<3.14`
- PostgreSQL
- Redis
- Docker + Docker Compose nếu muốn chạy nhanh toàn bộ dependency

## Cài đặt

1. Tạo file môi trường:

```bash
cp .env.example .env
```

2. Nếu chạy dependency bằng Docker Compose, giữ:

```env
POSTGRES_HOST=postgres
REDIS_HOST=redis
```

3. Nếu PostgreSQL và Redis chạy sẵn trên máy, dùng:

```env
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

4. Đồng bộ môi trường Python:

```bash
make sync
```

## Chạy services phụ trợ

Khởi động PostgreSQL và Redis:

```bash
make up
```

Kiểm tra trạng thái:

```bash
make ps
```

## Chạy Jesse

Sau khi dependency đã sẵn sàng:

```bash
make run
```

Ứng dụng mặc định chạy ở `http://localhost:9000`.

## Các lệnh tiện dụng

```bash
make help
make sync
make up
make down
make ps
make check
make run
```

## Cấu hình nhanh

- App port: `APP_PORT`
- LSP port: `LSP_PORT`
- Database name: `POSTGRES_NAME`
- Database user: `POSTGRES_USERNAME`
- Database password: `POSTGRES_PASSWORD`
- Redis port: `REDIS_PORT`
- Dashboard password: `PASSWORD`

Xem file mẫu tại [.env.example](/home/datlt/workspace/jesse-trading-strategies/.env.example:1).

## File quan trọng

- [pyproject.toml](/home/datlt/workspace/jesse-trading-strategies/pyproject.toml:1)
- [routes.py](/home/datlt/workspace/jesse-trading-strategies/routes.py:1)
- [strategies/EMA50_200/__init__.py](/home/datlt/workspace/jesse-trading-strategies/strategies/EMA50_200/__init__.py:1)
- [strategies/SMC_FVG_PinBar/__init__.py](/home/datlt/workspace/jesse-trading-strategies/strategies/SMC_FVG_PinBar/__init__.py:1)
- [docker-compose.yml](/home/datlt/workspace/jesse-trading-strategies/docker-compose.yml:1)

## Ghi chú vận hành

- Sau khi đổi tên thư mục project, một số script trong `.venv/bin/` có thể giữ shebang cũ. Nếu `./.venv/bin/jesse` lỗi đường dẫn Python, chạy lại `uv sync` hoặc tạo lại `.venv`.
- Repo hiện không có test suite riêng; kiểm tra cơ bản nên bắt đầu từ `py_compile`, `jesse run`, rồi backtest trong giao diện Jesse.
