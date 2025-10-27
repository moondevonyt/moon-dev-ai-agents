import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename to match backtesting.py requirements
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DirectionalVigor(Strategy):
    adx_period = 14
    adx_threshold = 25
    adx_weak = 20
    risk_per_trade = 0.01  # 1% risk
    atr_multiplier = 2.0
    tp_rr = 2.0  # Take profit reward-to-risk ratio for better exits

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        # 🌙 Moon Dev: Added EMA200 for trend filter to avoid counter-trend trades
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        # 🌙 Moon Dev: Added RSI for momentum confirmation to filter better setups
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev: Added Volume MA for volume confirmation to avoid low-quality signals
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        print("🌙 Moon Dev: Indicators initialized for optimized DirectionalVigor strategy (ADX, DI, ATR, EMA200, RSI, VolMA) ✨")

    def next(self):
        # 🌙 Moon Dev: Increased lookback check for new indicators (EMA200 requires more bars)
        if len(self.data) < 201:
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]
        current_ema = self.ema200[-1]
        current_rsi = self.rsi[-1]
        current_volume = self.data.Volume[-1]
        current_vol_ma = self.vol_ma[-1]

        # 🌙 Moon Dev: Define cross signals
        long_cross = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
        short_cross = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
        # 🌙 Moon Dev: ADX condition for strong trend
        adx_ok = (current_adx > self.adx_threshold) and (current_adx > prev_adx)
        # 🌙 Moon Dev: Volume filter for better entry quality
        vol_ok = current_volume > current_vol_ma
        # 🌙 Moon Dev: Tightened entry with trend (EMA), momentum (RSI), and volume filters
        entry_long = long_cross and adx_ok and (current_close > current_ema) and (current_rsi > 50) and vol_ok
        entry_short = short_cross and adx_ok and (current_close < current_ema) and (current_rsi < 50) and vol_ok

        # 🌙 Moon Dev: Exit on opposite cross (reversal) regardless of entry strength
        if self.position.is_long and short_cross:
            self.position.close()
            print(f"🌙 Moon Dev: Exiting LONG on reversal at {current_close:.2f} | ADX: {current_adx:.2f} 📉💫")
        if self.position.is_short and long_cross:
            self.position.close()
            print(f"🌙 Moon Dev: Exiting SHORT on reversal at {current_close:.2f} | ADX: {current_adx:.2f} 📉💫")

        # 🌙 Moon Dev: Exit on weakening ADX for risk management
        if self.position and current_adx < self.adx_weak:
            if self.position.is_long:
                print(f"🌙 Moon Dev: Exiting LONG on weakening trend at {current_close:.2f} | ADX: {current_adx:.2f} 📉💫")
            else:
                print(f"🌙 Moon Dev: Exiting SHORT on weakening trend at {current_close:.2f} | ADX: {current_adx:.2f} 📉💫")
            self.position.close()

        # 🌙 Moon Dev: Long entry with optimized sizing (fraction of equity), SL, and TP
        if entry_long and not self.position:
            sl_dist = self.atr_multiplier * current_atr
            sl_price = current_close - sl_dist
            tp_dist = self.tp_rr * sl_dist  # Dynamic TP based on RR for improved returns
            tp_price = current_close + tp_dist
            dist_percent = sl_dist / current_close
            fraction = self.risk_per_trade / dist_percent
            self.buy(size=fraction, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {fraction:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # 🌙 Moon Dev: Short entry symmetrically for more opportunities and higher returns
        if entry_short and not self.position:
            sl_dist = self.atr_multiplier * current_atr
            sl_price = current_close + sl_dist
            tp_dist = self.tp_rr * sl_dist  # Dynamic TP based on RR
            tp_price = current_close - tp_dist
            dist_percent = sl_dist / current_close
            fraction = self.risk_per_trade / dist_percent
            self.sell(size=fraction, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {fraction:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)