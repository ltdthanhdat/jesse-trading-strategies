# Plan: Strategy SMC với FVG + Pin Bar

## Tổng quan
Strategy SMC (Smart Money Concept) vào lệnh khi có **FVG (Fair Value Gap) + Pin Bar**, với stop loss đặt dưới FVG (long) hoặc trên FVG (short), và R:R = 1:1.

## Cấu trúc Strategy

### 1. Indicators & Detection

#### 1.1 FVG Detection
- **Bullish FVG**: `high[3] < low[1]` (khoảng trống giá tăng)
  - Top: `low[1]`
  - Bottom: `high[3]`
- **Bearish FVG**: `low[3] > high[1]` (khoảng trống giá giảm)
  - Top: `low[3]`
  - Bottom: `high[1]`

Lưu FVG vào list để theo dõi và vẽ trên chart. FVG bị mitigated khi giá fill vào khoảng trống.

#### 1.2 Pin Bar Detection
Pin Bar là nến có:
- **Bullish Pin Bar**: 
  - Lower wick dài (ít nhất 2x body)
  - Body nhỏ ở phần trên của nến
  - Close gần high
- **Bearish Pin Bar**:
  - Upper wick dài (ít nhất 2x body)
  - Body nhỏ ở phần dưới của nến
  - Close gần low

Công thức:
```python
body = abs(close - open)
upper_wick = high - max(close, open)
lower_wick = min(close, open) - low
total_range = high - low

# Bullish Pin Bar
is_bullish_pin = lower_wick >= 2 * body and body < total_range * 0.3 and close > open * 0.6

# Bearish Pin Bar  
is_bearish_pin = upper_wick >= 2 * body and body < total_range * 0.3 and close < open * 1.4
```

#### 1.3 Scope hiện tại
- Strategy hiện chỉ dùng:
  - FVG detection
  - Pin Bar detection
  - Entry theo Pin Bar nằm trong FVG còn hiệu lực
- BOS/CHoCH không nằm trong logic vào lệnh hiện tại.

### 2. Entry Logic

#### 2.1 Long Entry (`should_long()`)
Điều kiện:
1. Không có position đang mở
2. Có **Bullish FVG** gần đây (chưa bị mitigated)
3. Nến hiện tại là **Bullish Pin Bar**
4. Pin Bar nằm **trong** FVG: `low >= FVG_bottom` và `high <= FVG_top`

#### 2.2 Short Entry (`should_short()`)
Điều kiện:
1. Không có position đang mở
2. Có **Bearish FVG** gần đây (chưa bị mitigated)
3. Nến hiện tại là **Bearish Pin Bar**
4. Pin Bar nằm **trong** FVG: `low >= FVG_bottom` và `high <= FVG_top`

### 3. Position Management

#### 3.1 Long Position (`go_long()`)
- **Entry**: Giá hiện tại (close của Pin Bar)
- **Stop Loss**: Dưới FVG bottom (`high[3]` của FVG)
- **Take Profit**: R:R = 1:1 → `entry + (entry - stop_loss)`
- **Position Size**: Risk 2% balance (giống EMA50_200)

#### 3.2 Short Position (`go_short()`)
- **Entry**: Giá hiện tại (close của Pin Bar)
- **Stop Loss**: Trên FVG top (`low[3]` của FVG)
- **Take Profit**: R:R = 1:1 → `entry - (stop_loss - entry)`
- **Position Size**: Risk 2% balance

### 4. Exit Logic (`update_position()`)
- Exit qua stop loss hoặc take profit
- Exit khi FVG bị mitigated hoàn toàn:
  - Long: FVG bị mitigated khi `low <= FVG_bottom`
  - Short: FVG bị mitigated khi `high >= FVG_top`

### 5. Interactive Chart Plotting (`after()`)

Jesse chỉ hỗ trợ `add_line_to_candle_chart()` để vẽ đường thẳng, không có box như Pine Script. 

**Lưu ý**: Jesse xem toàn bộ lịch sử sau khi backtest, nên cần plot hợp lý để không làm chart rối.

**Cách plot:**

1. **FVG Lines**: 
   - Vẽ 2 đường ngang cho mỗi FVG (top và bottom) khi FVG được detect
   - Màu xanh cho bullish FVG, đỏ cho bearish FVG
   - Có thể dùng label hoặc chỉ vẽ đường

**Lưu ý**: Hiện tại chỉ plot FVG lines.

## Implementation Steps

1. ✅ Tạo folder `strategies/SMC_FVG_PinBar/`
2. ✅ Tạo `__init__.py` với class `SMC_FVG_PinBar(Strategy)`
3. ✅ Implement FVG detection và storage
4. ✅ Implement Pin Bar detection
5. ✅ Implement entry logic (should_long/short)
6. ✅ Implement position management (go_long/short)
7. ✅ Implement plotting trong `after()`
8. ✅ Update `routes.py` để thêm strategy mới
9. ✅ Test và debug

## Files Structure

```
strategies/
└── SMC_FVG_PinBar/
    └── __init__.py   # Strategy implementation
```

## Notes

- FVG cần được lưu trong list để track mitigation
- Pin Bar detection có thể cần fine-tune parameters
- Interactive chart chỉ hỗ trợ lines, không có boxes như Pine Script
- Có thể thêm các parameters để điều chỉnh (pin bar ratio, FVG lookback, etc.)
