import talib
import numpy as np
from backtesting import Strategy, Backtest
import pandas as pd

class NanosecondLiquidity(Strategy):
    ema_period = 5
    threshold = 0.0005  # 0.05%
    risk_per_trade = 0.01  # 1%
    tp_pct = 0.001  # 0.1%
    sl_pct = 0.0005  # 0.05%
    
    def init(self):
        self.fair_price = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        
        def spread_func(h, l, c):
            denom = h - l
            return np.where(denom != 0, denom / c, 0)
        
        self.spread_pct = self.I(spread_func, self.data.High, self.data.Low, self.data.Close)
        self.avg_spread = self.I(talib.SMA, self.spread_pct, timeperiod=20)
        
        def imbalance_func(h, l, c):
            denom = h - l
            return np.where(denom != 0, (c - l) / denom, 0.5)
        
        self.obi = self.I(imbalance_func, self.data.High, self.data.Low, self.data.Close)
        
        self.prev_pos_size = 0
        print("🌙 Moon Dev's Nanosecond Liquidity Strategy Initialized ✨")

    def next(self):
        if len(self.fair_price) < self.ema_period:
            return
        
        # Detect exit from previous bar
        pos_size = self.position.size
        if pos_size == 0 and self.prev_pos_size != 0:
            if len(self.trades) > 0:
                new_trade = self.trades[-1]
                direction = "LONG" if new_trade.is_long else "SHORT"
                pnl = new_trade.pnl
                emoji = "💰" if pnl > 0 else "💸"
                print(f"🌙 {direction} EXIT at {new_trade.exit_price:.2f}, P&L: {pnl:.2f} {emoji} | Duration: {new_trade.length} bars | Entry: {new_trade.entry_price:.2f} 🚀")
        
        price = self.data.Close[-1]
        fair = self.fair_price[-1]
        spread = self.spread_pct[-1]
        avg_sp = self.avg_spread[-1]
        obi = self.obi[-1]
        
        # 🌙 Debug print every bar for Moon Dev monitoring
        print(f"🌙 Bar Update: Price {price:.2f}, Fair EMA {fair:.2f}, Spread {spread*100:.4f}%, Avg Spread {avg_sp*100:.4f}%, OBI {obi:.3f} 📊")
        
        if self.position:
            # Position active, monitor for HFT-style quick exits (handled by SL/TP)
            exposure_pct = abs(self.position.size * price / self.equity) * 100
            if exposure_pct > 5:  # Inventory control: max 5% exposure
                print("🌙⚠️ Inventory imbalance detected, forcing exit! 🔄")
                self.position.close()
            # Update prev_pos_size at end, but since return, set here
            self.prev_pos_size = pos_size
            return
        
        if np.isnan(avg_sp) or np.isnan(spread) or np.isnan(obi):
            self.prev_pos_size = pos_size
            return
        
        # Liquidity provision opportunity: wide spread
        if spread > avg_sp * 1.2:
            print("🌙 Wide spread detected - scanning for micro-inefficiency! 🔍")
            
            risk_amount = self.equity * self.risk_per_trade
            
            # Long entry: undervalued with bullish imbalance
            if price < fair * (1 - self.threshold) and obi > 0.4:
                stop_price = price * (1 - self.sl_pct)
                tp_price = price * (1 + self.tp_pct)
                risk_dist = price - stop_price
                if risk_dist > 0:
                    desired_size = risk_amount / risk_dist
                    max_size = self._broker._cash / price if price > 0 else 0
                    size = int(round(min(desired_size, max_size)))
                    if size > 0:
                        self.buy(size=size, limit=price, sl=stop_price, tp=tp_price)
                        print(f"🌙🚀 Nanosecond Liquidity LONG Entry at {price:.2f}! Size: {size} BTC, SL: {stop_price:.2f}, TP: {tp_price:.2f} | Risk: {risk_amount:.2f} USD ✨")
            
            # Short entry: overvalued with bearish imbalance
            elif price > fair * (1 + self.threshold) and obi < 0.6:
                stop_price = price * (1 + self.sl_pct)
                tp_price = price * (1 - self.tp_pct)
                risk_dist = stop_price - price
                if risk_dist > 0:
                    desired_size = risk_amount / risk_dist
                    max_size = self._broker._cash / price if price > 0 else 0
                    size = int(round(min(desired_size, max_size)))
                    if size > 0:
                        self.sell(size=size, limit=price, sl=stop_price, tp=tp_price)
                        print(f"🌙🔥 Nanosecond Liquidity SHORT Entry at {price:.2f}! Size: {size} BTC, SL: {stop_price:.2f}, TP: {tp_price:.2f} | Risk: {risk_amount:.2f} USD 💥")
        
        self.prev_pos_size = pos_size

# 🌙 MOON DEV'S MULTI-DATA TESTING FRAMEWORK 🚀
# Tests this strategy on 25+ data sources automatically!
if __name__ == "__main__":
    import sys
    import os
    from backtesting import Backtest

    # FIRST: Run standard backtest and print stats (REQUIRED for parsing!)
    print("\n🌙 Running initial backtest for stats extraction...")
    data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')

    bt = Backtest(data, NanosecondLiquidity, cash=1_000_000, commission=0.002)
    stats = bt.run()

    # 🌙 CRITICAL: Print full stats for Moon Dev's parser!
    print("\n" + "="*80)
    print("📊 BACKTEST STATISTICS (Moon Dev's Format)")
    print("="*80)
    print(stats)
    print(stats._strategy)
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
    results = test_on_all_data(NanosecondLiquidity, 'NanosecondLiquidity', verbose=False)

    if results is not None:
        print("\n✅ Multi-data testing complete! Results saved in ./results/ folder")
        print(f"📊 Tested on {len(results)} different data sources")
    else:
        print("\n⚠️ No results generated - check for errors above")