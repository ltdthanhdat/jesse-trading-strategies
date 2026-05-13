# SMC_FVG_PinBar Autoresearch Tuning Plan

Trạng thái:
- active
- containment phase đã xong
- phase tiếp theo: tune `pin bar detection`

Mục tiêu:
- Ứng dụng tư duy của `karpathy/autoresearch` vào việc tune logic vào lệnh của `SMC_FVG_PinBar`.
- Không tune tràn lan.
- Ở trạng thái hiện tại, chỉ tập trung vào `pin bar detection`.

Plan này không cố bê nguyên repo `autoresearch` sang.
Plan này chỉ mượn framework làm research:
- scope nhỏ
- metric rõ
- mỗi vòng chỉ đổi rất ít
- chạy experiment ngắn, giữ hoặc bỏ
- ghi log kết quả có cấu trúc

## Ý tưởng mượn từ `autoresearch`

Những ý chính nên áp dụng:

1. Chỉ cho phép thay đổi rất ít chỗ
- Trong `autoresearch`, agent chủ yếu iterate trên một file.
- Ở repo này, nên làm tương tự:
  - chỉ cho phép sửa `strategies/SMC_FVG_PinBar/__init__.py`
  - không đụng `routes.py`
  - không đụng hạ tầng backtest

2. Mỗi experiment phải comparable
- `autoresearch` dùng budget cố định và metric cố định.
- Ở đây phải cố định:
  - exchange
  - symbol
  - timeframe
  - dataset
  - starting balance
  - fee
  - warmup

3. Mỗi vòng chỉ đổi 1 ý
- Không đổi đồng thời:
  - pin bar detection
  - FVG detection
  - exit logic
  - position sizing
- Một experiment chỉ đổi đúng 1 nhóm rule entry.

4. Keep / discard rõ ràng
- Nếu metric tốt hơn theo tiêu chí đã định thì giữ lại.
- Nếu không thì bỏ.
- Không merge cảm tính vì “trông có vẻ hợp lý”.

## Scope của tuning

Cho phase này, khóa cứng các phần sau:
- FVG detection
- FVG mitigation
- overlap FVG entry rule
- stop loss logic
- take profit logic
- qty logic
- timeframe `1h`
- exchange `Binance Perpetual Futures`
- symbol `BTC-USDT`

Chỉ cho phép tune:
- `_is_pin_bar()`
- nếu cần, tách helper pin bar variant riêng

Không cho phép tune trong phase này:
- `_is_pin_bar_in_fvg()`
- `go_long()`
- `go_short()`
- `update_position()`

## Baseline

Baseline hiện tại:
- logic FVG đã bám Pine hơn:
  - FVG không hết hạn theo số nến
  - chỉ bị remove khi mitigated hoàn toàn
- logic entry hiện tại:
  - pin bar chỉ cần overlap FVG:
    - `high >= fvg.bottom`
    - `low <= fvg.top`

Baseline result trên dataset hiện có:
- khoảng `2024-01-01` đến `2024-03-01`
- `3 trades`
- xem chi tiết tại:
  - `docs/research/smc_fvg_pinbar_backtest_results.md`

## Research question

Câu hỏi chính:
- Liệu strategy đang ít trade vì `pin bar detection` quá chặt?

Câu hỏi phụ:
- Variant pin bar nào tăng trade hợp lý mà không làm strategy spam trade?

## Candidate variants

Chạy theo thứ tự từ chặt đến lỏng.

### Variant 0: Current pin bar

Đây là baseline hiện tại.

Mục đích:
- mốc để so sánh

### Variant 1: Loose wick/body ratio

Ý tưởng:
- giảm ngưỡng `PIN_BAR_WICK_TO_BODY`
- hoặc nới `PIN_BAR_BODY_RATIO`

Mục đích:
- xem pin bar hiện tại có đang quá strict không

### Variant 2: Bỏ ràng buộc màu nến

Ý tưởng:
- bullish pin bar không bắt buộc `close > open`
- bearish pin bar không bắt buộc `close < open`

Mục đích:
- cho phép hammer / shooting star màu ngược

### Variant 3: Chỉ cần close near extreme + wick dominance

Ý tưởng:
- giữ điều kiện wick dài
- giữ close near high / close near low
- bỏ bớt constraint body position quá chặt

Mục đích:
- test một phiên bản pin bar theo intent thay vì theo hình học quá cứng

### Variant 4: Score-based pin bar

