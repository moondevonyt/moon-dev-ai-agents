import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Load and clean data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VigorConvergence(Strategy):
    # 🌙 Moon Dev Optimization: Increased ADX threshold for stronger trend confirmation to filter out weak signals
    adx_threshold = 30
    # 🌙 Moon Dev Optimization: Slightly increased risk per trade to amplify returns while keeping risk managed
    risk_per_trade = 0.015
    # 🌙 Moon Dev Optimization: Wider ATR multiplier for SL to give trades more room, reducing premature stops
    atr_multiplier_sl = 2.0
    # 🌙 Moon Dev Optimization: Higher RR ratio to target larger profits per trade, aiming for 50%+ returns
    rr_ratio = 3.0
    # 🌙 Moon Dev Optimization: Adjusted exit threshold to hold trends longer
    adx_exit_threshold = 25

    def init(self):
        # MACD (unchanged)
        self.macd_line, self.macd_signal, self.macd_hist = self.I(
            talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        # ADX and DMI (unchanged)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # ATR for stops (unchanged)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added EMA200 for trend filter - only trade in direction of longer-term trend to avoid counter-trend traps
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        # 🌙 Moon Dev Optimization: Added RSI for momentum confirmation - ensures entries align with overall strength (RSI >50 for longs, <50 for shorts)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added Volume SMA20 filter - requires above-average volume for entries to confirm conviction and avoid low-liquidity false signals
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        # Current values (expanded for new indicators)
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_plus_di = self.plus_di[-1]
        current_minus_di = self.minus_di[-1]
        current_macd = self.macd_line[-1]
        prev_macd = self.macd_line[-2]
        current_signal = self.macd_signal[-1]
        prev_signal = self.macd_signal[-2]
        # 🌙 Moon Dev Optimization: New variables for filters
        current_ema200 = self.ema200[-1]
        current_rsi = self.rsi[-1]
        current_volume = self.data.Volume[-1]
        current_vol_sma = self.vol_sma[-1]

        # Crossover detections (unchanged)
        macd_cross_up = current_macd > current_signal and prev_macd <= prev_signal
        macd_cross_down = current_macd < current_signal and prev_macd >= prev_signal

        # Check for emergency exit if ADX weakens (adjusted threshold)
        if self.position and current_adx < self.adx_exit_threshold:
            self.position.close()
            print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.adx_exit_threshold}) at {self.data.index[-1]} 🚀")

        # Exit on opposite signal (unchanged)
        if self.position.is_long and macd_cross_down:
            self.position.close()
            print(f"🌙 Moon Dev: Long exit on bearish MACD crossover at {self.data.index[-1]} ✨")
        elif self.position.is_short and macd_cross_up:
            self.position.close()
            print(f"🌙 Moon Dev: Short exit on bullish MACD crossover at {self.data.index[-1]} ✨")

        # Entry logic only if no position (optimized with new filters)
        if not self.position:
            # 🌙 Moon Dev Optimization: Enhanced long entry - added EMA200 trend filter, RSI >50 momentum, MACD >0 zero-line confirmation, and volume > SMA for quality setups
            if (macd_cross_up and current_adx > self.adx_threshold and current_plus_di > current_minus_di and
                current_close > current_ema200 and current_rsi > 50 and current_macd > 0 and current_volume > current_vol_sma):
                # Long entry
                sl_price = current_close - self.atr_multiplier_sl * current_atr
                risk_dist = current_close - sl_price
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close + tp_dist

                # 🌙 Moon Dev Optimization: Simplified position sizing to float for precision (no int rounding), directly size = risk_amount / risk_dist for exact 1.5% risk
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # Float size in BTC units for realistic fractional positioning

                self.buy(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Long entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} (filters: ADX={current_adx:.1f}, RSI={current_rsi:.1f}, Vol>{current_vol_sma:.0f}) 🚀")

            # 🌙 Moon Dev Optimization: Enhanced short entry - symmetric filters for bearish setups
            elif (macd_cross_down and current_adx > self.adx_threshold and current_minus_di > current_plus_di and
                  current_close < current_ema200 and current_rsi < 50 and current_macd < 0 and current_volume > current_vol_sma):
                # Short entry
                sl_price = current_close + self.atr_multiplier_sl * current_atr
                risk_dist = sl_price - current_close
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close - tp_dist

                # Position sizing (same optimization as long)
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # Float size

                self.sell(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Short entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} (filters: ADX={current_adx:.1f}, RSI={current_rsi:.1f}, Vol>{current_vol_sma:.0f}) 🚀")

        # Debug print every 100 bars or so (enhanced with new indicators)
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Backtest Progress: {self.data.index[-1]}, ADX: {current_adx:.2f}, MACD: {current_macd:.2f}, RSI: {current_rsi:.1f}, Close vs EMA200: {current_close > current_ema200} ✨")

# Run backtest
bt = Backtest(data, VigorConvergence, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)