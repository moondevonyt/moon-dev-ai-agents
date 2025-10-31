"""
🌙 Moon Dev - Auto-Generated Strategy: 5.0xEMA20/100_RSI65_Vol2.0x_v35
Generated: 20251031_005655
Performance: 64.17% return, -8.73% max DD

Description: Variation of winner strategy #35
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

class 5_0xEMA20_100_RSI65_Vol2_0x_v35Strategy(Strategy):
    """
    Variation of winner strategy #35

    Parameters:
    - Fast MA: 20
    - Slow MA: 100
    - Use EMA: True
    - Leverage: 5.0x
    - Stop Loss: 1.0%
    - Take Profit: 6.0%
    - RSI Min: 65
    - Volume Filter: True

    Backtest Results:
    - Return: 64.17%
    - Win Rate: 46.88%
    - Sharpe Ratio: 2.15
    - Trades: 32
    """

    # Strategy parameters
    fast_ma = 20
    slow_ma = 100
    use_ema = True
    leverage = 5.0
    stop_loss_pct = 0.01
    take_profit_pct = 0.06
    rsi_min = 65
    use_volume = True
    volume_mult = 2.0

    def init(self):
        close = self.data.Close

        # Calculate moving averages
        if self.use_ema:
            self.ma_fast = self.I(self._ema, close, self.fast_ma)
            self.ma_slow = self.I(self._ema, close, self.slow_ma)
        else:
            self.ma_fast = self.I(self._sma, close, self.fast_ma)
            self.ma_slow = self.I(self._sma, close, self.slow_ma)

        # RSI
        if self.rsi_min is not None:
            self.rsi = self.I(self._rsi, close, 14)

        # Volume average
        if self.use_volume:
            vol = self.data.Volume
            self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

    def _sma(self, prices, period):
        return pd.Series(prices).rolling(period).mean().values

    def _ema(self, prices, period):
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values

    def _rsi(self, prices, period=14):
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        if down == 0:
            return np.full_like(prices, 100)
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            up = (up * (period - 1) + max(delta, 0)) / period
            down = (down * (period - 1) + max(-delta, 0)) / period
            if down == 0:
                rsi[i] = 100
            else:
                rsi[i] = 100. - 100. / (1. + up/down)
        return rsi

    def next(self):
        if np.isnan(self.ma_slow[-1]):
            return

        price = self.data.Close[-1]

        if not self.position:
            # Entry logic
            entry_ok = False

            # MA condition
            if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                entry_ok = True

            # RSI filter
            if self.rsi_min is not None and hasattr(self, 'rsi'):
                if self.rsi[-1] < self.rsi_min:
                    entry_ok = False

            # Volume filter
            if self.use_volume and hasattr(self, 'vol_avg'):
                if self.data.Volume[-1] < (self.vol_avg[-1] * self.volume_mult):
                    entry_ok = False

            if entry_ok:
                sl = price * (1 - self.stop_loss_pct)
                tp = price * (1 + self.take_profit_pct)
                self.buy(size=self.leverage, sl=sl, tp=tp)

        else:
            # Exit on death cross
            if crossover(self.ma_slow, self.ma_fast):
                self.position.close()
