'''

This is a Moving Average (MA) Reversal Strategy that trades Bitcoin (BTC) using two moving averages. Let me break down the key components:
1. Core Strategy Logic:
* Uses two Simple Moving Averages (SMA):
* A faster MA (shorter period, default 20)
* A slower MA (longer period, default 40)
1. Entry Rules:
* Long Position: Enter when price is above both moving averages
* Short Position: Enter when price is above fast MA but below slow MA
1. Risk Management:
* Takes profit at a percentage gain (default 10%)
* Stops loss at a percentage loss (default 10%)
* Short positions are closed when price moves above the slow MA
* Commission is set at 0.2% per trade
1. Best Performing Parameters (from the optimization results):
* Fast MA: 28 periods
* Slow MA: 30 periods
* Take Profit: 1%
* Stop Loss: 2%
1. Performance Highlights (from the in-sample test):
* Win Rate: ~65%
* Profit Factor: 2.13 (meaning for every $1 lost, $2.13 was made)
* Maximum Drawdown: 63%
* Average Trade Duration: 9 days




✨ Moon Dev's Best Parameters ✨
==================================================
Fast MA: 25
Slow MA: 30
Take Profit: 5.00%
Stop Loss: 5.00%


OG--- '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/BTCUSD-1d-1000wks-data.csv'
ial Backtest Results 🌙
==================================================
Start                     2015-07-20 00:00:00
End                       2025-04-06 00:00:00
Duration                   3548 days 00:00:00
Exposure Time [%]                   74.894336
Equity Final [$]            1928266038.468144
Equity Peak [$]             2183209601.717443
Return [%]                      192726.603847
Buy & Hold Return [%]            29372.871429
Return (Ann.) [%]                  117.703725
Volatility (Ann.) [%]              127.260967
Sharpe Ratio                           0.9249
Sortino Ratio                        3.296705
Calmar Ratio                         1.866654
Max. Drawdown [%]                  -63.055991
Avg. Drawdown [%]                  -10.457963
Max. Drawdown Duration      693 days 00:00:00
Avg. Drawdown Duration       44 days 00:00:00
# Trades                                  241
Win Rate [%]                        63.900415
Best Trade [%]                      30.409423
Worst Trade [%]                    -23.913367
Avg. Trade [%]                       3.188753
Max. Trade Duration          97 days 00:00:00
Avg. Trade Duration          11 days 00:00:00
Profit Factor                        2.015229
Expectancy [%]                       3.930273
SQN                                  1.588684
_strategy                  MAReversalStrategy
_equity_curve                             ...
_trades                         Size  Entr...


HEAVILY OPTIMIZED---


=======================================
Start                     2015-07-20 00:00:00
End                       2025-04-06 00:00:00
Duration                   3548 days 00:00:00
Exposure Time [%]                   59.876021
Equity Final [$]          2723063920552414...
Equity Peak [$]           2899476000512426...
Return [%]                2723063920552413...
Buy & Hold Return [%]            29372.871429
Return (Ann.) [%]                 3767.514795
Volatility (Ann.) [%]                     inf
Sharpe Ratio                              0.0
Sortino Ratio                      149.140801
Calmar Ratio                       142.377153
Max. Drawdown [%]                  -26.461512
Avg. Drawdown [%]                    -4.76199
Max. Drawdown Duration      152 days 00:00:00
Avg. Drawdown Duration       14 days 00:00:00
# Trades                                 1352
Win Rate [%]                        85.133136
Best Trade [%]                 1971751.962741
Worst Trade [%]                    -23.224979
Avg. Trade [%]                       2.663609
Max. Trade Duration          18 days 00:00:00
Avg. Trade Duration           1 days 00:00:00
Profit Factor                      2660.66729
Expectancy [%]                    1460.393278
SQN                                   3.53692
_strategy                 MAReversalStrate...
_equity_curve                             ...
_trades                                   ...
dtype: object

✨ Moon Dev's Best Parameters ✨
==================================================
Fast MA: 28
Slow MA: 30
Take Profit: 1.00%
Stop Loss: 2.00%


VS the buy and hold strategy---
 Key Metrics for Comparison:
==================================================
Max Drawdown: -83.80%
Average Drawdown: -10.63%
Buy & Hold Return: 29831.87%
Annualized Return: 79.75%
Sharpe Ratio: 0.56
Sortino Ratio: 1.71
Calmar Ratio: 0.95
Exposure Time: 99.94%

# IS
# '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/IS_BTCUSD-1d-1000wks-data.csv'
 Moon Dev's Initial Backtest Results 🌙
==================================================
Start                     2015-07-20 00:00:00
End                       2022-07-11 00:00:00
Duration                   2548 days 00:00:00
Exposure Time [%]                   72.584541
Equity Final [$]             732419845.206421
Equity Peak [$]             1000095559.435421
Return [%]                       73141.984521
Buy & Hold Return [%]             7022.296429
Return (Ann.) [%]                  163.602211
Volatility (Ann.) [%]              166.494873
Sharpe Ratio                         0.982626
Sortino Ratio                        4.334835
Calmar Ratio                         2.594555
Max. Drawdown [%]                  -63.055991
Avg. Drawdown [%]                  -10.798358
Max. Drawdown Duration      550 days 00:00:00
Avg. Drawdown Duration       40 days 00:00:00
# Trades                                  188
Win Rate [%]                        65.425532
Best Trade [%]                      30.409423
Worst Trade [%]                    -23.913367
Avg. Trade [%]                       3.571259
Max. Trade Duration          97 days 00:00:00
Avg. Trade Duration           9 days 00:00:00
Profit Factor                        2.137064
Expectancy [%]                       4.338711
SQN                                  1.373457
_strategy                  MAReversalStrategy
_equity_curve                             ...
_trades                         Size  Entr...
dtype: object

## OOS '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/OS_BTCUSD-1d-1000wks-data.csv' # OOS
hub/moon-dev-trading-bots/backtests/2xmareversal.py

🌙 Moon Dev's Initial Backtest Results 🌙
==================================================
Start                     2021-09-15 00:00:00
End                       2025-04-06 00:00:00
Duration                   1299 days 00:00:00
Exposure Time [%]                   77.276995
Equity Final [$]                  850435.3954
Equity Peak [$]                 1121569.53376
Return [%]                          -14.95646
Buy & Hold Return [%]               71.396183
Return (Ann.) [%]                   -5.401018
Volatility (Ann.) [%]               56.434996
Sharpe Ratio                              0.0
Sortino Ratio                             0.0
Calmar Ratio                              0.0
Max. Drawdown [%]                  -77.030609
Avg. Drawdown [%]                  -21.376496
Max. Drawdown Duration     1245 days 00:00:00
Avg. Drawdown Duration      314 days 00:00:00
# Trades                                   49
Win Rate [%]                        59.183673
Best Trade [%]                      14.636981
Worst Trade [%]                    -67.932765
Avg. Trade [%]                      -0.477616
Max. Trade Duration         259 days 00:00:00
Avg. Trade Duration          21 days 00:00:00
Profit Factor                        1.207967
Expectancy [%]                       1.074262
SQN                                 -0.190653
_strategy                  MAReversalStrategy
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object


6HR IS

on Dev's Initial Backtest Results 🌙
==================================================
Start                     2015-07-20 18:00:00
End                       2022-07-30 12:00:00
Duration                   2566 days 18:00:00
Exposure Time [%]                   86.891648
Equity Final [$]             378000113.988762
Equity Peak [$]              714140932.979921
Return [%]                       37700.011399
Buy & Hold Return [%]             8652.689286
Return (Ann.) [%]                  138.020911
Volatility (Ann.) [%]              198.235233
Sharpe Ratio                         0.696248
Sortino Ratio                        3.134873
Calmar Ratio                         1.950846
Max. Drawdown [%]                  -70.749269
Avg. Drawdown [%]                   -5.705546
Max. Drawdown Duration      550 days 12:00:00
Avg. Drawdown Duration       18 days 00:00:00
# Trades                                  296
Win Rate [%]                        56.418919
Best Trade [%]                      28.989119
Worst Trade [%]                     -20.31387
Avg. Trade [%]                       2.025406
Max. Trade Duration          72 days 18:00:00
Avg. Trade Duration           7 days 08:00:00
Profit Factor                        1.709714
Expectancy [%]                       2.619223
SQN                                  0.816775
_strategy                  MAReversalStrategy
_equity_curve                             ...
_trades                         Size  Entr...
dtype: object

6HR OS -- currently optimizing the 6 hour

🌙 Moon Dev's Initial Backtest Results 🌙
==================================================
Start                     2022-05-16 18:00:00
End                       2025-04-25 12:00:00
Duration                   1074 days 18:00:00
Exposure Time [%]                   90.843261
Equity Final [$]                2618548.14478
Equity Peak [$]                 3960963.65856
Return [%]                         161.854814
Buy & Hold Return [%]               216.22134
Return (Ann.) [%]                   38.785272
Volatility (Ann.) [%]               70.621431
Sharpe Ratio                           0.5492
Sortino Ratio                        1.240081
Calmar Ratio                          0.76686
Max. Drawdown [%]                   -50.57672
Avg. Drawdown [%]                    -5.77097
Max. Drawdown Duration      277 days 18:00:00
Avg. Drawdown Duration       20 days 02:00:00
# Trades                                   74
Win Rate [%]                        55.405405
Best Trade [%]                      13.880804
Worst Trade [%]                    -16.714277
Avg. Trade [%]                       1.319864
Max. Trade Duration          57 days 06:00:00
Avg. Trade Duration          12 days 23:00:00
Profit Factor                        1.520151
Expectancy [%]                        1.76632
SQN                                  0.858878
_strategy                  MAReversalStrategy
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object



'''


