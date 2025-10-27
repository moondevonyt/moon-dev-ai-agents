import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.columns = [col.title() for col in data.columns]
data['Datetime'] = pd.to_datetime(data['Datetime'])
data.set_index('Datetime', inplace=True)
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VolatilityDirectional(Strategy):
    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        vol = self.data.Volume
        # Original indicators
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        self.sma50 = self.I(talib.SMA, close, timeperiod=50)
        # New: ATR for dynamic SL and trailing, RSI for entry filters, Volume SMA for confirmation
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        self.avg_vol = self.I(talib.SMA, vol, timeperiod=20)

    def next(self):
        if len(self.data) < 55:  # Warm-up period (covers all indicators)
            return

        if not self.position:
            self.entry_price = None
            self.current_sl = None
            self.initial_risk = None
            self.tp_price = None

        close = self.data.Close[-1]
        prev_close = self.data.Close[-2]
        bb_u = self.bb_upper[-1]
        bb_m = self.bb_middle[-1]
        bb_l = self.bb_lower[-1]
        bb_w = (bb_u - bb_l) / bb_m
        squeeze = bb_w < 0.02
        adx_strong = self.adx[-1] > 25  # Kept at 25 for trend strength
        plus_cross = self.plus_di[-1] > self.minus_di[-1] and self.plus_di[-2] <= self.minus_di[-2]
        minus_cross = self.minus_di[-1] > self.plus_di[-1] and self.minus_di[-2] <= self.plus_di[-2]
        # Improved trend filter: Use BB middle (SMA20) vs SMA50 for better regime detection
        trend_up = self.bb_middle[-1] > self.sma50[-1]
        trend_down = self.bb_middle[-1] < self.sma50[-1]
        vol_confirm = self.data.Volume[-1] > self.avg_vol[-1]  # New: Volume filter for entry quality
        vol_adjust = 0.5 if bb_w > 0.04 else 1.0  # Kept original volatility adjustment

        # Improved Long entry: Tightened with RSI <30 for pullback, >50 for squeeze; added volume; ATR-based SL
        pullback_long = close < bb_l and self.rsi[-1] < 30
        squeeze_long = squeeze and close > bb_m and self.rsi[-1] > 50
        if not self.position and (pullback_long or squeeze_long) and adx_strong and plus_cross and trend_up and vol_confirm:
            entry_price = close
            atr_val = self.atr[-1]
            sl_price = entry_price - 1.5 * atr_val  # New: ATR-based SL for better risk management
            risk_dist = 1.5 * atr_val
            if risk_dist > 0:
                risk_amount = self.equity * 0.01  # 1% risk per trade
                pos_size = (risk_amount / risk_dist) * vol_adjust
                max_size = self.equity * 0.95 / entry_price  # New: Cap position to 95% of equity to prevent overleverage
                pos_size = min(pos_size, max_size)
                tp_price = entry_price + 3 * risk_dist  # Improved: 3:1 R:R for higher returns
                self.buy(size=pos_size)  # No built-in SL/TP; manage manually for proper trailing
                self.entry_price = entry_price
                self.current_sl = sl_price
                self.initial_risk = risk_dist
                self.tp_price = tp_price
                print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, size {pos_size:.4f}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀")

        # Improved Short entry: Symmetric changes with RSI >70 for pullback, <50 for squeeze; volume; ATR SL
        pullback_short = close > bb_u and self.rsi[-1] > 70
        squeeze_short = squeeze and close < bb_m and self.rsi[-1] < 50
        if not self.position and (pullback_short or squeeze_short) and adx_strong and minus_cross and trend_down and vol_confirm:
            entry_price = close
            atr_val = self.atr[-1]
            sl_price = entry_price + 1.5 * atr_val  # ATR-based SL
            risk_dist = 1.5 * atr_val
            if risk_dist > 0:
                risk_amount = self.equity * 0.01
                pos_size = (risk_amount / risk_dist) * vol_adjust
                max_size = self.equity * 0.95 / entry_price
                pos_size = min(pos_size, max_size)
                tp_price = entry_price - 3 * risk_dist  # 3:1 R:R
                self.sell(size=pos_size)  # Manual management
                self.entry_price = entry_price
                self.current_sl = sl_price
                self.initial_risk = risk_dist
                self.tp_price = tp_price
                print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, size {pos_size:.4f}, SL {sl_price:.2f}, TP {tp_price:.2f} ✨")

        # Position management: All exits and trailing handled manually
        if self.position:
            entry_price_pos = self.entry_price
            initial_risk = self.initial_risk
            current_profit = (close - entry_price_pos) if self.position.is_long else (entry_price_pos - close)
            atr_val = self.atr[-1]

            # DI reverse exit (kept for momentum shift protection)
            if self.position.is_long and minus_cross:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                self.tp_price = None
                print(f"🌙 Moon Dev: Long exit on DI reverse at {close:.2f} 🚀")
                return
            if self.position.is_short and plus_cross:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                self.tp_price = None
                print(f"🌙 Moon Dev: Short exit on DI reverse at {close:.2f} 🚀")
                return

            # ADX weakening exit (kept, removed BB overband exit to allow trends to run)
            if self.adx[-1] < 20:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                self.tp_price = None
                print(f"🌙 Moon Dev: Exit on ADX weakening at {close:.2f} ✨")
                return

            # TP check (manual)
            if (self.position.is_long and close >= self.tp_price) or (self.position.is_short and close <= self.tp_price):
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                self.tp_price = None
                print(f"🌙 Moon Dev: TP hit at {close:.2f} 🚀")
                return

            # SL check (manual, uses current_sl for trailing)
            if (self.position.is_long and close <= self.current_sl) or (self.position.is_short and close >= self.current_sl):
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                self.tp_price = None
                print(f"🌙 Moon Dev: SL hit at {close:.2f} 🚀")
                return

            # Improved Trailing stop: ATR-based chandelier trail starting after 1.5R profit for better profit capture
            if current_profit > 1.5 * initial_risk:
                if self.position.is_long:
                    new_sl = close - 2 * atr_val
                    if new_sl > self.current_sl:
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Long trailing SL updated to {new_sl:.2f} 🚀")
                else:
                    new_sl = close + 2 * atr_val
                    if new_sl < self.current_sl:
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Short trailing SL updated to {new_sl:.2f} ✨")

bt = Backtest(data, VolatilityDirectional, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)