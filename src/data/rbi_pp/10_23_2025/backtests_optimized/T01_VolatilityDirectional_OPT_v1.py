import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.columns = [col.title() for col in data.columns]
data['Datetime'] = pd.to_datetime(data['Datetime'])
data.set_index('Datetime', inplace=True)
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VolatilityDirectional(Strategy):
    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        vol = self.data.Volume
        # 🌙 Moon Dev: Kept core BBANDS for volatility bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        # 🌙 Moon Dev: Kept ADX/DI for trend strength and direction
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        # 🌙 Moon Dev: Optimized trend filter to longer SMA200 for better regime detection on 15m timeframe
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        # 🌙 Moon Dev: Added ATR for dynamic, volatility-based SL/TP placement (improves risk management)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        # 🌙 Moon Dev: Added RSI for momentum confirmation on entries (filters low-quality setups)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        # 🌙 Moon Dev: Added volume MA for confirmation (avoids low-volume false signals)
        self.vol_ma = self.I(talib.SMA, vol, timeperiod=20)

    def next(self):
        # 🌙 Moon Dev: Extended warm-up to account for SMA200
        if len(self.data) < 205:
            return

        if not self.position:
            self.entry_price = None
            self.current_sl = None
            self.initial_risk = None

        close = self.data.Close[-1]
        prev_close = self.data.Close[-2]
        bb_u = self.bb_upper[-1]
        bb_m = self.bb_middle[-1]
        bb_l = self.bb_lower[-1]
        bb_w = (bb_u - bb_l) / bb_m if bb_m != 0 else 0
        # 🌙 Moon Dev: Slightly tightened squeeze threshold for higher quality low-vol setups
        squeeze = bb_w < 0.015
        # 🌙 Moon Dev: Lowered ADX threshold to 20 for more opportunities while maintaining trend filter
        adx_strong = self.adx[-1] > 20
        # 🌙 Moon Dev: Simplified DI to directional bias instead of cross (reduces missed trades, more realistic)
        plus_di_dir = self.plus_di[-1] > self.minus_di[-1]
        minus_di_dir = self.minus_di[-1] > self.plus_di[-1]
        # 🌙 Moon Dev: Used longer SMA for robust trend filter
        trend_up = close > self.sma200[-1]
        trend_down = close < self.sma200[-1]
        # 🌙 Moon Dev: Added volume confirmation for better entry quality
        volume_confirm = self.data.Volume[-1] > self.vol_ma[-1]

        # 🌙 Moon Dev: Long entry optimization - added RSI momentum filter to pullback/squeeze for better setups
        pullback_long = close <= bb_l
        squeeze_long = squeeze and close > bb_m
        long_momentum = (pullback_long and self.rsi[-1] < 35) or (squeeze_long and self.rsi[-1] > 55)
        if not self.position and long_momentum and adx_strong and plus_di_dir and trend_up and volume_confirm:
            entry_price = close
            atr_val = self.atr[-1]
            sl_dist = 1.5 * atr_val  # 🌙 Moon Dev: ATR-based SL for dynamic risk (avoids tight fixed % SL)
            sl_price = entry_price - sl_dist
            risk_dist = sl_dist
            if risk_dist > 0:
                risk_amount = self.equity * 0.015  # 🌙 Moon Dev: Increased risk to 1.5% for higher returns (balanced)
                pos_size = risk_amount / risk_dist  # 🌙 Moon Dev: Allow fractional size, removed vol_adjust (ATR handles vol)
                tp_dist = 3 * risk_dist  # 🌙 Moon Dev: Improved RR to 1:3 for higher reward potential
                tp_price = entry_price + tp_dist
                self.buy(size=pos_size, sl=sl_price, tp=tp_price)
                self.entry_price = entry_price
                self.current_sl = sl_price
                self.initial_risk = risk_dist
                print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, size {pos_size:.4f}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀")

        # 🌙 Moon Dev: Short entry optimization - symmetric to long with RSI filter
        pullback_short = close >= bb_u
        squeeze_short = squeeze and close < bb_m
        short_momentum = (pullback_short and self.rsi[-1] > 65) or (squeeze_short and self.rsi[-1] < 45)
        if not self.position and short_momentum and adx_strong and minus_di_dir and trend_down and volume_confirm:
            entry_price = close
            atr_val = self.atr[-1]
            sl_dist = 1.5 * atr_val
            sl_price = entry_price + sl_dist
            risk_dist = sl_dist
            if risk_dist > 0:
                risk_amount = self.equity * 0.015
                pos_size = risk_amount / risk_dist
                tp_dist = 3 * risk_dist
                tp_price = entry_price - tp_dist
                self.sell(size=pos_size, sl=sl_price, tp=tp_price)
                self.entry_price = entry_price
                self.current_sl = sl_price
                self.initial_risk = risk_dist
                print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, size {pos_size:.4f}, SL {sl_price:.2f}, TP {tp_price:.2f} ✨")

        # Additional exits and trailing
        if self.position:
            entry_price_pos = self.entry_price
            initial_risk = self.initial_risk

            # 🌙 Moon Dev: Simplified DI reverse to directional change (consistent with entry)
            if self.position.is_long and minus_di_dir:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Long exit on DI reverse at {close:.2f} 🚀")
                return
            if self.position.is_short and plus_di_dir:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Short exit on DI reverse at {close:.2f} 🚀")
                return

            # 🌙 Moon Dev: Tightened ADX exit to <15 for quicker exits in weakening trends
            if self.adx[-1] < 15:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Exit on weak ADX at {close:.2f} ✨")
                return

            # 🌙 Moon Dev: Kept BB extreme exit as additional filter (complements TP)
            if self.position.is_long and close > bb_u:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Long exit on BB upper at {close:.2f} ✨")
                return
            if self.position.is_short and close < bb_l:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Short exit on BB lower at {close:.2f} ✨")
                return

            # 🌙 Moon Dev: Improved trailing stop - breakeven at 1R, ATR trail at 2R (better profit locking)
            if self.position.is_long:
                profit = close - entry_price_pos
                if profit > initial_risk:
                    be_sl = entry_price_pos * 1.0005  # Slight buffer above entry
                    if be_sl > self.current_sl:
                        self.current_sl = be_sl
                        print(f"🌙 Moon Dev: SL to breakeven at {be_sl:.2f} 🚀")
                if profit > 2 * initial_risk:
                    trail_sl = close - 1.5 * self.atr[-1]
                    if trail_sl > self.current_sl:
                        self.current_sl = trail_sl
                        print(f"🌙 Moon Dev: Trailing SL to {trail_sl:.2f} 🚀")
            else:  # short
                profit = entry_price_pos - close
                if profit > initial_risk:
                    be_sl = entry_price_pos * 0.9995
                    if be_sl < self.current_sl:
                        self.current_sl = be_sl
                        print(f"🌙 Moon Dev: SL to breakeven at {be_sl:.2f} ✨")
                if profit > 2 * initial_risk:
                    trail_sl = close + 1.5 * self.atr[-1]
                    if trail_sl < self.current_sl:
                        self.current_sl = trail_sl
                        print(f"🌙 Moon Dev: Trailing SL to {trail_sl:.2f} ✨")

            # Manual trailing stop check
            if self.position.is_long and close <= self.current_sl:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Trailed SL hit at {close:.2f} 🚀")
                return
            if self.position.is_short and close >= self.current_sl:
                self.position.close()
                self.entry_price = None
                self.current_sl = None
                self.initial_risk = None
                print(f"🌙 Moon Dev: Trailed SL hit at {close:.2f} 🚀")
                return

bt = Backtest(data, VolatilityDirectional, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)