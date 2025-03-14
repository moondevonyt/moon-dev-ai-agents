```python
# 🌙 MOON DEV BACKTESTING SCRIPT FOR VOLATILITYCLIFFARB STRATEGY 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# DATA PREPARATION 🌙
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)

# Clean and prepare data according to Moon Dev specs ✨
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VolatilityCliffArb(Strategy):
    # 🌙 STRATEGY PARAMETERS
    atr_period = 14
    atr_ma_window = 20
    bb_period = 20
    bb_dev = 2
    risk_pct = 0.01  # 1% risk per trade

    def init(self):
        # 🌙 INDICATOR CALCULATIONS USING TALIB
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.atr_ma = self.I(talib.SMA, self.atr, self.atr_ma_window)
        
        # Bollinger Bands components
        self.bb_upper = self.I(self._calc_bb_upper, name='BB_UPPER')
        self.bb_middle = self.I(self._calc_bb_middle, name='BB_MID')
        self.bb_lower = self.I(self._calc_bb_lower, name='BB_LOWER')

    def _calc_bb_upper(self, close):
        upper, _, _ = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_dev)
        return upper

    def _calc_bb_middle(self, close):
        _, middle, _ = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_dev)
        return middle

    def _calc_bb_lower(self, close):
        _, _, lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_dev)
        return lower

    def next(self):
        # 🌙 MOON DEV DEBUG PRINTING
        if len(self.data) % 100 == 0:
            print(f"🌙 MOON DEV STATUS: Bar {len(self.data)} | Equity: {self.equity:,.0f} ✨")

        if self.position:
            return  # Hold existing position

        # 🌙 VOLATILITY CLIFF DETECTION
        atr_spike = self.atr[-1] > self.atr_ma[-1] * 1.5
        price_above_bb = self.Close[-1] > self.bb_upper[-1]
        price_below_bb = self.Close[-1] < self.bb_lower[-1]

        if atr_spike and (price_above_bb or price_below_bb):
            # 🌙 RISK CALCULATIONS
            risk_amount = self.equity * self.risk_pct
            entry_price = self.Close[-1]
            
            if price_above_bb:  # SHORT SIGNAL
                stop_loss = self.bb_upper[-1] + self.atr[-1]
                risk_per_share = stop_loss - entry_price
                position_size = int(round(risk_amount / risk_per_share))
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_loss, tp=self.bb_middle[-1])
                    print(f"🌙 MOON DEV SHORT ENTRY 🚀\nEntry: {entry_price:.2f} | Size: {position_size} | SL: {stop_loss:.2f} | TP: {self.bb_middle[-1]:.2f}")

            elif price_below_bb:  # LONG SIGNAL
                stop_loss = self.bb_lower[-1] - self.atr[-1]
                risk_per_share = entry_price - stop_loss
                position_size = int(round(risk_amount / risk_per_share))
                if position