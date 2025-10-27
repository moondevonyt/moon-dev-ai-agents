from backtesting import Backtest, Strategy
import talib
import pandas as pd

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'datetime': 'Datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['Datetime']))
data = data.drop(columns=['Datetime'])

class StochasticHarmony(Strategy):
    swing_length = 10
    risk_per_trade = 0.01
    rr = 2
    tolerance = 0.05

    def init(self):
        self.pivots = []
        self.max_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_length)
        self.min_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_length)
        self.k, self.d = self.I(talib.STOCHRSI, self.data.Close, timeperiod=14, fastk_period=14, fastd_period=3)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        print("🌙 Moon Dev: Initialized StochasticHarmony Strategy ✨")

    def next(self):
        n = len(self.data)
        if n <= 2 * self.swing_length:
            return

        pivot_offset = self.swing_length + 1
        pivot_n = n - pivot_offset
        if pivot_n < 0:
            return

        start_idx = pivot_n - self.swing_length
        if start_idx < 0:
            return

        # Check for confirmed high pivot
        high_window = self.data.High[start_idx:n]
        if len(high_window) == 2 * self.swing_length + 1:
            pivot_high_price = self.data.High[pivot_n]
            if pivot_high_price == high_window.max():
                if not self.pivots or self.pivots[-1][0] != pivot_n:
                    self.pivots.append((pivot_n, pivot_high_price, True))
                    print(f"🌙 High Pivot confirmed at bar {pivot_n}, price {pivot_high_price:.2f} 🚀")

        # Check for confirmed low pivot
        low_window = self.data.Low[start_idx:n]
        if len(low_window) == 2 * self.swing_length + 1:
            pivot_low_price = self.data.Low[pivot_n]
            if pivot_low_price == low_window.min():
                if not self.pivots or self.pivots[-1][0] != pivot_n:
                    self.pivots.append((pivot_n, pivot_low_price, False))
                    print(f"🌙 Low Pivot confirmed at bar {pivot_n}, price {pivot_low_price:.2f} ✨")

        # Limit pivots to recent for efficiency
        if len(self.pivots) > 20:
            self.pivots = self.pivots[-10:]

        if len(self.pivots) >= 5:
            p0 = self.pivots[-1]
            p1 = self.pivots[-2]
            p2 = self.pivots[-3]
            p3 = self.pivots[-4]
            p4 = self.pivots[-5]

            # Bullish Harmonic (Gartley: low-high-low-high-low)
            if (not p4[2] and p3[2] and not p2[2] and p1[2] and not p0[2]):
                X, A, B, C, D = p4[1], p3[1], p2[1], p1[1], p0[1]
                if X < A and B < A and B > X and C > B and D < C:
                    XA = A - X
                    AB = A - B
                    BC = C - B
                    CD = C - D
                    if XA > 0 and AB > 0 and BC > 0 and CD > 0:
                        retr_ab = AB / XA
                        retr_bc = BC / AB
                        retr_xd = (A - D) / XA
                        if (abs(retr_ab - 0.618) < self.tolerance and
                            0.382 < retr_bc < 0.886 and
                            abs(retr_xd - 0.786) < self.tolerance):
                            # Stochastic RSI confirmation
                            curr_k = self.k[-1]
                            curr_d = self.d[-1]
                            prev_k = self.k[-2]
                            prev_d = self.d[-2]
                            oversold = curr_k < 20 and curr_d < 20
                            bull_cross = curr_k > curr_d and prev_k <= prev_d
                            if bull_cross and oversold and not self.position:
                                entry = self.data.Close[-1]
                                sl = X - self.atr[-1]
                                risk = entry - sl
                                if risk > 0:
                                    tp = entry + self.rr * risk
                                    size = self.risk_per_trade * entry / risk
                                    if size > 1:
                                        size = round(size)
                                    self.buy(size=size, sl=sl, tp=tp)
                                    print(f"🌙 Moon Dev: Bullish Gartley Detected! LONG entry at {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Size: {size:.4f} 🚀✨")

            # Bearish Harmonic (Gartley: high-low-high-low-high)
            elif (p4[2] and not p3[2] and p2[2] and not p1[2] and p0[2]):
                X, A, B, C, D = p4[1], p3[1], p2[1], p1[1], p0[1]
                if X > A and B > A and B < X and C < B and D > C:
                    XA = X - A
                    AB = B - A
                    BC = B - C
                    CD = D - C
                    if XA > 0 and AB > 0 and BC > 0 and CD > 0:
                        retr_ab = AB / XA
                        retr_bc = BC / AB
                        retr_xd = (D - A) / XA
                        if (abs(retr_ab - 0.618) < self.tolerance and
                            0.382 < retr_bc < 0.886 and
                            abs(retr_xd - 0.786) < self.tolerance):
                            # Stochastic RSI confirmation
                            curr_k = self.k[-1]
                            curr_d = self.d[-1]
                            prev_k = self.k[-2]
                            prev_d = self.d[-2]
                            overbought = curr_k > 80 and curr_d > 80
                            bear_cross = curr_k < curr_d and prev_k >= prev_d
                            if bear_cross and overbought and not self.position:
                                entry = self.data.Close[-1]
                                sl = X + self.atr[-1]
                                risk = sl - entry
                                if risk > 0:
                                    tp = entry - self.rr * risk
                                    size = self.risk_per_trade * entry / risk
                                    if size > 1:
                                        size = round(size)
                                    self.sell(size=size, sl=sl, tp=tp)
                                    print(f"🌙 Moon Dev: Bearish Gartley Detected! SHORT entry at {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Size: {size:.4f} 🚀✨")

        # Debug print for Stochastic RSI occasionally
        if n % 100 == 0:
            print(f"🌙 Debug: Bar {n}, K: {self.k[-1]:.2f}, D: {self.d[-1]:.2f}, ATR: {self.atr[-1]:.2f} ✨")

# Run backtest
bt = Backtest(data, StochasticHarmony, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)