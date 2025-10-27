from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'datetime': 'Datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data.set_index(pd.to_datetime(data['Datetime']))

class QuadrupleCrossover(Strategy):
    risk_per_trade = 0.015  # Increased to 1.5% risk for higher potential returns while managing drawdown 🌙
    sma1_period = 5
    sma2_period = 13
    sma3_period = 26
    sma4_period = 50
    rsi_period = 14
    atr_period = 14
    atr_sma_period = 20
    time_exit_bars = 20  # Increased to 20 bars to allow more room for trends to develop ✨
    volatility_multiplier = 2.0  # Tightened to 2.0 for higher volatility filter to avoid choppy markets 🚀

    def init(self):
        # Switched to EMA for faster response to price changes, improving entry timing in volatile crypto markets 🌙
        self.ema1 = self.I(talib.EMA, self.data.Close, timeperiod=self.sma1_period)
        self.ema2 = self.I(talib.EMA, self.data.Close, timeperiod=self.sma2_period)
        self.ema3 = self.I(talib.EMA, self.data.Close, timeperiod=self.sma3_period)
        self.ema4 = self.I(talib.EMA, self.data.Close, timeperiod=self.sma4_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.atr_sma_period)
        # Added volume SMA filter for confirmation of momentum in entries ✨
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Added ADX for trend strength filter to avoid weak trends and focus on strong moves 🚀
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        self.entry_bar = None
        self.breakeven_set = False
        self.bar_count = -1

        print("🌙 Moon Dev: Initialized Optimized QuadrupleCrossover Strategy with EMAs, Volume, ADX, and Enhanced Exits! ✨")

    def next(self):
        self.bar_count += 1
        current_bar = self.bar_count
        current_price = self.data.Close[-1]
        entry_price = self.data.Close[-1]
        atr_val = self.atr[-1]
        rsi_val = self.rsi[-1]
        volatility_ok = self.atr[-1] > self.volatility_multiplier * self.atr_sma[-1]
        # Updated to use EMA4 for trend filter
        ema4_rising = self.ema4[-1] > self.ema4[-2]
        ema4_falling = self.ema4[-1] < self.ema4[-2]

        # Position management only if in a position
        if self.position.size != 0:
            # Check for trailing exit with EMA3 (updated from SMA3 for consistency and faster response)
            if self.position.is_long and current_price < self.ema3[-1]:
                self.position.close()
                self.entry_bar = None
                self.breakeven_set = False
                print(f"🚀 Moon Dev: Long trailing exit on EMA3 at {current_price} 🌙")
            elif self.position.is_short and current_price > self.ema3[-1]:
                self.position.close()
                self.entry_bar = None
                self.breakeven_set = False
                print(f"🚀 Moon Dev: Short trailing exit on EMA3 at {current_price} 🌙")
            
            # Time-based exit (extended for better trend capture)
            if self.entry_bar is not None and current_bar - self.entry_bar > self.time_exit_bars:
                self.position.close()
                print(f"⏰ Moon Dev: Time-based exit after {self.time_exit_bars} bars 🌙")
                self.entry_bar = None
                self.breakeven_set = False
            
            # Breakeven adjustment (kept at 1R but with EMAs for better alignment)
            if not self.breakeven_set:
                profit_threshold = atr_val * abs(self.position.size)
                if self.position.pl >= profit_threshold:
                    trade_entry_price = self.trades[-1].entry_price
                    self.position.sl = trade_entry_price
                    self.breakeven_set = True
                    print("✨ Moon Dev: Stop moved to breakeven! 🚀")

        # Entry logic only if no position
        if not self.position.size and volatility_ok:
            # Added ADX > 25 and volume > vol_sma for stronger entry filters to improve signal quality 🌙
            adx_strong = self.adx[-1] > 25
            volume_confirm = self.data.Volume[-1] > self.vol_sma[-1]
            # Long entry with tightened RSI > 55 for bullish bias
            long_crossover = self.ema1[-1] > self.ema2[-1] and self.ema1[-2] <= self.ema2[-2]
            long_alignment = (self.ema1[-1] > self.ema2[-1] > self.ema3[-1] > self.ema4[-1])
            long_rsi = rsi_val > 55  # Tightened from 50 to 55 for better momentum confirmation ✨
            long_trend = ema4_rising
            
            if long_crossover and long_alignment and long_rsi and long_trend and adx_strong and volume_confirm:
                stop_distance = atr_val
                risk_amount = self.equity * self.risk_per_trade
                intended_size = int(round(risk_amount / stop_distance))
                max_size = int(self.equity / entry_price)
                position_size = min(intended_size, max_size)
                sl_price = entry_price - stop_distance
                # Increased RR to 3:1 for higher returns on winners 🚀
                tp_price = entry_price + 3 * stop_distance
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = current_bar
                    self.breakeven_set = False
                    print(f"🌙 Moon Dev: LONG ENTRY 🚀 Price: {entry_price}, Size: {position_size}, SL: {sl_price}, TP: {tp_price} ✨")

            # Short entry with tightened RSI < 45 for bearish bias
            short_crossover = self.ema1[-1] < self.ema2[-1] and self.ema1[-2] >= self.ema2[-2]
            short_alignment = (self.ema1[-1] < self.ema2[-1] < self.ema3[-1] < self.ema4[-1])
            short_rsi = rsi_val < 45  # Tightened from 50 to 45 for better momentum confirmation ✨
            short_trend = ema4_falling
            
            if short_crossover and short_alignment and short_rsi and short_trend and adx_strong and volume_confirm:
                stop_distance = atr_val
                risk_amount = self.equity * self.risk_per_trade
                intended_size = int(round(risk_amount / stop_distance))
                max_size = int(self.equity / entry_price)
                position_size = min(intended_size, max_size)
                sl_price = entry_price + stop_distance
                # Increased RR to 3:1 for higher returns on winners 🚀
                tp_price = entry_price - 3 * stop_distance
                if position_size > 0:
                    self.sell(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = current_bar
                    self.breakeven_set = False
                    print(f"🌙 Moon Dev: SHORT ENTRY 🚀 Price: {entry_price}, Size: {position_size}, SL: {sl_price}, TP: {tp_price} ✨")

# Run backtest
bt = Backtest(data, QuadrupleCrossover, cash=1000000, commission=0.001, exclusive_orders=True, trade_on_close=True)
stats = bt.run()
print("🌙 Moon Dev: Optimized Backtest Completed! Targeting 50%+ returns with enhanced filters and RR! ✨")
print(stats)