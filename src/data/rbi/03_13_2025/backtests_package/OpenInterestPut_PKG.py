# 🌙 Moon Dev's OpenInterestPut Backtest Implementation
import pandas as pd
from backtesting import Backtest, Strategy
import talib

# Data Preparation 🌐
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and prepare columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

class OpenInterestPut(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌡️
    stop_loss_pct = 0.02  # 2% stop loss 🛑
    take_profit_pct = 0.03  # 3% take profit 🎯
    
    def init(self):
        # Price Trend Indicators 📉
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        
        # Open Interest Analysis 🔍
        oi_series = self.data.df['open_interest']
        self.oi_max = self.I(talib.MAX, oi_series, timeperiod=20)
        self.oi_sma5 = self.I(talib.SMA, oi_series, timeperiod=5)
        self.oi = self.I(lambda x: x, oi_series)  # Raw OI values
        
    def next(self):
        current_close = self.data.Close[-1]
        current_oi = self.oi[-1]
        oi_max = self.oi_max[-1]
        oi_sma5 = self.oi_sma5[-1]

        # Moon Dev Debug Prints 🌙
        print(f"\n🌕 Price: {current_close:.2f} | SMA20: {self.sma20[-1]:.2f}")
        print(f"📊 OI: {current_oi} | OI Max: {oi_max} | OI SMA5: {oi_sma5:.2f}")

        if not self.position:
            # Entry Logic 🚀
            bearish_trend = current_close < self.sma20[-1]
            high_oi = current_oi >= 0.95 * oi_max
            
            if bearish_trend and high_oi:
                risk_amount = self.equity * self.risk_percent
                entry_price = current_close
                sl_price = entry_price * (1 + self.stop_loss_pct)
                tp_price = entry_price * (1 - self.take_profit_pct)
                risk_per_share = sl_price - entry_price
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    if position_size > 0:
                        print(f"🚀 SELL SIGNAL! Size: {position_size}")
                        self.sell(size=position_size, 
                                 sl=sl_price,
                                 tp=tp_price)
        else:
            # Exit Logic 🌧️
            if current_oi > oi_sma5:
                print("🔔 OI Increasing - Closing Position!")
                self.position.close()

# Run Backtest 📊
bt = Backtest(data, OpenInterestPut, cash=1_000_000, commission=.002)
stats = bt.run()

# Moon Dev Results Print 🌙
print("\n" + "="*55)
print("🌙✨ MOON DEV BACKTEST RESULTS ✨🌙")
print("="*55)
print(stats)
print(stats._strategy)