# jessie-trading-strategies

Bộ strategy cho [Jesse](https://docs.jesse.trade/) dùng để nghiên cứu và backtest trên `BTC-USDT` futures.

## Có gì trong repo

- `SMC_FVG_PinBar`: vào lệnh theo Fair Value Gap + Pin Bar, stop loss theo biên FVG, take profit `1R`.
- `routes.py`: đang cấu hình `SMC_FVG_PinBar` trên `Binance Futures`, timeframe `1h`.

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

## Live Trade

Repo hiện mới ở trạng thái `ready for cutover`, chưa thể cài live plugin nếu thiếu `LICENSE_API_TOKEN` trong `.env`.

Flow tối thiểu:

```bash
cp .env.example .env
# điền LICENSE_API_TOKEN
# nếu muốn, chừa sẵn BINANCE_* trong .env để thêm sau
make up
uv run jesse install-live
make run
```

Runbook chi tiết: [docs/reference/realtime_test.md](docs/reference/realtime_test.md)

## Các lệnh tiện dụng

```bash
make help
make sync
make up
make down
make ps
make check
make clean-research
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

Xem file mẫu tại [.env.example](.env.example).

## File quan trọng

- [pyproject.toml](pyproject.toml)
- [routes.py](routes.py)
- [strategies/SMC_FVG_PinBar/__init__.py](strategies/SMC_FVG_PinBar/__init__.py)
- [docker-compose.yml](docker-compose.yml)
- [storage/README.md](storage/README.md)

## Ghi chú vận hành

- Sau khi đổi tên thư mục project hoặc đổi máy, nếu môi trường Python bị lệch, chạy lại `uv sync`.
- Repo hiện không có test suite riêng; kiểm tra cơ bản nên bắt đầu từ `py_compile`, `jesse run`, rồi backtest trong giao diện Jesse.
- `make clean-research` sẽ xóa artifacts batch backtest sinh ra trong `storage/cache`, `storage/results/all_futures`, và recent temp caches không còn cần cho phase realtime.
