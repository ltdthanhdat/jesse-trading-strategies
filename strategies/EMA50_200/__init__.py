"""
EMA 50/200 Crossover Strategy

- Long when fast EMA (50) crosses above slow EMA (200) (golden cross).
- Short when fast EMA crosses below slow EMA (death cross).
- Position size via risk_percent of balance.
- Stop loss: giá thấp nhất (low) cho long, giá cao nhất (high) cho short.
- Take profit: R:R = 1:1 (take profit = entry + (entry - stop) cho long, entry - (stop - entry) cho short).
- Exit chỉ qua stop loss hoặc take profit (không exit sớm qua update_position).
- Uses @cached for indicator performance.
"""

from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils


class EMA50_200(Strategy):
    # --- Indicators (cached to avoid recompute each candle) ---
    @property
    @cached
    def ema_fast(self):
        return ta.ema(self.candles, 50, sequential=True)

    @property
    @cached
    def ema_slow(self):
        return ta.ema(self.candles, 200, sequential=True)

    # --- Entry: crossover signals (chỉ vào khi có cross thực sự) ---
    # Chỉ vào lệnh mới khi đã exit lệnh trước (không có position đang mở)
    def should_long(self) -> bool:
        # Chỉ vào long khi không có position đang mở
        if self.is_open:
            return False
        # Cần ít nhất 2 giá trị để detect crossover
        if len(self.ema_fast) < 2 or len(self.ema_slow) < 2:
            return False
        # Golden cross: EMA fast cross từ dưới lên trên EMA slow
        # Hiện tại: fast > slow, trước đó: fast <= slow
        ema_fast_now = self.ema_fast[-1]
        ema_fast_prev = self.ema_fast[-2]
        ema_slow_now = self.ema_slow[-1]
        ema_slow_prev = self.ema_slow[-2]
        return ema_fast_now > ema_slow_now and ema_fast_prev <= ema_slow_prev

    def should_short(self) -> bool:
        # Chỉ vào short khi không có position đang mở
        if self.is_open:
            return False
        # Cần ít nhất 2 giá trị để detect crossover
        if len(self.ema_fast) < 2 or len(self.ema_slow) < 2:
            return False
        # Death cross: EMA fast cross từ trên xuống dưới EMA slow
        # Hiện tại: fast < slow, trước đó: fast >= slow
        ema_fast_now = self.ema_fast[-1]
        ema_fast_prev = self.ema_fast[-2]
        ema_slow_now = self.ema_slow[-1]
        ema_slow_prev = self.ema_slow[-2]
        return ema_fast_now < ema_slow_now and ema_fast_prev >= ema_slow_prev

    def should_cancel_entry(self) -> bool:
        return False

    # --- Position sizing: risk % of balance, cap by max size ---
    def _qty(self, entry: float, stop: float):
        risk_percent = 2.0
        max_capital_pct = 0.25
        risk_qty = utils.risk_to_qty(
            self.balance, risk_percent, entry, stop, fee_rate=self.fee_rate
        )
        max_qty = utils.size_to_qty(
            max_capital_pct * self.balance, entry, precision=6, fee_rate=self.fee_rate
        )
        return min(risk_qty, max_qty)

    def go_long(self):
        entry = self.price
        # Stop loss = giá thấp nhất (low) của nến hiện tại
        stop = self.low
        # Đảm bảo stop < entry (nếu low >= entry thì dùng entry - 1% entry làm stop tối thiểu)
        if stop >= entry:
            stop = entry * 0.99
        # R:R = 1:1 → take profit = entry + (entry - stop)
        take_profit = entry + (entry - stop)
        qty = self._qty(entry, stop)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, take_profit

    def go_short(self):
        entry = self.price
        # Stop loss = giá cao nhất (high) của nến hiện tại
        stop = self.high
        # Đảm bảo stop > entry (nếu high <= entry thì dùng entry + 1% entry làm stop tối thiểu)
        if stop <= entry:
            stop = entry * 1.01
        # R:R = 1:1 → take profit = entry - (stop - entry)
        take_profit = entry - (stop - entry)
        qty = self._qty(entry, stop)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, take_profit

    # --- Exit: chỉ exit qua stop loss hoặc take profit, không exit qua update_position ---
    # Để đảm bảo R:R = 1:1 được thực thi, không liquidate sớm khi có opposite crossover.
    # Nếu muốn exit sớm khi opposite crossover, có thể bỏ comment code dưới.
    def update_position(self):
        # Không exit sớm - để stop loss và take profit tự động đóng lệnh
        # Nếu muốn exit khi opposite crossover, uncomment:
        # if len(self.ema_fast) < 2 or len(self.ema_slow) < 2:
        #     return
        # if self.is_long:
        #     ema_fast_now = self.ema_fast[-1]
        #     ema_fast_prev = self.ema_fast[-2]
        #     ema_slow_now = self.ema_slow[-1]
        #     ema_slow_prev = self.ema_slow[-2]
        #     if ema_fast_now < ema_slow_now and ema_fast_prev >= ema_slow_prev:
        #         self.liquidate()
        # if self.is_short:
        #     ema_fast_now = self.ema_fast[-1]
        #     ema_fast_prev = self.ema_fast[-2]
        #     ema_slow_now = self.ema_slow[-1]
        #     ema_slow_prev = self.ema_slow[-2]
        #     if ema_fast_now > ema_slow_now and ema_fast_prev <= ema_slow_prev:
        #         self.liquidate()
        pass

    # --- Interactive chart: vẽ EMA 50/200 lên candle chart (Jesse built-in)
    # Bật "Interactive charts" trong form backtest để xem.
    # https://docs.jesse.trade/docs/charts/Interactive-charts
    def after(self) -> None:
        # Lấy giá trị hiện tại (không phải array) để vẽ
        self.add_line_to_candle_chart("EMA 50", self.ema_fast[-1])
        self.add_line_to_candle_chart("EMA 200", self.ema_slow[-1])
