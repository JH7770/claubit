"""
Daily Strategy Selector Module

Automates the meta-strategy selection process by backtesting all strategies
in the pool and selecting the best performer for today's trading session.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from modules.backtester import VectorizedBacktester
from modules.optimizer import StrategyOptimizer
from modules.collector import DataCollector
from modules.notifier import TelegramNotifier
from database.init_db import DatabaseManager
from config.config import Config

# Import strategies
from strategies import (
    VolatilityBreakoutStrategy,
    RSIBollingerReversionStrategy,
    VolumeWeightedMACrossStrategy
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyStrategySelector:
    """
    Automates daily strategy selection using meta-strategy approach.

    Workflow:
    1. Load recent market data (configurable lookback period)
    2. Backtest all strategies in pool with various parameters
    3. Rank strategies by composite score
    4. Select best performer as "Today's Champion"
    5. Save results to database
    6. Send Telegram notification
    """

    def __init__(
        self,
        backtester: Optional[VectorizedBacktester] = None,
        optimizer: Optional[StrategyOptimizer] = None,
        db_manager: Optional[DatabaseManager] = None,
        collector: Optional[DataCollector] = None,
        notifier: Optional[TelegramNotifier] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize daily strategy selector.

        Args:
            backtester: VectorizedBacktester instance
            optimizer: StrategyOptimizer instance
            db_manager: DatabaseManager for saving results
            collector: DataCollector for loading data
            notifier: Optional TelegramNotifier for alerts
            config: Configuration instance
        """
        self.config = config or Config()
        self.backtester = backtester or VectorizedBacktester(
            initial_balance=10000,
            leverage=self.config.LEVERAGE
        )
        self.optimizer = optimizer or StrategyOptimizer(backtester=self.backtester)
        self.db_manager = db_manager or DatabaseManager(self.config.DB_PATH)
        self.collector = collector or DataCollector(self.config.EXCHANGE_NAME)
        self.notifier = notifier

        # Strategy class mapping
        self.strategy_class_map = {
            'Volatility_Breakout': VolatilityBreakoutStrategy,
            'RSI_Bollinger_Reversion': RSIBollingerReversionStrategy,
            'Volume_MA_Cross': VolumeWeightedMACrossStrategy,
            'SMA_Cross': VolatilityBreakoutStrategy  # Fallback to existing strategy
        }

        logger.info("DailyStrategySelector initialized")

    def select_daily_strategy(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = '1m',
        lookback_days: Optional[int] = None,
        mode: Optional[str] = None
    ) -> Dict:
        """
        Main method to select best strategy for today.

        Args:
            symbols: List of symbols to analyze (default: config PRIMARY_SYMBOL)
            timeframe: Candle timeframe (default: 1m)
            lookback_days: Days of historical data (default: config SELECTOR_LOOKBACK_DAYS)
            mode: 'quick' or 'comprehensive' (default: config SELECTOR_MODE)

        Returns:
            Dict with selection results:
            {
                'selected_strategy': str,
                'selected_params': dict,
                'score': float,
                'backtest_results': dict,
                'rank_table': pd.DataFrame,
                'selection_time': datetime,
                'symbol': str
            }
        """
        symbols = symbols or [self.config.PRIMARY_SYMBOL]
        lookback_days = lookback_days or self.config.SELECTOR_LOOKBACK_DAYS
        mode = mode or self.config.SELECTOR_MODE

        logger.info(f"Starting daily strategy selection - Mode: {mode}, Lookback: {lookback_days} days")

        # Use first symbol for selection
        symbol = symbols[0]

        try:
            # 1. Load recent data
            df = self._load_recent_data(symbol, timeframe, lookback_days)
            logger.info(f"Loaded {len(df)} candles for {symbol}")

            # 2. Get strategy pool
            strategy_pool = self._get_strategy_pool()
            logger.info(f"Testing {len(strategy_pool)} strategy variants")

            # 3. Run selection based on mode
            if mode == 'quick':
                results_df = self._run_quick_selection(df, strategy_pool)
            elif mode == 'comprehensive':
                results_df = self._run_comprehensive_selection(df, strategy_pool)
            else:
                raise ValueError(f"Invalid mode: {mode}. Must be 'quick' or 'comprehensive'")

            # 4. Get best strategy
            if len(results_df) == 0:
                raise ValueError("No valid strategies found with sufficient trades")

            best_result = results_df.iloc[0]

            # 5. Save selection results
            today = datetime.now().strftime('%Y-%m-%d')
            self._save_selection_results(today, results_df, best_result)

            # 6. Send notification
            if self.notifier:
                self._send_selection_notification(best_result, results_df)

            # 7. Prepare return data
            result = {
                'selected_strategy': best_result['strategy_name'],
                'selected_params': json.loads(best_result['params']),
                'score': best_result['score'],
                'backtest_results': {
                    'total_return': best_result['total_return'],
                    'win_rate': best_result['win_rate'],
                    'profit_factor': best_result['profit_factor'],
                    'max_drawdown': best_result['max_drawdown'],
                    'sharpe_ratio': best_result['sharpe_ratio'],
                    'total_trades': best_result['total_trades']
                },
                'rank_table': results_df,
                'selection_time': datetime.now(),
                'symbol': symbol
            }

            logger.info(f"✓ Selected strategy: {result['selected_strategy']} (Score: {result['score']:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error in strategy selection: {e}", exc_info=True)
            raise

    def _load_recent_data(
        self,
        symbol: str,
        timeframe: str,
        days: int
    ) -> pd.DataFrame:
        """
        Load recent data for backtesting.

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            days: Days to load

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Try to load from local parquet file first
            data_path = Path('data') / f"{symbol.replace('/', '_')}_{timeframe}.parquet"

            if data_path.exists():
                df = pd.read_parquet(data_path)
                df.index = pd.to_datetime(df.index)

                # Check if data is recent enough
                cutoff_date = datetime.now() - timedelta(days=days + 1)
                if df.index[-1] >= cutoff_date:
                    # Filter to requested period
                    start_date = datetime.now() - timedelta(days=days)
                    df = df[df.index >= start_date]
                    logger.info(f"Loaded data from local file: {data_path}")
                    return df

            # If not available or stale, download fresh data
            logger.info(f"Downloading fresh data for {symbol}...")
            df = self.collector.download_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                days=days
            )

            if df is None or len(df) == 0:
                raise ValueError(f"Failed to download data for {symbol}")

            return df

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def _get_strategy_pool(self) -> List[Dict]:
        """
        Get list of strategies to test.

        Returns:
            List of strategy configurations with parameter variants
        """
        # Define strategy variants to test in quick mode
        strategy_pool = [
            # ST-01: Volatility Breakout variants
            {
                'name': 'Volatility_Breakout_k0.4',
                'strategy_class': VolatilityBreakoutStrategy,
                'params': {'k': 0.4, 'lookback_period': 24, 'stop_loss_percent': 2.0, 'take_profit_percent': 4.0}
            },
            {
                'name': 'Volatility_Breakout_k0.5',
                'strategy_class': VolatilityBreakoutStrategy,
                'params': {'k': 0.5, 'lookback_period': 24, 'stop_loss_percent': 2.0, 'take_profit_percent': 4.0}
            },
            {
                'name': 'Volatility_Breakout_k0.6',
                'strategy_class': VolatilityBreakoutStrategy,
                'params': {'k': 0.6, 'lookback_period': 12, 'stop_loss_percent': 2.0, 'take_profit_percent': 4.0}
            },

            # ST-02: RSI + Bollinger variants
            {
                'name': 'RSI_Bollinger_Standard',
                'strategy_class': RSIBollingerReversionStrategy,
                'params': {
                    'rsi_period': 14,
                    'rsi_buy_threshold': 30,
                    'rsi_sell_threshold': 70,
                    'bb_stddev': 2.0,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },
            {
                'name': 'RSI_Bollinger_Aggressive',
                'strategy_class': RSIBollingerReversionStrategy,
                'params': {
                    'rsi_period': 14,
                    'rsi_buy_threshold': 25,
                    'rsi_sell_threshold': 75,
                    'bb_stddev': 2.2,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },
            {
                'name': 'RSI_Bollinger_Conservative',
                'strategy_class': RSIBollingerReversionStrategy,
                'params': {
                    'rsi_period': 14,
                    'rsi_buy_threshold': 35,
                    'rsi_sell_threshold': 65,
                    'bb_stddev': 1.8,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },

            # ST-03: Volume MA Cross variants
            {
                'name': 'Volume_MA_Cross_Fast',
                'strategy_class': VolumeWeightedMACrossStrategy,
                'params': {
                    'short_window': 5,
                    'long_window': 20,
                    'vol_multiplier': 2.0,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },
            {
                'name': 'Volume_MA_Cross_Standard',
                'strategy_class': VolumeWeightedMACrossStrategy,
                'params': {
                    'short_window': 10,
                    'long_window': 30,
                    'vol_multiplier': 2.0,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },
            {
                'name': 'Volume_MA_Cross_Slow',
                'strategy_class': VolumeWeightedMACrossStrategy,
                'params': {
                    'short_window': 15,
                    'long_window': 40,
                    'vol_multiplier': 1.5,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 4.0
                }
            },
        ]

        return strategy_pool

    def _run_quick_selection(
        self,
        df: pd.DataFrame,
        strategy_pool: List[Dict]
    ) -> pd.DataFrame:
        """
        Quick selection mode: Test predefined parameter sets.

        Args:
            df: Historical data
            strategy_pool: List of strategy configs

        Returns:
            DataFrame with backtest results, sorted by score
        """
        results = []

        for i, config in enumerate(strategy_pool, 1):
            logger.info(f"  [{i}/{len(strategy_pool)}] Testing {config['name']}...")

            try:
                strategy = config['strategy_class'](params=config['params'])
                result = self.backtester.run_backtest(df, strategy, symbol='TEST')

                # Filter out strategies with insufficient trades
                if result['total_trades'] < self.config.SELECTOR_MIN_TRADES:
                    logger.warning(f"    Skipped: Only {result['total_trades']} trades (min: {self.config.SELECTOR_MIN_TRADES})")
                    continue

                results.append({
                    'strategy_name': config['name'],
                    'params': json.dumps(config['params']),
                    'total_return': result['total_return'],
                    'win_rate': result['win_rate'],
                    'profit_factor': result['profit_factor'],
                    'max_drawdown': result['max_drawdown'],
                    'sharpe_ratio': result['sharpe_ratio'],
                    'total_trades': result['total_trades'],
                    'score': result['score']
                })

                logger.info(f"    Score: {result['score']:.2f} | Return: {result['total_return']:.2f}% | Trades: {result['total_trades']}")

            except Exception as e:
                logger.error(f"    Error testing {config['name']}: {e}")
                continue

        # Rank results
        results_df = pd.DataFrame(results)
        if len(results_df) > 0:
            results_df = results_df.sort_values('score', ascending=False).reset_index(drop=True)
            results_df['rank'] = range(1, len(results_df) + 1)

        return results_df

    def _run_comprehensive_selection(
        self,
        df: pd.DataFrame,
        strategy_pool: List[Dict],
        n_trials: int = 50
    ) -> pd.DataFrame:
        """
        Comprehensive selection: Run Optuna optimization for each strategy.

        Args:
            df: Historical data
            strategy_pool: List of strategy configs
            n_trials: Optuna trials per strategy

        Returns:
            DataFrame with optimized results, sorted by score
        """
        results = []

        # Get unique strategy classes
        unique_strategies = {}
        for config in strategy_pool:
            strategy_class = config['strategy_class']
            if strategy_class not in unique_strategies:
                unique_strategies[strategy_class] = config['name'].split('_')[0:2]  # Get base name

        logger.info(f"Running comprehensive optimization for {len(unique_strategies)} strategy classes...")

        for i, (strategy_class, base_name) in enumerate(unique_strategies.items(), 1):
            name = '_'.join(base_name)
            logger.info(f"  [{i}/{len(unique_strategies)}] Optimizing {name}...")

            try:
                # Run Optuna optimization
                best_params, trials_df = self.optimizer.optimize_strategy(
                    strategy_class=strategy_class,
                    df=df,
                    n_trials=n_trials,
                    objective_metric='score',
                    min_trades=self.config.SELECTOR_MIN_TRADES
                )

                if best_params is None:
                    logger.warning(f"    No valid parameters found for {name}")
                    continue

                # Run backtest with best parameters
                strategy = strategy_class(params=best_params)
                result = self.backtester.run_backtest(df, strategy, symbol='TEST')

                results.append({
                    'strategy_name': f"{name}_Optimized",
                    'params': json.dumps(best_params),
                    'total_return': result['total_return'],
                    'win_rate': result['win_rate'],
                    'profit_factor': result['profit_factor'],
                    'max_drawdown': result['max_drawdown'],
                    'sharpe_ratio': result['sharpe_ratio'],
                    'total_trades': result['total_trades'],
                    'score': result['score']
                })

                logger.info(f"    Best Score: {result['score']:.2f} | Return: {result['total_return']:.2f}%")

            except Exception as e:
                logger.error(f"    Error optimizing {name}: {e}")
                continue

        # Rank results
        results_df = pd.DataFrame(results)
        if len(results_df) > 0:
            results_df = results_df.sort_values('score', ascending=False).reset_index(drop=True)
            results_df['rank'] = range(1, len(results_df) + 1)

        return results_df

    def _save_selection_results(
        self,
        date: str,
        results_df: pd.DataFrame,
        selected_result: pd.Series
    ):
        """
        Save selection results to database.

        Args:
            date: Selection date (YYYY-MM-DD)
            results_df: Full ranking table
            selected_result: Best strategy result
        """
        try:
            # Save all results to database
            for _, row in results_df.iterrows():
                result_data = {
                    'date': date,
                    'strategy_name': row['strategy_name'],
                    'params': row['params'],
                    'total_return': row['total_return'],
                    'win_rate': row['win_rate'],
                    'profit_factor': row['profit_factor'],
                    'max_drawdown': row['max_drawdown'],
                    'sharpe_ratio': row['sharpe_ratio'],
                    'total_trades': row['total_trades'],
                    'score': row['score'],
                    'rank': row['rank']
                }
                self.db_manager.save_backtest_result(result_data)

            logger.info(f"Saved {len(results_df)} strategy results to database")

        except Exception as e:
            logger.error(f"Error saving selection results: {e}")

    def _send_selection_notification(
        self,
        selected_result: pd.Series,
        rank_table: pd.DataFrame
    ):
        """
        Send Telegram notification with selection results.

        Args:
            selected_result: Selected strategy details
            rank_table: Full ranking table
        """
        try:
            # Format message
            message = f"""
