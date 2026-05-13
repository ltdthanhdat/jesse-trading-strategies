# AGENTS.md

Quy ước khi viết hoặc cập nhật tài liệu trong `docs/`.

## Mục tiêu

- Không trộn `plan`, `debug note`, `research result`, `reference` vào cùng một file.
- File mới phải đặt đúng chỗ ngay từ đầu.
- Ưu tiên update file hiện có nếu cùng mục đích, không tạo thêm file gần giống nhau.

## Cấu trúc

- `docs/plans/`
  - kế hoạch làm việc
  - hypothesis
  - biến test
  - tiêu chí pass/fail

- `docs/notes/`
  - debug note ngắn
  - trạng thái hiện tại
  - bug đã sửa
  - blocker còn lại

- `docs/research/`
  - kết quả backtest
  - sweep result
  - benchmark
  - so sánh giữa các variant

- `docs/reference/`
  - tài liệu tham chiếu tương đối ổn định
  - ví dụ: access, template, pine script, external reference notes

## Rule viết file

- Nếu là kế hoạch:
  - viết vào `docs/plans/`

- Nếu là log debug / note làm việc:
  - viết vào `docs/notes/`

- Nếu là số liệu hoặc kết quả test:
  - viết vào `docs/research/`

- Nếu là tài liệu mẫu hoặc reference:
  - viết vào `docs/reference/`

## Naming

- Dùng prefix theo strategy hoặc chủ đề.
- Ví dụ:
  - `smc_fvg_pinbar_test_plan.md`
  - `smc_fvg_pinbar_autoresearch_plan.md`
  - `smc_fvg_pinbar_notes.md`
  - `smc_fvg_pinbar_backtest_results.md`

## Không làm

- Không tạo file mới chỉ vì tên cũ chưa đẹp.
- Không để một file vừa là plan vừa là result.
- Không ghi số liệu dài vào file debug note.
- Không tạo nhiều file khác nhau cho cùng một đợt test nếu chỉ khác chút wording.

## Khi chưa có thư mục đúng

- Tạo thư mục đúng trước.
- Sau đó mới tạo file.

## Ưu tiên

1. Update file hiện có cùng mục đích.
2. Nếu chưa có, tạo file mới đúng thư mục.
3. Nếu tài liệu cũ sai mục đích, đề xuất move thay vì copy.
