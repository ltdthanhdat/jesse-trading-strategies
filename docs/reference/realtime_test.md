# Realtime Test Cutover

Mục tiêu:
- giữ nguyên logic strategy hiện tại
- dừng research loop
- chuyển sang test account trước khi nghĩ tới live money

## Current rollout choice

- strategy: `SMC_FVG_PinBar`
- route mặc định hiện tại: `BTC-USDT`, `1h`, `Binance Futures`
- lý do:
  - đây là route đang có sẵn trong [routes.py](/home/thanhdatle/workspace/jesse-trading-strategies/routes.py:1)
  - an toàn hơn việc nhảy thẳng sang basket nhiều symbol
  - không phụ thuộc tier license có hỗ trợ nhiều trading routes hay không

Nếu account/license của Jesse hỗ trợ nhiều routes và muốn mở rộng sau khi test ổn:
- basket research gần nhất:
  - `PLAY-USDT`
  - `BIO-USDT`
  - `SPACE-USDT`
  - `PENDLE-USDT`
  - `BR-USDT`
  - `BASED-USDT`
  - `D-USDT`
  - `YGG-USDT`
  - `STG-USDT`
  - `我踏马来了-USDT`
  - `BTC-USDT`

## Preconditions

- có `LICENSE_API_TOKEN` trong `.env`
- có account testnet hoặc paper account tương thích với license/plugin Jesse
- PostgreSQL và Redis chạy được
- đã hiểu rằng `jesse_live` chưa cài nếu chưa chạy `uv run jesse install-live`

## Steps

1. Dọn artifacts research:

```bash
make clean-research
```

2. Khởi động dependencies:

```bash
make up
```

3. Cài live plugin:

```bash
uv run jesse install-live
```

4. Chạy app:

```bash
make run
```

5. Mở dashboard:

- URL: `http://127.0.0.1:9000/`
- password: lấy từ `.env`

6. Trong dashboard/live plugin:

- thêm test account
- chọn exchange testnet hoặc paper mode phù hợp với license/plugin của bạn
- dùng route hiện tại trong `routes.py`
- start session với size nhỏ nhất có thể

## Known blocker right now

Hiện tại repo này chưa có `LICENSE_API_TOKEN` trong `.env`, nên bước `uv run jesse install-live` sẽ không chạy tiếp được.

## Notes

- Không mở rộng sang `11` symbol ngay ở vòng đầu.
- Không đổi strategy logic trong phase này.
- Nếu plugin/license chỉ cho `1` route, giữ nguyên `BTC-USDT 1h` cho vòng test đầu tiên.