🏆 **TODAY'S CHAMPION STRATEGY SELECTED**

**Selected Strategy:** {selected_result['strategy_name']}
**Composite Score:** {selected_result['score']:.2f}

**Backtest Performance (Last {self.config.SELECTOR_LOOKBACK_DAYS} Days):**
  • Total Return: {selected_result['total_return']:.2f}%
  • Win Rate: {selected_result['win_rate']:.2f}%
  • Profit Factor: {selected_result['profit_factor']:.2f}
  • Max Drawdown: {selected_result['max_drawdown']:.2f}%
  • Sharpe Ratio: {selected_result['sharpe_ratio']:.2f}
  • Total Trades: {int(selected_result['total_trades'])}

**Top 3 Alternatives:**
"""
            # Add top 3 alternatives
            for i in range(min(3, len(rank_table))):
                if i == 0:
                    continue  # Skip selected (already shown)
                row = rank_table.iloc[i]
                message += f"\n{i+1}. {row['strategy_name']} (Score: {row['score']:.2f})"

            message += f"\n\n📅 Selection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message += f"\n🤖 Mode: {self.config.SELECTOR_MODE.upper()}"

            self.notifier.send_strategy_selection(
                strategy_name=selected_result['strategy_name'],
                score=selected_result['score'],
                performance_metrics={
                    'total_return': selected_result['total_return'],
                    'win_rate': selected_result['win_rate'],
                    'profit_factor': selected_result['profit_factor'],
                    'max_drawdown': selected_result['max_drawdown']
                }
            )

            logger.info("Sent selection notification via Telegram")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def get_today_strategy(
        self,
        date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Retrieve the selected strategy for a given date.

        Args:
            date: Date to query (default: today)

        Returns:
            Dict with strategy details or None if not found
        """
        date = date or datetime.now().strftime('%Y-%m-%d')

        try:
            result = self.db_manager.get_best_strategy_for_date(date)

            if result:
                return {
                    'strategy_name': result['strategy_name'],
                    'params': json.loads(result['params']),
                    'score': result['score'],
                    'backtest_results': {
                        'total_return': result['total_return'],
                        'win_rate': result['win_rate'],
                        'profit_factor': result['profit_factor'],
                        'max_drawdown': result['max_drawdown'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'total_trades': result['total_trades']
                    }
                }

            logger.warning(f"No strategy selected for date: {date}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving strategy for {date}: {e}")
            return None


if __name__ == "__main__":
    # Test the selector
    print("=" * 70)
    print("Daily Strategy Selector Test")
    print("=" * 70)

    try:
        selector = DailyStrategySelector()
        result = selector.select_daily_strategy(
            symbols=['BTC/USDT'],
            timeframe='1h',
            lookback_days=7,
            mode='quick'
        )

        print(f"\n✓ Selected: {result['selected_strategy']}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Return: {result['backtest_results']['total_return']:.2f}%")
        print(f"  Win Rate: {result['backtest_results']['win_rate']:.2f}%")

    except Exception as e:
        print(f"\n✗ Error: {e}")
