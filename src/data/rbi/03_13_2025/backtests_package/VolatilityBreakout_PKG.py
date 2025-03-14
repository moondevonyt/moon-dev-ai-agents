# 🌙 Moon Dev's Volatility Breakout Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class VolatilityBreakout(Strategy):
    def init(self):
        # 🌙 Initialize indicators using TA-Lib and self.I()
        # Bollinger Bands components
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20, name='SMA20')
        self.stddev = self.I(talib.STDDEV, self.data.Close, timeperiod=20, nbdev=1, name='STDDEV')
        self.bb_upper = self.I(lambda: self.sma20 + 2 * self.stddev, name='BB_UPPER')
        self.bb_lower = self.I(lambda: self.sma20 - 2 * self.stddev, name='BB_LOWER')
        
        # Band width and average band width
        self.band_width = self.I(lambda: self.bb_upper - self.bb_lower, name='BAND_WIDTH')
        self.avg_band_width = self.I(talib.SMA, self.band_width, timeperiod=20, name='AVG_BAND_WIDTH')
        
        print("🌙✨ Moon Dev Indicators Initialized! SMA20, BBANDS, Volatility Ready! ✨")

    def next(self):
        # 🌙 Check if we're not in a position
        if not self.position:
            # Calculate conditions
            current_volatility = self.band_width[-1]
            avg_volatility = self.avg_band_width[-1]
            close_below_lower = self.data.Close[-1] < self.bb_lower[-1]
            
            # Entry conditions
            if current_volatility < avg_volatility and close_below_lower:
                # 🌙 Risk management calculations
                account_risk = 0.01  # Risk 1% of equity
                entry_price = self.data.Close[-1]
                entry_bb_upper = self.bb_upper[-1]
                
                # Calculate risk per share and position size
                risk_per_share = entry_bb_upper - entry_price
                if risk_per_share <= 0:
                    print("🌙⚠️ Moon Dev Warning: Negative/Zero Risk Per Share - Trade Skipped!")
                    return
                
                risk_amount = self.equity * account_risk
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size <= 0:
                    print("🌙⚠️ Moon Dev Warning: Invalid Position Size - Trade Skipped!")
                    return
                
                # 🌙 Enter short position with stop loss at upper band
                self.sell(size=position_size, sl=entry_bb_upper)
                print(f"🌙🚀 MOON DEV SHORT ENTRY! Size: {position_size} @ {entry_price:.2f} | SL: {entry_bb_upper:.2f} 🚀")
        
        # 🌙 Check for exit conditions on existing short position
        else:
            if self.data.High[-1] >= self.bb_upper[-1]:
                self.position.close()
                print(f"🌙🎯 MOON DEV EXIT! Price Touched Upper Band @ {self.data.Close[-1]:.2f} 🎯")

# 🌙✨ Data Preparation Magic ✨
data = pd.read_csv(
    '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
    parse_dates=['datetime'],
    index_col='datetime'
)

# 🌙 Cleanse and prepare data
data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

# 🌙 Run the backtest
bt = Backtest(data, VolatilityBreakout, cash=10000, commission=0.002)
results = bt.run()

# 🌙 Print results
print("🌙✨ MOON DEV BACKTEST RESULTS ✨")
print(results)