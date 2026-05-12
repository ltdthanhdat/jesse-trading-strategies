"""
SMC Strategy với FVG + Pin Bar

- Long khi có Bullish FVG + Bullish Pin Bar nằm trong FVG
- Short khi có Bearish FVG + Bearish Pin Bar nằm trong FVG
- Stop loss: dưới FVG bottom (long) hoặc trên FVG top (short)
- Take profit: R:R = 1:1
- Exit khi FVG bị mitigated hoàn toàn
- Plot FVG, BOS, CHoCH trên interactive chart
"""

from jesse.strategies import Strategy
from jesse import utils
from typing import List, Tuple, Optional
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
    FVG_LOOKBACK = 20
    STRUCTURE_LOOKBACK = 10
    PIN_BAR_BODY_RATIO = 0.3
    PIN_BAR_WICK_TO_BODY = 2.0
    PIN_BAR_CLOSE_EXTREME_RATIO = 0.25
    
    def _get_candle(self, offset: int = 0) -> Optional[Tuple[float, float, float, float]]:
        """Get candle data: (open, close, high, low)"""
        if len(self.candles) <= abs(offset):
            return None
        candle = self.candles[offset]
        return candle[1], candle[2], candle[3], candle[4]
    
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
    
    def _get_all_fvgs(self) -> List[FVG]:
        """Scan candles để tìm tất cả FVG"""
        fvgs = []
        if len(self.candles) < 4:
            return fvgs
        
        # Scan từ đầu đến hiện tại để tìm FVG
        for i in range(3, len(self.candles)):
            if i < 3:
                continue
            
            candle_3 = self.candles[i-3]
            candle_1 = self.candles[i-1]
            
            high_3 = candle_3[3]
            low_3 = candle_3[4]
            high_1 = candle_1[3]
            low_1 = candle_1[4]
            
            # Bullish FVG: high[3] < low[1]
            if high_3 < low_1:
                fvgs.append(FVG(
                    top=low_1,
                    bottom=high_3,
                    is_bullish=True,
                    bar_index=i
                ))
            
            # Bearish FVG: low[3] > high[1]
            if low_3 > high_1:
                fvgs.append(FVG(
                    top=low_3,
                    bottom=high_1,
                    is_bullish=False,
                    bar_index=i
                ))
        
        return fvgs
    
    def _is_fvg_mitigated(self, fvg: FVG) -> bool:
        """Check if FVG đã bị mitigated"""
        # Check từ bar_index của FVG đến hiện tại
        for i in range(fvg.bar_index, len(self.candles)):
            candle = self.candles[i]
            low_price = candle[4]
            high_price = candle[3]
            
            if fvg.is_bullish:
                # Bullish FVG bị mitigated khi low <= FVG bottom
                if low_price <= fvg.bottom:
                    return True
            else:
                # Bearish FVG bị mitigated khi high >= FVG top
                if high_price >= fvg.top:
                    return True
        
        return False
    
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
    
    def _get_structure_highest_bar(self, lookback: int) -> int:
        """Find structure highest bar index"""
        if len(self.candles) <= lookback:
            lookback = len(self.candles) - 1
        
        max_bar_idx = 0
        max_high = self.candles[-lookback-1][2]  # high
        
        for i in range(-lookback-1, 0):
            if self.candles[i][2] > max_high:  # high
                max_high = self.candles[i][2]
                max_bar_idx = i
        
        return max_bar_idx
    
    def _get_structure_lowest_bar(self, lookback: int) -> int:
        """Find structure lowest bar index"""
        if len(self.candles) <= lookback:
            lookback = len(self.candles) - 1
        
        min_bar_idx = 0
        min_low = self.candles[-lookback-1][3]  # low
        
        for i in range(-lookback-1, 0):
            if self.candles[i][3] < min_low:  # low
                min_low = self.candles[i][3]
                min_bar_idx = i
        
        return min_bar_idx
    
    def _get_structure_breaks(self) -> List[Tuple[float, bool, bool]]:
        """Get BOS/CHoCH events: returns list of (price, is_bos, is_choch)"""
        breaks = []
        if len(self.candles) < self.STRUCTURE_LOOKBACK + 4:
            return breaks
        
        # Simplified: track structure và detect breaks
        # This is a simplified version - full implementation would track structure state
        # For now, return empty list (can be enhanced later)
        return breaks
    
    def _get_active_bullish_fvg(self) -> Optional[FVG]:
        """Get most recent active (non-mitigated) Bullish FVG"""
        fvgs = self._get_all_fvgs()
        for fvg in reversed(fvgs):
            if fvg.is_bullish and not self._is_fvg_mitigated(fvg):
                return fvg
        return None
    
    def _get_active_bearish_fvg(self) -> Optional[FVG]:
        """Get most recent active (non-mitigated) Bearish FVG"""
        fvgs = self._get_all_fvgs()
        for fvg in reversed(fvgs):
            if not fvg.is_bullish and not self._is_fvg_mitigated(fvg):
                return fvg
        return None
    
    def _get_fvg_containing_pin_bar(self, is_bullish: bool) -> Optional[FVG]:
        """Get FVG mà Pin Bar nằm trong đó"""
        fvgs = self._get_all_fvgs()
        for fvg in reversed(fvgs):
            if fvg.is_bullish == is_bullish and not self._is_fvg_mitigated(fvg):
                if self._is_pin_bar_in_fvg(is_bullish, fvg):
                    return fvg
        return None
    
    def _is_pin_bar_in_fvg(self, pin_bar_is_bullish: bool, fvg: FVG) -> bool:
        """Check if Pin Bar nằm trong FVG"""
        if pin_bar_is_bullish != fvg.is_bullish:
            return False
        
        return self.low >= fvg.bottom and self.high <= fvg.top
    
    def should_long(self) -> bool:
        """Long entry: Bullish FVG + Bullish Pin Bar nằm trong FVG"""
        if self.is_open:
            return False
        
        # Check for Bullish Pin Bar
        if not self._is_pin_bar(is_bullish=True):
            return False
        
        return self._get_fvg_containing_pin_bar(is_bullish=True) is not None
    
    def should_short(self) -> bool:
        """Short entry: Bearish FVG + Bearish Pin Bar nằm trong FVG"""
        if self.is_open:
            return False
        
        # Check for Bearish Pin Bar
        if not self._is_pin_bar(is_bullish=False):
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
        # Get FVG mà Pin Bar nằm trong đó
        fvg = self._get_fvg_containing_pin_bar(is_bullish=True)
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
        # Get FVG mà Pin Bar nằm trong đó
        fvg = self._get_fvg_containing_pin_bar(is_bullish=False)
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
        """Exit khi FVG bị mitigated hoàn toàn"""
        if not self.is_open:
            self.vars.pop("active_fvg", None)
            return

        active_fvg = self.vars.get("active_fvg")
        if active_fvg is None:
            return

        if self._is_fvg_mitigated(active_fvg):
            self.liquidate()
    
    def after(self) -> None:
        """Plot FVG, BOS, CHoCH trên interactive chart"""
        # Plot FVG lines
        fvgs = self._get_all_fvgs()
        for fvg in fvgs[-5:]:  # Plot 5 FVG gần nhất
            if fvg.is_bullish:
                self.add_line_to_candle_chart(f"FVG_Bullish_Top_{fvg.bar_index}", fvg.top)
                self.add_line_to_candle_chart(f"FVG_Bullish_Bottom_{fvg.bar_index}", fvg.bottom)
            else:
                self.add_line_to_candle_chart(f"FVG_Bearish_Top_{fvg.bar_index}", fvg.top)
                self.add_line_to_candle_chart(f"FVG_Bearish_Bottom_{fvg.bar_index}", fvg.bottom)
        
        # Plot BOS/CHoCH lines (simplified - can be enhanced)
        breaks = self._get_structure_breaks()
        for i, (price, is_bos, is_choch) in enumerate(breaks[-10:]):  # Plot 10 breaks gần nhất
            if is_bos:
                self.add_line_to_candle_chart(f"BOS_{i}", price)
            elif is_choch:
                self.add_line_to_candle_chart(f"CHoCH_{i}", price)
