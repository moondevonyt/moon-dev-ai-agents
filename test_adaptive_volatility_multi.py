"""
🌙 Moon Dev's Multi-Asset/Multi-Timeframe Backtest
Tests AdaptiveVolatility strategy on BTC, ETH, SOL across 15m and 30m timeframes
"""
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from pathlib import Path
import sys

# Import the strategy class (copy from the working file)
class AdaptiveVolatility(Strategy):
    # Parameters from the successful backtest
    ema_fast_period = 13
    ema_slow_period = 34
    ema_trend_period = 89
    rsi_period = 14
    chandelier_period = 10
    chandelier_multiplier = 2.8
    lookback_trades = 25
    adx_period = 14
    volume_ema_period = 15
    min_adx = 22
    min_volume_ratio = 1.15
    atr_period = 14
    volatility_lookback = 20
    high_volatility_threshold = 0.025
    
    def init(self):
        self.ema_fast = self.I(self.calculate_ema, self.data.Close, self.ema_fast_period)
        self.ema_slow = self.I(self.calculate_ema, self.data.Close, self.ema_slow_period)
        self.ema_trend = self.I(self.calculate_ema, self.data.Close, self.ema_trend_period)
        self.rsi = self.I(self.calculate_rsi, self.data.Close, self.rsi_period)
        self.adx = self.I(self.calculate_adx, self.data.High, self.data.Low, self.data.Close, self.adx_period)
        self.volume_ema = self.I(self.calculate_ema, self.data.Volume, self.volume_ema_period)
        self.atr = self.I(self.calculate_atr, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.high_max = self.I(self.calculate_rolling_max, self.data.High, self.chandelier_period)
        self.volatility_ratio = self.I(self.calculate_volatility_ratio, self.data.Close, self.atr, self.volatility_lookback)
        self.trade_history = []
        self.current_trade = None
        self.kelly_fraction = 0.25
        
    def calculate_ema(self, prices, period):
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    def calculate_rsi(self, prices, period):
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).values
    
    def calculate_adx(self, high, low, close, period):
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        up_move = high.diff()
        down_move = low.diff().abs() * -1
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / atr)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(period).mean()
        return adx.fillna(25).values
    
    def calculate_rolling_max(self, prices, period):
        return pd.Series(prices).rolling(window=period).max().values
    
    def calculate_atr(self, high, low, close, period):
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr.fillna(true_range.mean()).values
    
    def calculate_volatility_ratio(self, close, atr, lookback):
        close_series = pd.Series(close)
        atr_series = pd.Series(atr)
        atr_ratio = atr_series / close_series
        volatility_ratio = atr_ratio.rolling(lookback).mean()
        return volatility_ratio.fillna(atr_ratio.mean()).values
    
    def calculate_chandelier_exit(self, i):
        if i < self.chandelier_period:
            return None
        return self.high_max[i] - self.atr[i] * self.chandelier_multiplier
    
    def update_trade_performance(self):
        if len(self.trade_history) < 2:
            return
        recent_trades = self.trade_history[-min(self.lookback_trades, len(self.trade_history)):]
        wins = [t for t in recent_trades if t['pnl'] > 0]
        losses = [t for t in recent_trades if t['pnl'] <= 0]
        if not wins or not losses:
            self.kelly_fraction = 0.25
            return
        win_rate = len(wins) / len(recent_trades)
        avg_win = np.mean([t['pnl'] for t in wins])
        avg_loss = np.abs(np.mean([t['pnl'] for t in losses]))
        if avg_loss == 0:
            self.kelly_fraction = 0.25
            return
        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        self.kelly_fraction = max(0.05, min(0.5, kelly * 0.5))
    
    def next(self):
        current_price = self.data.Close[-1]
        i = len(self.data.Close) - 1
        
        if i < max(self.ema_trend_period, self.chandelier_period, self.volatility_lookback):
            return
        
        # Entry logic
        if not self.position:
            ema_fast = self.ema_fast[-1]
            ema_slow = self.ema_slow[-1]
            ema_trend = self.ema_trend[-1]
            rsi = self.rsi[-1]
            adx = self.adx[-1]
            volume = self.data.Volume[-1]
            volume_ema = self.volume_ema[-1]
            volatility_ratio = self.volatility_ratio[-1]
            
            # Multi-filter entry conditions
            trend_bullish = current_price > ema_trend and ema_fast > ema_slow
            ema_crossover = ema_fast > ema_slow
            rsi_pullback = 45 <= rsi <= 60
            strong_trend = adx >= self.min_adx
            volume_confirmation = volume > volume_ema * self.min_volume_ratio
            volatility_regime = volatility_ratio < self.high_volatility_threshold
            
            if (trend_bullish and ema_crossover and rsi_pullback and 
                strong_trend and volume_confirmation and volatility_regime):
                size = self.kelly_fraction
                self.buy(size=size)
                self.current_trade = {
                    'entry_price': current_price,
                    'entry_bar': i
                }
        
        # Exit logic
        else:
            chandelier_exit = self.calculate_chandelier_exit(i)
            ema_fast = self.ema_fast[-1]
            ema_slow = self.ema_slow[-1]
            
            # Multiple exit conditions
            chandelier_hit = chandelier_exit is not None and current_price <= chandelier_exit
            ema_cross_down = ema_fast < ema_slow
            
            if chandelier_hit or ema_cross_down:
                if self.current_trade:
                    pnl_pct = (current_price - self.current_trade['entry_price']) / self.current_trade['entry_price']
                    self.trade_history.append({
                        'pnl': pnl_pct,
                        'bars_held': i - self.current_trade['entry_bar']
                    })
                    self.current_trade = None
                    self.update_trade_performance()
                self.position.close()