import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import matplotlib.pyplot as plt

# Load the data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/quant/BTCUSD-1d-100wks-data.csv' # OG **
# #data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/IS_BTCUSD-1d-1000wks-data.csv' # IS
# data_path ='/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/OS_BTCUSD-1d-1000wks-data.csv' # OOS
# data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/IS_BTCUSD-6h-1000wks-data.csv' # 6hr IS
# #data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/OS_BTCUSD-6h-1000wks-data.csv' # 6hr OOS
# # data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/ETHUSD-1d-1000wks-data.csv'
# # data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/IS_ETHUSD-1d-1000wks-data.csv' # ETH **
# # data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/OS_ETHUSD-1d-1000wks-data.csv'
# # data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/IS_SOLUSD-1d-1000wks-data.csv'
# # data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/coinbase/OS_SOLUSD-1d-1000wks-data.csv'
#data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/birdeye/DitHyRMQiSDhn5cnKMJV2CDDt6sVct96YrECiM49pump-4H-30days-data.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

class MAReversalStrategy(Strategy):
    # Define the parameters we'll optimize
    ma_fast = 20
    ma_slow = 40
    take_profit = 0.10  # 10%
    stop_loss = 0.10    # 10%

    def init(self):
        # Calculate moving averages using TA-Lib
        self.sma_fast = self.I(talib.SMA, self.data.Close, self.ma_fast)
        self.sma_slow = self.I(talib.SMA, self.data.Close, self.ma_slow)
        
        # Add indicators to the plot - fixed lambda functions
        self.I(lambda x: self.sma_fast, f'SMA{self.ma_fast}', overlay=True)
        self.I(lambda x: self.sma_slow, f'SMA{self.ma_slow}', overlay=True)

    def next(self):
        price = self.data.Close[-1]
        
        # Check for short setup: price above SMA20 but below SMA40
        if price > self.sma_fast[-1] and price < self.sma_slow[-1] and not self.position:
            self.sell(sl=price * (1 + self.stop_loss),
                     tp=price * (1 - self.take_profit))
        
        # Check for long setup: price above both SMAs
        elif price > self.sma_fast[-1] and price > self.sma_slow[-1] and not self.position:
            self.buy(sl=price * (1 - self.stop_loss),
                    tp=price * (1 + self.take_profit))
        
        # Close short if price moves above SMA40
        elif self.position and self.position.is_short and price > self.sma_slow[-1]:
            self.position.close()
            
