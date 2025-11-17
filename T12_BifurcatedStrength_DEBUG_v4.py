import talib
from backtesting import Strategy
import pandas as pd

class BifurcatedStrength(Strategy):
    adx14_period = 14
    adx20_period = 20
    atr_period = 14
    high_low_period = 20
    adx_threshold = 25
    adx_weak_threshold = 20
    risk_per_trade = 0.01
    atr_multiplier_sl = 1.5
    rr_ratio = 2

    def init(self):
        # 🌙 Initialize indicators with TA-Lib via self.I() 🚀
        self.adx14 = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx14_period)
        self.adx20 = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx20_period)
        self.plus_di14 = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx14_period)
        self.minus_di14 = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx14_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.high20 = self.I(talib.MAX, self.data.High, timeperiod=self.high_low_period)
        self.low20 = self.I(talib.MIN, self.data.Low, timeperiod=self.high_low_period)
        
        # ✨ Moon Dev Debug: Indicators ready! 🌙
        print("🌙 BifurcatedStrength indicators initialized! 🚀")

    def next(self):
        # 📊 Current values for debugging ✨
        current_close = self.data.Close[-1]
        current_adx14 = self.adx14[-1]
        current_adx20 = self.adx20[-1]
        current_plus_di = self.plus_di14[-1]
        current_minus_di = self.minus_di14[-1]
        current_atr = self.atr[-1]
        current_high20 = self.high20[-1]
        current_low20 = self.low20[-1]
        
        # 🚨 Exit conditions first 🌙
        if self.position:
            # Exit if ADX(14) drops below 20 (trend weakening)
            if current_adx14 < self.adx_weak_threshold:
                self.position.close()
                print(f"🌙 Exit: ADX(14) weakened below {self.adx_weak_threshold} at {current_close} 💥")
                return
            
            # Exit on opposite DI crossover
            if self.position.is_long and (self.minus_di14[-2] < self.plus_di14[-2] and self.minus_di14[-1] > self.plus_di14[-1]):
                self.position.close()
                print(f"🌙 Long Exit: -DI crossed above +DI at {current_close} 🔄")
            elif self.position.is_short and (self.plus_di14[-2] < self.minus_di14[-2] and self.plus_di14[-1] > self.minus_di14[-1]):
                self.position.close()
                print(f"🌙 Short Exit: +DI crossed above -DI at {current_close} 🔄")
        
        # No position: Check entries
        if not self.position:
            risk_distance = self.atr_multiplier_sl * current_atr
            if risk_distance <= 0:
                return  # Avoid division by zero or invalid distance 🌙
            risk_amount = self.equity * self.risk_per_trade
            position_size = int(round(risk_amount / risk_distance))
            if position_size <= 0:
                return  # Invalid size, skip trade ✨
            
            # 📈 Long Entry Logic 🚀
            long_di_cross = (self.plus_di14[-2] < self.minus_di14[-2] and self.plus_di14[-1] > self.minus_di14[-1])
            long_adx_strong = current_adx14 > self.adx_threshold
            long_bifurcation = current_adx14 > current_adx20
            long_market_not_ranging = current_adx20 > self.adx_weak_threshold
            long_breakout = current_close > self.high20[-2]
            
            if (long_di_cross and long_adx_strong and long_bifurcation and 
                long_market_not_ranging and long_breakout):
                
                sl_long = current_close - risk_distance
                tp_long = current_close + (self.rr_ratio * risk_distance)
                
                self.buy(size=position_size, limit=current_close, sl=sl_long, tp=tp_long)
                print(f"🌙 LONG ENTRY: Bifurcated Strength Signal! 🚀 Price: {current_close}, Size: {position_size}, SL: {sl_long}, TP: {tp_long}")
            
            # 📉 Short Entry Logic 💥
            short_di_cross = (self.minus_di14[-2] < self.plus_di14[-2] and self.minus_di14[-1] > self.plus_di14[-1])
            short_adx_strong = current_adx14 > self.adx_threshold
            short_bifurcation = current_adx14 > current_adx20
            short_market_not_ranging = current_adx20 > self.adx_weak_threshold
            short_breakout = current_close < self.low20[-2]
            
            if (short_di_cross and short_adx_strong and short_bifurcation and 
                short_market_not_ranging and short_breakout):
                
                sl_short = current_close + risk_distance
                tp_short = current_close - (self.rr_ratio * risk_distance)
                
                self.sell(size=position_size, limit=current_close, sl=sl_short, tp=tp_short)
                print(f"🌙 SHORT ENTRY: Bifurcated Strength Signal! 💥 Price: {current_close}, Size: {position_size}, SL: {sl_short}, TP: {tp_short}")

# 🌙 MOON DEV'S MULTI-DATA TESTING FRAMEWORK 🚀
# Tests this strategy on 25+ data sources automatically!
if __name__ == "__main__":
    import sys
    import os
    from backtesting import Backtest
    import pandas as pd

    # FIRST: Run standard backtest and print stats (REQUIRED for parsing!)
    print("\n🌙 Running initial backtest for stats extraction...")
    data = pd.read_csv('./src/data/rbi/BTC-USD-15m.csv')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data.rename(columns={'datetime': 'Datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
    data['Datetime'] = pd.to_datetime(data['Datetime'])
    data = data.set_index('Datetime')
    # 🌙 Moon Dev Debug: Data loaded and cleaned! Columns: Open, High, Low, Close, Volume 🚀
    print(f"🌙 Data shape: {data.shape}, Columns: {list(data.columns)}")

    bt = Backtest(data, BifurcatedStrength, cash=1_000_000, commission=0.002, trade_on_close=True)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print("="*80 + "\n")

    # THEN: Run multi-data testing
    sys.path.append('/Users/md/Dropbox/dev/github/moon-dev-trading-bots/backtests')
    from multi_data_tester import test_on_all_data

    print("\n" + "="*80)
    print("🚀 MOON DEV'S MULTI-DATA BACKTEST - Testing on 25+ Data Sources!")
    print("="*80)

    # Test this strategy on all configured data sources
    # This will test on: BTC, ETH, SOL (multiple timeframes), AAPL, TSLA, ES, NQ, GOOG, NVDA
    # IMPORTANT: verbose=False to prevent plotting (causes timeouts in parallel processing!)
    results = test_on_all_data(BifurcatedStrength, 'BifurcatedStrength', verbose=False)

    if results is not None:
        print("\n✅ Multi-data testing complete! Results saved in ./results/ folder")
        print(f"📊 Tested on {len(results)} different data sources")
    else:
        print("\n⚠️ No results generated - check for errors above")