Ý tưởng:
- không dùng toàn bộ điều kiện cứng kiểu all-or-nothing
- chấm điểm:
  - wick/body
  - close near extreme
  - small body
- đạt ngưỡng thì nhận là pin bar

Mục đích:
- chỉ dùng nếu 3 variant trên vẫn quá ít trade

## Evaluation metrics

Không dùng duy nhất PnL.

Metric chính:
- `trades_count`
- `net_profit_percentage`
- `max_drawdown`
- `win_rate`

Metric phụ:
- `average_holding_period`
- phân bổ `long/short`
- số setup xuất hiện trước khi khớp lệnh

Metric kiểm soát chất lượng:
- số trade tăng lên bao nhiêu lần so với baseline
- drawdown có tăng đột biến không
- có xuất hiện nhiều trade sát nhau bất thường không

## Decision rule

Không chọn variant chỉ vì có nhiều trade hơn.

Ưu tiên chọn variant nếu:
- `trades_count` tăng rõ
- `max_drawdown` không xấu đi quá mạnh
- `net_profit_percentage` không sụp
- logic còn dễ giải thích bằng SMC/FVG, không bị quá loose

Loại variant nếu:
- trade count tăng mạnh nhưng drawdown xấu rõ
- tạo nhiều trade “rác”
- khó giải thích bằng intent ban đầu của setup

## Experiment loop kiểu autoresearch

Mỗi vòng research làm đúng quy trình này:

1. Copy baseline result
   - verify: có số liệu gốc để so

2. Chọn đúng 1 variant
   - verify: diff chỉ chạm vào entry rule

3. Chạy backtest trên cùng dataset
   - verify: config không đổi

4. Ghi output vào log
   - metrics
   - số trade
   - 3 trade mẫu đầu tiên nếu có

5. So với baseline
   - keep
   - discard

6. Chỉ khi variant thắng mới chuyển sang branch thử tiếp
   - không stack nhiều thay đổi chưa chứng minh

## Phase execution

### Phase 1: Manual bounded sweep

Chưa dùng agent loop tự động.

Chạy tay vài variant pin bar:
- baseline
- loose_wick_body_ratio
- no_color_requirement
- close_near_extreme_wick_dominance

Mục tiêu:
- xác định vùng khả thi

### Phase 2: Semi-automated experiment harness

Nếu Phase 1 cho tín hiệu tốt, tạo harness nhỏ:
- 1 script sinh patch variant
- 1 script chạy backtest
- 1 file log JSON/CSV kết quả

Nhưng vẫn giữ:
- code thay đổi trong 1 file
- 1 lần chỉ 1 variant

### Phase 3: Agent-driven loop

Chỉ làm khi:
- Phase 1 xác nhận tuning entry thực sự có ích
- repo đã có harness ổn định

Khi đó mới cho agent loop:
- đọc baseline
- đề xuất 1 variant nhỏ
- patch
- run
- parse metrics
- keep/discard

## File structure đề xuất

Nếu triển khai theo hướng này, nên thêm:

```text
docs/plans/
  smc_fvg_pinbar_autoresearch_plan.md
  smc_fvg_pinbar_test_log.md

scripts/
  run_smc_fvg_pinbar_backtest.py
  sweep_smc_fvg_pinbar_entry_variants.py
```

## Constraints cho agent

Nếu sau này dùng agent loop, phải khóa chặt:

- Chỉ sửa:
  - `strategies/SMC_FVG_PinBar/__init__.py`
- Không được sửa:
  - `routes.py`
  - `Makefile`
  - infra
  - DB config
- Không được đồng thời đổi:
  - pin bar rule
  - stop loss
  - take profit
  - qty

## Output format cho mỗi experiment

```text
Experiment:
- variant:
- hypothesis:

Code change:
- file:
- function:

Backtest setup:
- exchange:
- symbol:
- timeframe:
- start:
- finish:

Result:
- trades_count:
- net_profit_percentage:
- max_drawdown:
- win_rate:
- keep_or_discard:
- notes:
```

## Next step

Bước tiếp theo hợp lý nhất:

1. Implement harness nhỏ để chạy 4 variant của Plan 2
   - verify: có bảng so sánh gọn cho pin bar variants
2. Chọn 1 variant pin bar thắng
   - verify: thắng trên cùng dataset
3. Chỉ sau đó mới nghĩ đến agent loop kiểu `autoresearch`
   - verify: tránh automate cái chưa có objective rõ
