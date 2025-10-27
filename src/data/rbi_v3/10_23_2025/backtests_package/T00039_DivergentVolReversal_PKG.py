import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

class DivergentVolReversal(Strategy):
    lookback = 10
    risk_pct = 0.01
    atr_mult = 1.0
    rr_ratio = 1.5
    vol_mult = 1.2
    max_bars = 10
    adx_threshold = 25
    rsi_ob = 70
    rsi_os = 30
    vix_proxy_threshold = 300  # Arbitrary threshold for BTC ATR as VIX proxy to avoid entry

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        macd_line, macd_signal, macd_hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.macd_hist = macd_hist
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=20)
        self.entry_bar = None
        print("🌙 Moon Dev: Strategy initialized with indicators! ✨")

    def next(self):
        if len(self.data) < 50:
            return

        # Volatility exit for open positions
        if self.position:
            if self.atr[-1] > self.vol_mult * self.atr_sma[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Volatility spike exit at {self.data.Close[-1]}! ⚠️")
                return
            bars_held = len(self.data) - self.entry_bar if self.entry_bar is not None else 0
            if bars_held > self.max_bars:
                self.position.close()
                print(f"🌙 Moon Dev: Time-based exit at {self.data.Close[-1]} after {bars_held} bars! ⏰")
                return
            return

        # No position: check for entries
        if self.adx[-1] > self.adx_threshold:
            return  # Trending market, skip entry
        if self.atr[-1] > self.vix_proxy_threshold:
            return  # High vol, avoid entry like VIX >25

        # Long entry
        if self.data.Close[-1] < self.sma[-1] and len(self.data) > self.lookback + 1:
            recent_lows = self.data.Low.iloc[-self.lookback-1:-1].values
            if len(recent_lows) == self.lookback:
                min_rel_idx = np.argmin(recent_lows)
                prev_low_rel_pos = -(self.lookback + 1) + min_rel_idx
                prev_rsi = self.rsi.iloc[prev_low_rel_pos]
                prev_hist = self.macd_hist.iloc[prev_low_rel_pos]
                current_low = self.data.Low[-1]
                prev_min_low = recent_lows.min()
                if (current_low < prev_min_low and
                    self.rsi[-1] > prev_rsi and
                    self.macd_hist[-1] > prev_hist and
                    self.rsi[-1] < self.rsi_os):
                    entry_price = self.data.Close[-1]
                    atr_val = self.atr[-1]
                    sl_price = current_low - self.atr_mult * atr_val
                    risk_per_unit = entry_price - sl_price
                    if risk_per_unit > 0:
                        equity = self._broker.getvalue()
                        risk_amount = self.risk_pct * equity
                        pos_size = risk_amount / risk_per_unit
                        pos_size = int(round(pos_size))
                        if pos_size > 0:
                            tp_price = entry_price + self.rr_ratio * risk_per_unit
                            self.buy(size=pos_size, sl=sl_price, tp=tp_price)
                            self.entry_bar = len(self.data)
                            print(f"🌙 Moon Dev: Bullish divergence LONG entry at {entry_price:.2f}, size {pos_size}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀")

        # Short entry
        if self.data.Close[-1] > self.sma[-1] and len(self.data) > self.lookback + 1:
            recent_highs = self.data.High.iloc[-self.lookback-1:-1].values
            if len(recent_highs) == self.lookback:
                max_rel_idx = np.argmax(recent_highs)
                prev_high_rel_pos = -(self.lookback + 1) + max_rel_idx
                prev_rsi = self.rsi.iloc[prev_high_rel_pos]
                prev_hist = self.macd_hist.iloc[prev_high_rel_pos]
                current_high = self.data.High[-1]
                prev_max_high = recent_highs.max()
                if (current_high > prev_max_high and
                    self.rsi[-1] < prev_rsi and
                    self.macd_hist[-1] < prev_hist and
                    self.rsi[-1] > self.rsi_ob):
                    entry_price = self.data.Close[-1]
                    atr_val = self.atr[-1]
                    sl_price = current_high + self.atr_mult * atr_val
                    risk_per_unit = sl_price - entry_price
                    if risk_per_unit > 0:
                        equity = self._broker.getvalue()
                        risk_amount = self.risk_pct * equity
                        pos_size = risk_amount / risk_per_unit
                        pos_size = int(round(pos_size))
                        if pos_size > 0:
                            tp_price = entry_price - self.rr_ratio * risk_per_unit
                            self.sell(size=pos_size, sl=sl_price, tp=tp_price)
                            self.entry_bar = len(self.data)
                            print(f"🌙 Moon Dev: Bearish divergence SHORT entry at {entry_price:.2f}, size {pos_size}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀")

bt = Backtest(data, DivergentVolReversal, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)