# Test configurations
TEST_CONFIGS = [
    {'symbol': 'BTC-USD', 'timeframe': '15m', 'file': 'BTC-USD-15m.csv'},
    {'symbol': 'BTC-USD', 'timeframe': '30m', 'file': 'BTC-USD-30m.csv'},
    {'symbol': 'ETH-USD', 'timeframe': '15m', 'file': 'ETH-USD-15m.csv'},
    {'symbol': 'ETH-USD', 'timeframe': '30m', 'file': 'ETH-USD-30m.csv'},
    {'symbol': 'SOL-USD', 'timeframe': '15m', 'file': 'SOL-USD-15m.csv'},
    {'symbol': 'SOL-USD', 'timeframe': '30m', 'file': 'SOL-USD-30m.csv'},
]

def run_multi_asset_test():
    """Run backtest across multiple assets and timeframes"""
    project_root = Path(__file__).parent
    data_dir = project_root / "src" / "data" / "ohlcv"
    
    results = []
    
    print("\n" + "="*80)
    print("🌙 Moon Dev's Multi-Asset/Multi-Timeframe Backtest 🌙")
    print("Testing AdaptiveVolatility Strategy")
    print("="*80 + "\n")
    
    for config in TEST_CONFIGS:
        print(f"\n🔍 Testing {config['symbol']} ({config['timeframe']})...")
        
        data_file = data_dir / config['file']
        
        if not data_file.exists():
            print(f"❌ Data file not found: {data_file}")
            print(f"   Skipping {config['symbol']} {config['timeframe']}")
            continue
        
        try:
            # Load data
            df = pd.read_csv(data_file)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Run backtest
            bt = Backtest(df, AdaptiveVolatility, cash=10000, commission=0.002)
            stats = bt.run()
            
            # Extract key metrics
            result = {
                'Symbol': config['symbol'],
                'Timeframe': config['timeframe'],
                'Return %': round(stats['Return [%]'], 2),
                'Buy & Hold %': round(stats['Buy & Hold Return [%]'], 2),
                'Max Drawdown %': round(stats['Max. Drawdown [%]'], 2),
                'Sharpe': round(stats['Sharpe Ratio'], 2),
                'Sortino': round(stats['Sortino Ratio'], 2),
                'Trades': stats['# Trades'],
                'Win Rate %': round(stats['Win Rate [%]'], 2) if stats['# Trades'] > 0 else 0,
                'Avg Trade %': round(stats['Avg. Trade [%]'], 2) if stats['# Trades'] > 0 else 0,
            }
            
            results.append(result)
            
            # Print individual result
            print(f"✅ {config['symbol']} {config['timeframe']}:")
            print(f"   Return: {result['Return %']}% | B&H: {result['Buy & Hold %']}%")
            print(f"   MaxDD: {result['Max Drawdown %']}% | Sharpe: {result['Sharpe']}")
            print(f"   Trades: {result['Trades']} | Win Rate: {result['Win Rate %']}%")
            
        except Exception as e:
            print(f"❌ Error testing {config['symbol']} {config['timeframe']}: {str(e)}")
            continue
    
    # Summary table
    if results:
        print("\n" + "="*80)
        print("📊 SUMMARY TABLE")
        print("="*80)
        
        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))
        
        # Save to CSV
        output_file = project_root / "adaptive_volatility_multi_test.csv"
        df_results.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Key insights
        print("\n" + "="*80)
        print("🔍 KEY INSIGHTS")
        print("="*80)
        print(f"Average Return: {df_results['Return %'].mean():.2f}%")
        print(f"Best Performer: {df_results.loc[df_results['Return %'].idxmax(), 'Symbol']} " +
              f"{df_results.loc[df_results['Return %'].idxmax(), 'Timeframe']} " +
              f"({df_results['Return %'].max():.2f}%)")
        print(f"Average Win Rate: {df_results['Win Rate %'].mean():.2f}%")
        print(f"Total Trades: {df_results['Trades'].sum()}")
        
        # 100% Winrate check
        perfect_winrate = df_results[df_results['Win Rate %'] == 100.0]
        if len(perfect_winrate) > 0:
            print(f"\n🎯 100% Win Rate found on:")
            for _, row in perfect_winrate.iterrows():
                print(f"   - {row['Symbol']} {row['Timeframe']} ({row['Trades']} trades)")
        else:
            print(f"\n⚠️ No 100% win rate found. Highest: {df_results['Win Rate %'].max():.2f}%")
    else:
        print("\n❌ No results generated. Check if data files exist in src/data/ohlcv/")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    run_multi_asset_test()
