"""
SMC Strategy với FVG + Pin Bar

- Long khi có Bullish FVG + Bullish Pin Bar nằm trong FVG
- Short khi có Bearish FVG + Bearish Pin Bar nằm trong FVG
- Stop loss: dưới FVG bottom (long) hoặc trên FVG top (short)
- Take profit: R:R = 1:1
- Exit khi FVG bị mitigated hoàn toàn
- Plot FVG trên interactive chart
"""

from jesse.strategies import Strategy
from jesse import utils
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FVG:
    """Fair Value Gap structure"""
    top: float
    bottom: float
    is_bullish: bool
    bar_index: int


class SMC_FVG_PinBar(Strategy):
    # Parameters
    PIN_BAR_BODY_RATIO = 0.3
    PIN_BAR_WICK_TO_BODY = 2.0
    PIN_BAR_CLOSE_EXTREME_RATIO = 0.25

    def _state(self) -> Dict:
        if "fvg_state" not in self.vars:
            self.vars["fvg_state"] = {
                "last_candle_ts": None,
                "active_bullish": [],
                "active_bearish": [],
                "recent_fvgs": [],
                "signal_bullish_fvg": None,
                "signal_bearish_fvg": None,
            }
        return self.vars["fvg_state"]
    
    def _get_candle(self, offset: int = 0) -> Optional[Tuple[float, float, float, float]]:
        """Get candle data: (open, close, high, low)"""
        index = -1 if offset == 0 else offset
        if len(self.candles) < abs(index):
            return None
        candle = self.candles[index]
        return candle[1], candle[2], candle[3], candle[4]

    def _current_candle_timestamp(self) -> Optional[int]:
        if len(self.candles) == 0:
            return None
        return int(self.candles[-1][0])
    
    def _detect_current_fvg(self) -> Optional[FVG]:
        """Detect FVG tại nến hiện tại: Bullish FVG khi high[3] < low[1], Bearish FVG khi low[3] > high[1]"""
        if len(self.candles) < 4:
            return None
        
        # Get candles: [3] [2] [1] [0] (current)
        candle_3 = self._get_candle(-4)  # 3 nến trước
        candle_1 = self._get_candle(-2)   # 1 nến trước
        
        if candle_3 is None or candle_1 is None:
            return None
        
        _, _, high_3, low_3 = candle_3
        _, _, high_1, low_1 = candle_1
        
        # Bullish FVG: high[3] < low[1]
        if high_3 < low_1:
            return FVG(
                top=low_1,
                bottom=high_3,
                is_bullish=True,
                bar_index=len(self.candles) - 1
            )
        
        # Bearish FVG: low[3] > high[1]
        if low_3 > high_1:
            return FVG(
                top=low_3,
                bottom=high_1,
                is_bullish=False,
                bar_index=len(self.candles) - 1
            )
        
        return None

    def _is_fvg_mitigated_by_current_candle(self, fvg: FVG) -> bool:
        if fvg.is_bullish:
            return self.low <= fvg.bottom
        return self.high >= fvg.top

    def _refresh_fvg_state(self) -> None:
        state = self._state()
        candle_ts = self._current_candle_timestamp()
        if candle_ts is None or state["last_candle_ts"] == candle_ts:
            return

        current_fvg = self._detect_current_fvg()
        if current_fvg is not None:
            bucket_name = "active_bullish" if current_fvg.is_bullish else "active_bearish"
            state[bucket_name].append(current_fvg)
            state["recent_fvgs"].append(current_fvg)
            if len(state["recent_fvgs"]) > 5:
                state["recent_fvgs"] = state["recent_fvgs"][-5:]

        state["active_bullish"] = [
            fvg
            for fvg in state["active_bullish"]
            if not self._is_fvg_mitigated_by_current_candle(fvg)
        ]
        state["active_bearish"] = [
            fvg
            for fvg in state["active_bearish"]
            if not self._is_fvg_mitigated_by_current_candle(fvg)
        ]

        state["signal_bullish_fvg"] = None
        state["signal_bearish_fvg"] = None
        state["last_candle_ts"] = candle_ts
    
    def _is_pin_bar(self, is_bullish: bool) -> bool:
        """Detect Pin Bar pattern"""
        if len(self.candles) < 1:
            return False
        
        open_price, close_price, high_price, low_price = self._get_candle(0)
        
        body = abs(close_price - open_price)
        upper_wick = high_price - max(close_price, open_price)
        lower_wick = min(close_price, open_price) - low_price
        total_range = high_price - low_price
        
        if total_range == 0:
            return False
        
        if is_bullish:
            close_near_high = close_price >= high_price - total_range * self.PIN_BAR_CLOSE_EXTREME_RATIO
            body_in_upper_range = min(open_price, close_price) >= low_price + total_range * (1 - self.PIN_BAR_BODY_RATIO)
            return (
                close_price > open_price and
                lower_wick >= self.PIN_BAR_WICK_TO_BODY * body and
                upper_wick <= body and
                body <= total_range * self.PIN_BAR_BODY_RATIO and
                close_near_high and
                body_in_upper_range
            )
        else:
            close_near_low = close_price <= low_price + total_range * self.PIN_BAR_CLOSE_EXTREME_RATIO
            body_in_lower_range = max(open_price, close_price) <= high_price - total_range * (1 - self.PIN_BAR_BODY_RATIO)
            return (
                close_price < open_price and
                upper_wick >= self.PIN_BAR_WICK_TO_BODY * body and
                lower_wick <= body and
                body <= total_range * self.PIN_BAR_BODY_RATIO and
                close_near_low and
                body_in_lower_range
            )

    def _is_trend_body(self, is_bullish: bool) -> bool:
        """Detect strong body candle with short opposite wick"""
        if len(self.candles) < 1:
            return False

        open_price, close_price, high_price, low_price = self._get_candle(0)

        body = abs(close_price - open_price)
        upper_wick = high_price - max(close_price, open_price)
        lower_wick = min(close_price, open_price) - low_price
        total_range = high_price - low_price

        if total_range == 0:
            return False

        body_ratio = body / total_range
        if is_bullish:
            return (
                close_price > open_price and
                body_ratio >= 0.55 and
                close_price >= high_price - total_range * 0.15 and
                upper_wick <= total_range * 0.15 and
                lower_wick <= total_range * 0.2
            )

        return (
            close_price < open_price and
            body_ratio >= 0.55 and
            close_price <= low_price + total_range * 0.15 and
            lower_wick <= total_range * 0.15 and
            upper_wick <= total_range * 0.2
        )

    def _is_displacement_break(self, is_bullish: bool) -> bool:
        """Detect displacement close that breaks the previous candle extreme"""
        if len(self.candles) < 2:
            return False

        open_price, close_price, high_price, low_price = self._get_candle(0)
        _, _, prev_high, prev_low = self._get_candle(-2)

        body = abs(close_price - open_price)
        total_range = high_price - low_price
        if total_range == 0:
            return False

        body_ratio = body / total_range
        if is_bullish:
            return (
                close_price > open_price and
                body_ratio >= 0.6 and
                close_price > prev_high and
                close_price >= high_price - total_range * 0.2
            )

        return (
            close_price < open_price and
            body_ratio >= 0.6 and
            close_price < prev_low and
            close_price <= low_price + total_range * 0.2
        )

    def _entry_signal_kind(self, is_bullish: bool) -> Optional[str]:
        if self._is_pin_bar(is_bullish):
            return "pin_bar"
        if self._is_trend_body(is_bullish):
            return "trend_body"
        if self._is_displacement_break(is_bullish):
            return "displacement"
        return None
    
    def _get_active_bullish_fvg(self) -> Optional[FVG]:
        """Get most recent active (non-mitigated) Bullish FVG"""
        self._refresh_fvg_state()
        state = self._state()
        if not state["active_bullish"]:
            return None
        return state["active_bullish"][-1]
    
    def _get_active_bearish_fvg(self) -> Optional[FVG]:
        """Get most recent active (non-mitigated) Bearish FVG"""
        self._refresh_fvg_state()
        state = self._state()
        if not state["active_bearish"]:
            return None
        return state["active_bearish"][-1]
    
    def _get_fvg_containing_pin_bar(self, is_bullish: bool) -> Optional[FVG]:
        """Get FVG mà Pin Bar nằm trong đó"""
        self._refresh_fvg_state()
        state = self._state()
        active_fvgs = state["active_bullish"] if is_bullish else state["active_bearish"]
        for fvg in reversed(active_fvgs):
            if self._is_pin_bar_in_fvg(is_bullish, fvg):
                if is_bullish:
                    state["signal_bullish_fvg"] = fvg
                else:
                    state["signal_bearish_fvg"] = fvg
                return fvg
        return None
    
    def _is_pin_bar_in_fvg(self, pin_bar_is_bullish: bool, fvg: FVG) -> bool:
        """Check if Pin Bar nằm trong FVG"""
        if pin_bar_is_bullish != fvg.is_bullish:
            return False

        overlaps_fvg = self.high >= fvg.bottom and self.low <= fvg.top
        if not overlaps_fvg:
            return False

        signal_kind = self.vars.get("entry_signal_kind")
        if signal_kind not in {"trend_body", "displacement"}:
            return True

        fvg_height = fvg.top - fvg.bottom
        if fvg_height <= 0:
            return False

        _, close_price, _, _ = self._get_candle(0)
        if pin_bar_is_bullish:
            return (
                self.low <= fvg.bottom + fvg_height * 0.35 and
                close_price >= fvg.bottom + fvg_height * 0.65
            )

        return (
            self.high >= fvg.top - fvg_height * 0.35 and
            close_price <= fvg.bottom + fvg_height * 0.35
        )
    
    def should_long(self) -> bool:
        """Long entry: Bullish FVG + Bullish Pin Bar nằm trong FVG"""
        if self.is_open:
            return False
        self._refresh_fvg_state()

        signal_kind = self._entry_signal_kind(is_bullish=True)
        self.vars["entry_signal_kind"] = signal_kind
        if signal_kind is None:
            return False

        return self._get_fvg_containing_pin_bar(is_bullish=True) is not None
    
    def should_short(self) -> bool:
        """Short entry: Bearish FVG + Bearish Pin Bar nằm trong FVG"""
        if self.is_open:
            return False
        self._refresh_fvg_state()

        signal_kind = self._entry_signal_kind(is_bullish=False)
        self.vars["entry_signal_kind"] = signal_kind
        if signal_kind is None:
            return False

        return self._get_fvg_containing_pin_bar(is_bullish=False) is not None
    
    def should_cancel_entry(self) -> bool:
        return False
    
    def _qty(self, entry: float, stop: float):
        """Position sizing: risk 2% balance, max 25% capital"""
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
        """Long position: entry tại close, SL dưới FVG bottom, TP R:R 1:1"""
        self._refresh_fvg_state()
        state = self._state()
        fvg = state.get("signal_bullish_fvg") or self._get_fvg_containing_pin_bar(is_bullish=True)
        if fvg is None:
            return
        
        entry = self.price
        stop = fvg.bottom  # Dưới FVG bottom
        
        # Ensure stop < entry
        if stop >= entry:
            stop = entry * 0.99
        
        # R:R = 1:1
        take_profit = entry + (entry - stop)
        
        qty = self._qty(entry, stop)
        self.vars["active_fvg"] = fvg
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, take_profit
    
    def go_short(self):
        """Short position: entry tại close, SL trên FVG top, TP R:R 1:1"""
        self._refresh_fvg_state()
        state = self._state()
        fvg = state.get("signal_bearish_fvg") or self._get_fvg_containing_pin_bar(is_bullish=False)
        if fvg is None:
            return
        
        entry = self.price
        stop = fvg.top  # Trên FVG top
        
        # Ensure stop > entry
        if stop <= entry:
            stop = entry * 1.01
        
        # R:R = 1:1
        take_profit = entry - (stop - entry)
        
        qty = self._qty(entry, stop)
        self.vars["active_fvg"] = fvg
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, take_profit
    
    def update_position(self):
        """Manage open-position state; exits are handled by SL/TP orders."""
        if not self.is_open:
            self.vars.pop("active_fvg", None)
            self.vars.pop("entry_signal_kind", None)
    
    def after(self) -> None:
        """Plot FVG trên interactive chart"""
        self._refresh_fvg_state()
        for fvg in self._state()["recent_fvgs"]:
            if fvg.is_bullish:
                self.add_line_to_candle_chart(f"FVG_Bullish_Top_{fvg.bar_index}", fvg.top)
                self.add_line_to_candle_chart(f"FVG_Bullish_Bottom_{fvg.bar_index}", fvg.bottom)
            else:
                self.add_line_to_candle_chart(f"FVG_Bearish_Top_{fvg.bar_index}", fvg.top)
                self.add_line_to_candle_chart(f"FVG_Bearish_Bottom_{fvg.bar_index}", fvg.bottom)
