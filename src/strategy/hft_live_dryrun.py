"""
🌙 Moon Dev's HFT Live Dry-Run with Binance Futures
Real market data, simulated execution

Features:
- Fetches real 1h and 5m data from Binance Futures
- Multi-symbol support (BTC, ETH, SOL, ADA, XRP, SUI)
- Real-time trend analysis
- Dry-run mode (no real orders)
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from termcolor import cprint
from pathlib import Path
import sys
import time
import os
from dotenv import load_dotenv

# Add project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.strategy.hft_multi_timeframe import HFTMultiTimeframeStrategy
from src.strategy.hft_improver_deepseek import HFTImproverDeepSeek
from src.utils.trade_logger import get_trade_logger


class BinanceFuturesHFT:
    """HFT System with Real Binance Futures Data"""
    
    def __init__(self, symbols: List[str], deepseek_key: str):
        load_dotenv()
        
        cprint("\n" + "="*70, "magenta")
        cprint("🔴 LIVE DRY-RUN MODE - BINANCE FUTURES", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Binance Futures Exchange
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}  # Use futures
        })
        
        self.symbols = symbols
        self.strategies = {}
        
        # Initialize strategy for each symbol
        for symbol in symbols:
            self.strategies[symbol] = HFTMultiTimeframeStrategy(
                informative_timeframe="1h",
                primary_timeframe="5m",
                symbol=symbol
            )
        
        # DeepSeek Improver
        self.improver = HFTImproverDeepSeek(
            api_key=deepseek_key,
            model_name="deepseek-reasoner"
        )
        
        # Trade logger
        self.trade_logger = get_trade_logger()
        
        # Timing
        self.last_hourly_check = datetime.now()
        self.session_start = datetime.now()
        
        cprint("✅ Binance Futures HFT initialized", "green")
        cprint(f"   Symbols: {', '.join(symbols)}", "white")
        cprint(f"   Mode: DRY-RUN (no real orders)", "yellow")
    
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Fetch OHLCV data from Binance Futures
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            timeframe: '1h', '5m', etc.
            limit: Number of candles
        
        Returns:
            DataFrame with OHLCV data
        """
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            cprint(f"❌ Error fetching {symbol} {timeframe}: {e}", "red")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            cprint(f"❌ Error fetching price for {symbol}: {e}", "red")
            return None
    
    def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate"""
        
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            # Convert to percentage
            return funding['fundingRate'] * 100 if funding['fundingRate'] else 0.0
        except Exception as e:
            # Default to 0 if not available
            return 0.0
    
    def scan_all_symbols(self) -> List[Dict]:
        """
        Scan all symbols for trading opportunities
        
        Returns:
            List of trading signals with symbol and direction
        """
        
        signals = []
        
        for symbol in self.symbols:
            try:
                # Fetch data
                df_1h = self.fetch_ohlcv(symbol, '1h', limit=100)
                df_5m = self.fetch_ohlcv(symbol, '5m', limit=50)
                
                if df_1h is None or df_5m is None:
                    continue
                
                # Get strategy
                strategy = self.strategies[symbol]
                
                # Analyze 1h trend
                trend = strategy.analyze_1h_trend(df_1h)
                
                # Generate 5m signal
                signal = strategy.generate_signal_1m(df_5m)
                
                if signal:
                    side, features = signal
                    
                    # Check alignment
                    if strategy.should_take_trade(side, features):
                        
                        # Get current price and funding
                        current_price = self.get_current_price(symbol)
                        funding_rate = self.get_funding_rate(symbol)
                        
                        if current_price:
                            features['funding_rate'] = funding_rate
                            
                            signals.append({
                                'symbol': symbol,
                                'side': side,
                                'entry_price': current_price,
                                'features': features,
                                'trend_1h': trend,
                                'timestamp': datetime.now()
                            })
                            
                            cprint(f"\n✨ SIGNAL: {symbol} {side.upper()}", "cyan", attrs=['bold'])
                            cprint(f"   1h Trend: {trend.upper()}", "white")
                            cprint(f"   Entry: ${current_price:.4f}", "white")
                            cprint(f"   Momentum: {features['momentum_zscore']:.2f}", "white")
                            cprint(f"   RSI: {features['rsi']:.1f}", "white")
                            cprint(f"   Funding: {funding_rate:.3f}%", "white")
                
            except Exception as e:
                cprint(f"⚠️  Error scanning {symbol}: {e}", "yellow")
                continue
        
        return signals
    
    def execute_dry_run_trade(self, signal: Dict) -> bool:
        """
        Execute trade in dry-run mode (simulated)
        
        Args:
            signal: Signal dict with symbol, side, price, features
        
        Returns:
            True if executed
        """
        
        symbol = signal['symbol']
        side = signal['side']
        entry_price = signal['entry_price']
        features = signal['features']
        
        # Position size (small for HFT)
        position_size = 0.01  # BTC equivalent
        
        # Calculate stops and targets
        stop_pct = 0.005  # 0.5%
        target_pct = 0.01  # 1%
        
        if side == 'long':
            stop_price = entry_price * (1 - stop_pct)
            target_price = entry_price * (1 + target_pct)
        else:
            stop_price = entry_price * (1 + stop_pct)
            target_price = entry_price * (1 - target_pct)
        
        cprint(f"\n🎯 DRY-RUN EXECUTION: {symbol} {side.upper()}", "green", attrs=['bold'])
        cprint(f"   Entry: ${entry_price:.4f}", "white")
        cprint(f"   Stop: ${stop_price:.4f} | Target: ${target_price:.4f}", "white")
        cprint(f"   Size: {position_size} (equivalent)", "white")
        cprint(f"   Mode: SIMULATED (no real order)", "yellow")
        
        # Add to strategy's hourly trades
        strategy = self.strategies[symbol]
        strategy.hourly_trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'size': position_size,
            'features': features,
            'reason': f"HFT Signal (1h: {signal['trend_1h']})"
        })
        
        return True
    
    def simulate_trade_outcome(self, symbol: str, side: str, entry_price: float, 
                               target_price: float, stop_price: float) -> Tuple[bool, float, float]:
        """
        Simulate trade outcome by checking price movement
        (In dry-run, we simulate based on features quality)
        
        Returns:
            (is_winner, exit_price, pnl_pct)
        """
        
        # Get latest price
        current_price = self.get_current_price(symbol)
        
        if current_price is None:
            # Fallback to simulation
            win_prob = 0.5
            is_winner = np.random.random() < win_prob
            
            if is_winner:
                exit_price = target_price
                pnl_pct = 1.0 if side == 'long' else -1.0
            else:
                exit_price = stop_price
                pnl_pct = -0.5 if side == 'long' else 0.5
            
            return is_winner, exit_price, pnl_pct
        
        # Check if hit target or stop
        if side == 'long':
            if current_price >= target_price:
                return True, target_price, 1.0
            elif current_price <= stop_price:
                return False, stop_price, -0.5
        else:
            if current_price <= target_price:
                return True, target_price, 1.0
            elif current_price >= stop_price:
                return False, stop_price, -0.5
        
        # Still in trade (simulate outcome based on momentum)
        # For dry-run, we'll simulate immediate outcome
        win_prob = 0.5
        is_winner = np.random.random() < win_prob
        
        if is_winner:
            return True, target_price, 1.0
        else:
            return False, stop_price, -0.5
    
    def run_live_session(self, duration_minutes: int = 60, scan_interval: int = 60):
        """
        Run live trading session with Binance data
        
        Args:
            duration_minutes: How long to run
            scan_interval: Seconds between scans
        """
        
        cprint("\n" + "="*70, "cyan")
        cprint(f"🔴 STARTING LIVE DRY-RUN SESSION", "cyan", attrs=['bold'])
        cprint(f"   Duration: {duration_minutes} minutes", "white")
        cprint(f"   Scan Interval: {scan_interval} seconds", "white")
        cprint(f"   Symbols: {len(self.symbols)}", "white")
        cprint("="*70 + "\n", "cyan")
        
        start_time = datetime.now()
        trades_executed = 0
        
        try:
            while (datetime.now() - start_time).total_seconds() < duration_minutes * 60:
                
                # Current time
                now = datetime.now()
                cprint(f"\n⏰ {now.strftime('%H:%M:%S')} - Scanning markets...", "cyan")
                
                # Scan all symbols
                signals = self.scan_all_symbols()
                
                if signals:
                    cprint(f"\n📊 Found {len(signals)} signals", "green")
                    
                    # Execute each signal (dry-run)
                    for signal in signals:
                        self.execute_dry_run_trade(signal)
                        trades_executed += 1
                        
                        # Simulate outcome after short delay
                        time.sleep(5)
                        
                        symbol = signal['symbol']
                        side = signal['side']
                        entry = signal['entry_price']
                        
                        # Get current trade
                        if self.strategies[symbol].hourly_trades:
                            trade = self.strategies[symbol].hourly_trades[-1]
                            
                            is_winner, exit_price, pnl_pct = self.simulate_trade_outcome(
                                symbol, side, entry,
                                trade['target_price'], trade['stop_price']
                            )
                            
                            pnl = pnl_pct * entry * 0.01 / 100  # Normalized
                            
                            # Update trade
                            trade['exit_price'] = exit_price
                            trade['pnl'] = pnl
                            trade['is_winner'] = is_winner
                            
                            # Log trade
                            self.trade_logger.log_trade(
                                symbol=symbol,
                                side=side,
                                entry_price=entry,
                                exit_price=exit_price,
                                quantity=0.01,
                                pnl=pnl,
                                pnl_pct=pnl_pct,
                                entry_time=trade['timestamp'],
                                exit_time=datetime.now(),
                                features=trade['features'],
                                reason=trade['reason']
                            )
                else:
                    cprint("   No signals found", "yellow")
                
                # Check if hourly check needed
                if (datetime.now() - self.last_hourly_check).total_seconds() >= 3600:
                    self.run_hourly_improvement()
                
                # Sleep until next scan
                cprint(f"\n⏳ Waiting {scan_interval}s until next scan...", "white")
                time.sleep(scan_interval)
        
        except KeyboardInterrupt:
            cprint("\n\n👋 Session interrupted by user", "yellow")
        
        # Final summary
        cprint("\n" + "="*70, "green")
        cprint("📊 SESSION SUMMARY", "green", attrs=['bold'])
        cprint("="*70, "green")
        cprint(f"Duration: {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes", "white")
        cprint(f"Trades Executed: {trades_executed}", "white")
        cprint(f"Symbols Monitored: {len(self.symbols)}", "white")
        cprint("="*70 + "\n", "green")
    
    def run_hourly_improvement(self):
        """Run hourly improvement check for all symbols"""
        
        cprint("\n" + "="*70, "magenta")
        cprint("🕐 HOURLY IMPROVEMENT CHECK", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Aggregate all trades from all symbols
        all_trades = []
        total_wins = 0
        total_losses = 0
        
        for symbol, strategy in self.strategies.items():
            if strategy.hourly_trades:
                all_trades.extend(strategy.hourly_trades)
                wins = sum(1 for t in strategy.hourly_trades if t.get('is_winner', False))
                losses = len(strategy.hourly_trades) - wins
                total_wins += wins
                total_losses += losses
        
        if not all_trades:
            cprint("No trades this hour - skipping improvement", "yellow")
            self.last_hourly_check = datetime.now()
            return
        
        total = len(all_trades)
        win_rate = total_wins / total if total > 0 else 0
        
        stats = {
            'hour': datetime.now().strftime("%Y-%m-%d %H:00"),
            'total_trades': total,
            'winners': total_wins,
            'losers': total_losses,
            'win_rate': win_rate,
            'total_pnl': sum(t.get('pnl', 0) for t in all_trades),
            'needs_improvement': win_rate < 0.50
        }
        
        cprint(f"Total Trades: {total}", "white")
        cprint(f"Win Rate: {win_rate:.1%}", "green" if win_rate >= 0.5 else "red")
        
        if stats['needs_improvement']:
            cprint("\n⚠️  Running DeepSeek analysis...", "yellow")
            
            analysis = self.improver.analyze_hourly_trades(all_trades, stats)
            
            if analysis:
                cprint("✅ Analysis complete - improvements proposed", "green")
        else:
            cprint("✅ Performance good - continuing", "green")
        
        # Reset all strategies
        for strategy in self.strategies.values():
            strategy.reset_hourly()
        
        self.last_hourly_check = datetime.now()


def main():
    """Run Live Dry-Run with Binance Futures"""
    
    load_dotenv()
    
    # DeepSeek Key
    deepseek_key = os.getenv('DEEPSEEK_KEY')
    if not deepseek_key:
        cprint("❌ DEEPSEEK_KEY not found in .env", "red")
        return
    
    # Symbols (Binance Futures format)
    symbols = [
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        'SOL/USDT:USDT',
        'ADA/USDT:USDT',
        'XRP/USDT:USDT',
        'SUI/USDT:USDT'
    ]
    
    cprint("\n🚀 Initializing Binance Futures HFT...", "cyan")
    
    # Initialize system
    hft = BinanceFuturesHFT(symbols, deepseek_key)
    
    # Test exchange connection
    cprint("\n🔌 Testing Binance connection...", "yellow")
    try:
        ticker = hft.exchange.fetch_ticker('BTC/USDT:USDT')
        cprint(f"✅ Connected! BTC Price: ${ticker['last']:.2f}", "green")
    except Exception as e:
        cprint(f"❌ Connection failed: {e}", "red")
        return
    
    # Run live session
    cprint("\n" + "="*70, "cyan")
    cprint("⚠️  DRY-RUN MODE - NO REAL ORDERS WILL BE PLACED", "yellow", attrs=['bold'])
    cprint("="*70 + "\n", "cyan")
    
    input("Press ENTER to start live dry-run session...")
    
    # Run for 60 minutes, scan every 60 seconds
    hft.run_live_session(
        duration_minutes=60,
        scan_interval=60  # Scan every minute
    )


if __name__ == "__main__":
    main()