# Rename columns to match Backtest.py requirements
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# Sort index in ascending order to fix the warning
data = data.sort_index(ascending=True)

# Create and run the backtest with initial parameters
bt = Backtest(data, MAReversalStrategy, cash=1000000, commission=0.002)

# Run backtest with default parameters
print("\n🌙 Moon Dev's Initial Backtest Results 🌙")
print("=" * 50)
stats = bt.run()
print(stats)

# Plot the unoptimized strategy results
print("\n📊 Showing plot for unoptimized strategy (close plot to continue)...")
bt.plot(filename=None)  # Setting filename=None to show plot instead of saving
plt.show()

# Optimize the strategy
print("\n🚀 Moon Dev's Strategy Optimization Starting 🚀")
print("=" * 50)

# Perform optimization
optimization_results = bt.optimize(
    ma_fast=range(10, 30, 3),
    ma_slow=range(30, 60, 3),
    take_profit=[i/100 for i in range(2, 20, 2)],  # 1% to 15%
    stop_loss=[i/100 for i in range(2, 20, 2)],    # 1% to 15%
    maximize='Equity Final [$]',
    constraint=lambda p: p.ma_fast < p.ma_slow
)

print("\n🎯 Moon Dev's Optimized Results 🎯")
print("=" * 50)
print(optimization_results)

# Print optimized parameters
print("\n✨ Moon Dev's Best Parameters ✨")
print("=" * 50)
print(f"Fast MA: {optimization_results._strategy.ma_fast}")
print(f"Slow MA: {optimization_results._strategy.ma_slow}")
print(f"Take Profit: {optimization_results._strategy.take_profit:.2%}")
print(f"Stop Loss: {optimization_results._strategy.stop_loss:.2%}")

# Create a new backtest with optimized parameters
optimized_bt = Backtest(data, MAReversalStrategy, cash=1000000, commission=0.002)

# Run backtest with optimized parameters
optimized_stats = optimized_bt.run(
    ma_fast=optimization_results._strategy.ma_fast,
    ma_slow=optimization_results._strategy.ma_slow,
    take_profit=optimization_results._strategy.take_profit,
    stop_loss=optimization_results._strategy.stop_loss
)

print("\n📊 Showing plot for optimized strategy...")
optimized_bt.plot(filename=None)  # Setting filename=None to show plot instead of saving
plt.show()
