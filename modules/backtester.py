"""
Vectorized Backtesting Engine

High-performance backtesting engine using pandas vectorized operations.
Simulates trading with leverage, commissions, and stop-loss/take-profit execution.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime
import warnings
from config.logging_config import get_logger

warnings.filterwarnings('ignore')
logger = get_logger(__name__)


class VectorizedBacktester:
    """
    Vectorized backtesting engine for strategy evaluation.

    Uses pandas operations to avoid slow loops, enabling fast backtesting
    of strategies against historical data.

    Attributes:
        initial_balance (float): Starting capital for backtesting
        leverage (int): Leverage multiplier for position sizing
        commission_rate (float): Trading commission per trade (0.0004 = 0.04%)
        slippage (float): Slippage per trade (0.0001 = 0.01%)
    """

    def __init__(
        self,
        initial_balance: float = 10000,
        leverage: int = 10,
        commission: float = 0.0004,
        slippage: float = 0.0001
    ):
        """
        Initialize backtester with account settings.

        Args:
            initial_balance: Starting capital in USDT
            leverage: Leverage multiplier (e.g., 10x)
            commission: Commission rate per trade (default: 0.04%)
            slippage: Slippage rate per trade (default: 0.01%)
        """
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.commission_rate = commission
        self.slippage = slippage

    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy,
        symbol: str = "BTC/USDT"
    ) -> Dict:
        """
        Run backtest on historical data with given strategy.

        Args:
            df: OHLCV DataFrame with DatetimeIndex
            strategy: Strategy instance (must have generate_signals method)
            symbol: Trading symbol name

        Returns:
            Dictionary containing:
                - total_return: Total return percentage
                - win_rate: Winning trades percentage
                - profit_factor: Gross profit / gross loss
                - max_drawdown: Maximum drawdown percentage
                - sharpe_ratio: Sharpe ratio (annualized)
                - total_trades: Number of trades executed
                - winning_trades: Number of winning trades
                - losing_trades: Number of losing trades
                - avg_win: Average winning trade percentage
                - avg_loss: Average losing trade percentage
                - equity_curve: Equity curve as pd.Series
                - trade_log: Trade log as pd.DataFrame
                - score: Composite score
        """
        if len(df) < 100:
            raise ValueError("Insufficient data for backtesting (need at least 100 candles)")

        # 1. Generate signals using strategy
        df_signals = strategy.generate_signals(df.copy())

        # 2. Simulate trades vectorized
        df_signals, trades_df = self._simulate_trades_vectorized(
            df_signals, strategy, symbol
        )

        # 3. Calculate performance metrics
        metrics = self._calculate_metrics(df_signals, trades_df)

        # 4. Calculate composite score
        metrics['score'] = self.calculate_composite_score(metrics)

        return metrics

    def _simulate_trades_vectorized(
        self,
        df: pd.DataFrame,
        strategy,
        symbol: str
    ):
        """
        Simulate trades using vectorized operations.

        Processes:
        1. Forward fill signals to maintain positions
        2. Detect entry/exit points
        3. Simulate SL/TP execution using high/low
        4. Calculate returns with leverage and fees
        5. Generate trade log

        Args:
            df: DataFrame with 'signal' column (1=long, -1=short, 0=hold)
            strategy: Strategy instance for SL/TP calculation
            symbol: Trading symbol

        Returns:
            Tuple of (df_with_equity, trades_dataframe)
        """
        # Initialize columns
        df['position'] = 0.0
        df['entry_price'] = 0.0
        df['stop_loss'] = 0.0
        df['take_profit'] = 0.0
        df['exit_reason'] = ''

        # Track trades
        trades = []
        current_position = 0
        entry_price = 0
        entry_idx = None
        stop_loss = 0
        take_profit = 0

        # Iterate through signals (unavoidable for SL/TP simulation)
        for i in range(len(df)):
            row = df.iloc[i]

            # Check if we have an open position
            if current_position != 0:
                # Check SL/TP trigger using high/low
                sl_triggered = False
                tp_triggered = False
                exit_price = None
                exit_reason = None

                if current_position == 1:  # Long position
                    # Check if stop loss hit (price went below SL)
                    if row['low'] <= stop_loss:
                        sl_triggered = True
                        exit_price = stop_loss
                        exit_reason = 'stop_loss'
                    # Check if take profit hit (price went above TP)
                    elif row['high'] >= take_profit:
                        tp_triggered = True
                        exit_price = take_profit
                        exit_reason = 'take_profit'
                    # Check for exit signal
                    elif row['signal'] == -1:
                        exit_price = row['close']
                        exit_reason = 'signal'

                elif current_position == -1:  # Short position
                    # Check if stop loss hit (price went above SL)
                    if row['high'] >= stop_loss:
                        sl_triggered = True
                        exit_price = stop_loss
                        exit_reason = 'stop_loss'
                    # Check if take profit hit (price went below TP)
                    elif row['low'] <= take_profit:
                        tp_triggered = True
                        exit_price = take_profit
                        exit_reason = 'take_profit'
                    # Check for exit signal
                    elif row['signal'] == 1:
                        exit_price = row['close']
                        exit_reason = 'signal'

                # Execute exit if triggered
                if exit_price is not None:
                    # Calculate PnL
                    if current_position == 1:
                        pnl_percent = ((exit_price - entry_price) / entry_price) * 100 * self.leverage
                    else:  # Short
                        pnl_percent = ((entry_price - exit_price) / entry_price) * 100 * self.leverage

                    # Apply fees
                    pnl_percent -= (self.commission_rate + self.slippage) * 100 * 2  # Entry + Exit

                    # Record trade
                    trades.append({
                        'entry_time': df.index[entry_idx],
                        'exit_time': df.index[i],
                        'symbol': symbol,
                        'side': 'LONG' if current_position == 1 else 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_percent': pnl_percent,
                        'exit_reason': exit_reason,
                        'bars_held': i - entry_idx
                    })

                    # Close position
                    current_position = 0
                    entry_price = 0
                    entry_idx = None
                    stop_loss = 0
                    take_profit = 0

            # Check for new entry signal
            if current_position == 0 and row['signal'] != 0:
                current_position = row['signal']
                entry_price = row['close']
                entry_idx = i

                # Calculate SL/TP using strategy methods
                if current_position == 1:  # Long
                    stop_loss = strategy.get_stop_loss_price(
                        entry_price, 'LONG', strategy.params.get('stop_loss_percent', 2.0)
                    )
                    take_profit = strategy.get_take_profit_price(
                        entry_price, 'LONG', strategy.params.get('take_profit_percent', 4.0)
                    )
                else:  # Short
                    stop_loss = strategy.get_stop_loss_price(
                        entry_price, 'SHORT', strategy.params.get('stop_loss_percent', 2.0)
                    )
                    take_profit = strategy.get_take_profit_price(
                        entry_price, 'SHORT', strategy.params.get('take_profit_percent', 4.0)
                    )

            # Record current position state
            df.iloc[i, df.columns.get_loc('position')] = current_position
            if current_position != 0:
                df.iloc[i, df.columns.get_loc('entry_price')] = entry_price
                df.iloc[i, df.columns.get_loc('stop_loss')] = stop_loss
                df.iloc[i, df.columns.get_loc('take_profit')] = take_profit

        # Close any remaining position at end
        if current_position != 0:
            exit_price = df.iloc[-1]['close']
            if current_position == 1:
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100 * self.leverage
            else:
                pnl_percent = ((entry_price - exit_price) / entry_price) * 100 * self.leverage
            pnl_percent -= (self.commission_rate + self.slippage) * 100 * 2

            trades.append({
                'entry_time': df.index[entry_idx],
                'exit_time': df.index[-1],
                'symbol': symbol,
                'side': 'LONG' if current_position == 1 else 'SHORT',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl_percent': pnl_percent,
                'exit_reason': 'end_of_data',
                'bars_held': len(df) - 1 - entry_idx
            })

        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)

        # Calculate equity curve
        if len(trades_df) > 0:
            df['equity'] = self.initial_balance
            cumulative_return = 0

            for _, trade in trades_df.iterrows():
                # Find the period this trade covers
                mask = (df.index >= trade['entry_time']) & (df.index <= trade['exit_time'])
                trade_return_pct = trade['pnl_percent'] / 100

                # Apply return at exit
                exit_mask = df.index == trade['exit_time']
                if exit_mask.any():
                    cumulative_return += trade_return_pct
                    # Update equity from exit point onwards
                    df.loc[df.index >= trade['exit_time'], 'equity'] = \
                        self.initial_balance * (1 + cumulative_return)
        else:
            # No trades, equity stays flat
            df['equity'] = self.initial_balance

        return df, trades_df

    def _calculate_metrics(
        self,
        df: pd.DataFrame,
        trades_df: pd.DataFrame
    ) -> Dict:
        """
        Calculate all performance metrics.

        Args:
            df: DataFrame with equity curve
            trades_df: DataFrame with trade log

        Returns:
            Dictionary with all metrics
        """
        metrics = {}

        # Basic equity metrics
        final_equity = df['equity'].iloc[-1]
        metrics['final_equity'] = final_equity
        metrics['total_return'] = ((final_equity / self.initial_balance) - 1) * 100

        # Trade statistics
        if len(trades_df) > 0:
            metrics['total_trades'] = len(trades_df)

            winning_trades = trades_df[trades_df['pnl_percent'] > 0]
            losing_trades = trades_df[trades_df['pnl_percent'] <= 0]

            metrics['winning_trades'] = len(winning_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = (len(winning_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0

            metrics['avg_win'] = winning_trades['pnl_percent'].mean() if len(winning_trades) > 0 else 0
            metrics['avg_loss'] = losing_trades['pnl_percent'].mean() if len(losing_trades) > 0 else 0

            # Profit factor
            gross_profit = winning_trades['pnl_percent'].sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades['pnl_percent'].sum()) if len(losing_trades) > 0 else 0
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 0

            # Average trade duration
            metrics['avg_bars_held'] = trades_df['bars_held'].mean()
        else:
            # No trades executed
            metrics['total_trades'] = 0
            metrics['winning_trades'] = 0
            metrics['losing_trades'] = 0
            metrics['win_rate'] = 0
            metrics['avg_win'] = 0
            metrics['avg_loss'] = 0
            metrics['profit_factor'] = 0
            metrics['avg_bars_held'] = 0

        # Maximum drawdown
        equity_curve = df['equity']
        running_max = equity_curve.expanding().max()
        drawdown = ((equity_curve - running_max) / running_max) * 100
        metrics['max_drawdown'] = abs(drawdown.min())

        # Sharpe ratio (annualized)
        if len(trades_df) > 0:
            returns = trades_df['pnl_percent'].values / 100
            if len(returns) > 1 and returns.std() > 0:
                # Annualize assuming ~250 trading days
                mean_return = returns.mean()
                std_return = returns.std()
                metrics['sharpe_ratio'] = (mean_return / std_return) * np.sqrt(250)
            else:
                metrics['sharpe_ratio'] = 0
        else:
            metrics['sharpe_ratio'] = 0

        # Store equity curve and trade log
        metrics['equity_curve'] = equity_curve
        metrics['trade_log'] = trades_df

        return metrics

    def calculate_composite_score(self, metrics: Dict) -> float:
        """
        Calculate composite score using formula from 기획문서.md.

        Formula: Score = (TotalReturn × 0.4) + (WinRate × 0.3) + (1/|MDD| × 100 × 0.3)

        Args:
            metrics: Dictionary with performance metrics

        Returns:
            Composite score (higher is better)
        """
        total_return = metrics['total_return']
        win_rate = metrics['win_rate']
        max_drawdown = metrics['max_drawdown']

        # Handle edge case: MDD = 0 (no drawdown)
        if max_drawdown == 0:
            mdd_component = 100  # Maximum score for MDD component
        else:
            mdd_component = (1 / max_drawdown) * 100

        # Calculate composite score
        score = (total_return * 0.4) + (win_rate * 0.3) + (mdd_component * 0.3)

        return score

    def print_results(self, metrics: Dict, verbose: bool = True):
        """
        Print backtest results in a formatted way.

        Args:
            metrics: Dictionary with performance metrics
            verbose: If True, print detailed trade log
        """
        logger.info("=" * 70)
        logger.info("BACKTEST RESULTS")
        logger.info("=" * 70)
        logger.info(f"Initial Balance:     ${self.initial_balance:,.2f}")
        logger.info(f"Final Equity:        ${metrics['final_equity']:,.2f}")
        logger.info(f"Total Return:        {metrics['total_return']:>10.2f}%")
        logger.info(f"Win Rate:            {metrics['win_rate']:>10.2f}%")
        logger.info(f"Profit Factor:       {metrics['profit_factor']:>10.2f}")
        logger.info(f"Max Drawdown:        {metrics['max_drawdown']:>10.2f}%")
        logger.info(f"Sharpe Ratio:        {metrics['sharpe_ratio']:>10.2f}")
        logger.info("-" * 70)
        logger.info(f"Total Trades:        {metrics['total_trades']:>10}")
        logger.info(f"Winning Trades:      {metrics['winning_trades']:>10}")
        logger.info(f"Losing Trades:       {metrics['losing_trades']:>10}")
        logger.info(f"Avg Win:             {metrics['avg_win']:>10.2f}%")
        logger.info(f"Avg Loss:            {metrics['avg_loss']:>10.2f}%")
        logger.info(f"Avg Bars Held:       {metrics['avg_bars_held']:>10.1f}")
        logger.info("-" * 70)
        logger.info(f"Composite Score:     {metrics['score']:>10.2f}")
        logger.info("=" * 70)

        if verbose and len(metrics['trade_log']) > 0:
            logger.info("\nTRADE LOG (First 10 trades):")
            logger.info(metrics['trade_log'].head(10).to_string())
