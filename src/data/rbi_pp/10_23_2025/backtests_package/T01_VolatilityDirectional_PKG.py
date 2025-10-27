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
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        self.sma50 = self.I(talib.SMA, close, timeperiod=50)

    def next(self):
        if len(self.data) < 55:  # Warm-up period
            return

        close = self.data.Close[-1]
        prev_close = self.data.Close[-2]
        bb_u = self.bb_upper[-1]
        bb_m = self.bb_middle[-1]
        bb_l = self.bb_lower[-1]
        bb_w = (bb_u - bb_l) / bb_m
        squeeze = bb_w < 0.02
        adx_strong = self.adx[-1] > 25
        plus_cross = self.plus_di[-1] > self.minus_di[-1] and self.plus_di[-2] <= self.minus_di[-2]
        minus_cross = self.minus_di[-1] > self.plus_di[-1] and self.minus_di[-2] <= self.plus_di[-2]
        trend_up = close > self.sma50[-1]
        trend_down = close < self.sma50[-1]
        vol_adjust = 0.5 if bb_w > 0.04 else 1.0

        # Long entry
        pullback_long = close < bb_l
        squeeze_long = squeeze and close > bb_m
        if not self.position and (pullback_long or squeeze_long) and adx_strong and plus_cross and trend_up:
            entry_price = close
            sl_price = bb_l * 0.99
            risk_dist = entry_price - sl_price
            if risk_dist > 0:
                risk_amount = self.equity * 0.01
                pos_size = risk_amount / risk_dist * vol_adjust
                pos_size = int(round(pos_size))
                tp_price = entry_price + 2 * risk_dist
                self.buy(size=pos_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, size {pos_size}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀")

        # Short entry
        pullback_short = close > bb_u
        squeeze_short = squeeze and close < bb_m
        if not self.position and (pullback_short or squeeze_short) and adx_strong and minus_cross and trend_down:
            entry_price = close
            sl_price = bb_u * 1.01
            risk_dist = sl_price - entry_price
            if risk_dist > 0:
                risk_amount = self.equity * 0.01
                pos_size = risk_amount / risk_dist * vol_adjust
                pos_size = int(round(pos_size))
                tp_price = entry_price - 2 * risk_dist
                self.sell(size=pos_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, size {pos_size}, SL {sl_price:.2f}, TP {tp_price:.2f} ✨")

        # Additional exits and trailing
        if self.position:
            entry_price_pos = self.position.price
            initial_risk = abs(entry_price_pos - self.position.sl)
            current_profit = abs(close - entry_price_pos) if self.position.is_long else abs(entry_price_pos - close)

            # DI reverse exit
            if self.position.is_long and minus_cross:
                self.position.close()
                print(f"🌙 Moon Dev: Long exit on DI reverse at {close:.2f} 🚀")
                return
            if self.position.is_short and plus_cross:
                self.position.close()
                print(f"🌙 Moon Dev: Short exit on DI reverse at {close:.2f} 🚀")
                return

            # BB or ADX exit
            if self.position.is_long and (close > bb_u or self.adx[-1] < 20):
                self.position.close()
                print(f"🌙 Moon Dev: Long exit on BB/ADX at {close:.2f} ✨")
                return
            if self.position.is_short and (close < bb_l or self.adx[-1] < 20):
                self.position.close()
                print(f"🌙 Moon Dev: Short exit on BB/ADX at {close:.2f} ✨")
                return

            # Trailing stop
            if current_profit > initial_risk:
                trail_sl = bb_m
                if (self.position.is_long and trail_sl > self.position.sl) or \
                   (self.position.is_short and trail_sl < self.position.sl):
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} 🚀")

bt = Backtest(data, VolatilityDirectional, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)