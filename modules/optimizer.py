"""
Strategy Optimizer using Optuna

Hyperparameter optimization for trading strategies using Bayesian optimization.
"""

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Type, Tuple, Optional, Callable
from datetime import datetime
import json
import warnings

# Suppress Optuna's verbose logging
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings('ignore')


class StrategyOptimizer:
    """
    Strategy parameter optimizer using Optuna.

    Uses Bayesian optimization to find optimal parameters for trading
    strategies based on historical backtesting results.

    Attributes:
        backtester: VectorizedBacktester instance for running backtests
        db_manager: Optional DatabaseManager for storing results
    """

    def __init__(self, backtester, db_manager=None):
        """
        Initialize optimizer.

        Args:
            backtester: VectorizedBacktester instance
            db_manager: Optional DatabaseManager instance for saving results
        """
        self.backtester = backtester
        self.db_manager = db_manager

    def optimize_strategy(
        self,
        strategy_class: Type,
        df: pd.DataFrame,
        param_space: Dict,
        n_trials: int = 100,
        objective_metric: str = 'profit_factor',
        timeout: int = 1800,
        min_trades: int = 10,
        max_drawdown: float = 30.0,
        show_progress: bool = True
    ) -> Tuple[Dict, pd.DataFrame]:
        """
        Optimize strategy parameters using Optuna.

        Args:
            strategy_class: Strategy class to optimize (e.g., VolatilityBreakoutStrategy)
            df: Historical OHLCV data for backtesting
            param_space: Parameter search space definition
            n_trials: Number of optimization trials
            objective_metric: Metric to maximize ('profit_factor', 'sharpe_ratio', 'score', etc.)
            timeout: Maximum optimization time in seconds
            min_trades: Minimum number of trades required (prune if not met)
            max_drawdown: Maximum allowed drawdown in percent (prune if exceeded)
            show_progress: Show progress bar

        Returns:
            Tuple of (best_params_dict, trials_dataframe)

        Example param_space:
            {
                'k': {
                    'type': 'float',
                    'low': 0.3,
                    'high': 0.8,
                    'step': 0.1
                },
                'lookback_period': {
                    'type': 'categorical',
                    'choices': [4, 8, 12, 24]
                },
                'stop_loss_percent': {
                    'type': 'float',
                    'low': 1.0,
                    'high': 3.0,
                    'step': 0.5
                }
            }
        """
        print(f"\n{'='*70}")
        print(f"OPTIMIZING: {strategy_class.__name__}")
        print(f"{'='*70}")
        print(f"Data period: {df.index[0]} to {df.index[-1]} ({len(df)} candles)")
        print(f"Trials: {n_trials}, Timeout: {timeout}s")
        print(f"Objective: Maximize {objective_metric}")
        print(f"Constraints: Min trades={min_trades}, Max DD={max_drawdown}%")
        print(f"{'='*70}\n")

        # Create objective function
        objective = self._create_objective(
            strategy_class=strategy_class,
            df=df,
            param_space=param_space,
            objective_metric=objective_metric,
            min_trades=min_trades,
            max_drawdown=max_drawdown
        )

        # Create Optuna study
        study = optuna.create_study(
            direction='maximize',
            study_name=f"{strategy_class.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Run optimization
        study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=show_progress
        )

        # Get best parameters
        best_params = study.best_params
        best_value = study.best_value

        print(f"\n{'='*70}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*70}")
        print(f"Best {objective_metric}: {best_value:.4f}")
        print(f"\nBest Parameters:")
        for param, value in best_params.items():
            print(f"  {param}: {value}")
        print(f"{'='*70}\n")

        # Convert trials to DataFrame
        trials_df = self._study_to_dataframe(study, objective_metric)

        # Save results to database if available
        if self.db_manager is not None:
            self._save_optimization_results(
                study=study,
                strategy_name=strategy_class.__name__,
                objective_metric=objective_metric,
                n_trials=n_trials
            )

        return best_params, trials_df

    def _create_objective(
        self,
        strategy_class: Type,
        df: pd.DataFrame,
        param_space: Dict,
        objective_metric: str,
        min_trades: int,
        max_drawdown: float
    ) -> Callable:
        """
        Create Optuna objective function.

        Args:
            strategy_class: Strategy class
            df: Historical data
            param_space: Parameter search space
            objective_metric: Metric to optimize
            min_trades: Minimum trades constraint
            max_drawdown: Maximum drawdown constraint

        Returns:
            Objective function for Optuna
        """
        def objective(trial: optuna.Trial) -> float:
            """
            Objective function for a single trial.

            Args:
                trial: Optuna trial object

            Returns:
                Objective metric value (to be maximized)
            """
            # Suggest parameters based on param_space
            params = {}
            for param_name, config in param_space.items():
                if config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name,
                        config['low'],
                        config['high'],
                        step=config.get('step')
                    )
                elif config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name,
                        config['low'],
                        config['high'],
                        step=config.get('step', 1)
                    )
                elif config['type'] == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name,
                        config['choices']
                    )
                else:
                    raise ValueError(f"Unknown parameter type: {config['type']}")

            # Create strategy instance with suggested parameters
            try:
                strategy = strategy_class(params=params)
            except Exception as e:
                # If strategy initialization fails, prune this trial
                raise optuna.TrialPruned()

            # Run backtest
            try:
                results = self.backtester.run_backtest(df.copy(), strategy)
            except Exception as e:
                # If backtest fails, prune this trial
                raise optuna.TrialPruned()

            # Apply constraints
            if results['total_trades'] < min_trades:
                # Not enough trades, prune
                raise optuna.TrialPruned()

            if results['max_drawdown'] > max_drawdown:
                # Drawdown too large, prune
                raise optuna.TrialPruned()

            # Return objective metric
            if objective_metric not in results:
                raise ValueError(f"Metric '{objective_metric}' not found in results")

            return results[objective_metric]

        return objective

    def _study_to_dataframe(self, study: optuna.Study, objective_metric: str) -> pd.DataFrame:
        """
        Convert Optuna study trials to DataFrame.

        Args:
            study: Completed Optuna study
            objective_metric: Name of objective metric

        Returns:
            DataFrame with trial results
        """
        trials_data = []

        for trial in study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                trial_dict = {
                    'trial_number': trial.number,
                    objective_metric: trial.value,
                }
                trial_dict.update(trial.params)
                trials_data.append(trial_dict)

        df = pd.DataFrame(trials_data)

        # Sort by objective metric (best first)
        if len(df) > 0:
            df = df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)

        return df

    def _save_optimization_results(
        self,
        study: optuna.Study,
        strategy_name: str,
        objective_metric: str,
        n_trials: int
    ):
        """
        Save optimization results to database.

        Args:
            study: Completed Optuna study
            strategy_name: Name of strategy
            objective_metric: Objective metric used
            n_trials: Number of trials run
        """
        try:
            # Prepare optimization run data
            run_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'strategy_name': strategy_name,
                'n_trials': n_trials,
                'best_score': study.best_value,
                'best_params': json.dumps(study.best_params),
                'objective_metric': objective_metric,
                'duration_seconds': (study.trials[-1].datetime_complete -
                                   study.trials[0].datetime_start).total_seconds()
            }

            # Save to database
            self.db_manager.save_optimization_run(run_data)
            print(f"✓ Optimization results saved to database")

        except Exception as e:
            print(f"⚠ Failed to save optimization results: {e}")

    def grid_search(
        self,
        strategy_class: Type,
        df: pd.DataFrame,
        param_grid: Dict,
        objective_metric: str = 'score',
        min_trades: int = 10
    ) -> pd.DataFrame:
        """
        Perform grid search over parameter combinations.

        Simpler alternative to Bayesian optimization. Tests all
        combinations of parameters in the grid.

        Args:
            strategy_class: Strategy class to test
            df: Historical data
            param_grid: Dictionary of parameter lists
            objective_metric: Metric to evaluate
            min_trades: Minimum trades required

        Returns:
            DataFrame with all results sorted by metric

        Example param_grid:
            {
                'k': [0.4, 0.5, 0.6],
                'lookback_period': [12, 24],
                'stop_loss_percent': [2.0, 3.0]
            }
        """
        print(f"\n{'='*70}")
        print(f"GRID SEARCH: {strategy_class.__name__}")
        print(f"{'='*70}")

        # Generate all combinations
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        print(f"Testing {len(combinations)} parameter combinations...")
        print(f"{'='*70}\n")

        results = []

        for i, combo in enumerate(combinations, 1):
            # Create params dict
            params = dict(zip(param_names, combo))

            # Create strategy
            strategy = strategy_class(params=params)

            # Run backtest
            try:
                backtest_results = self.backtester.run_backtest(df.copy(), strategy)

                # Skip if insufficient trades
                if backtest_results['total_trades'] < min_trades:
                    continue

                # Store results
                result_dict = {
                    'combination': i,
                    **params,
                    'total_return': backtest_results['total_return'],
                    'win_rate': backtest_results['win_rate'],
                    'profit_factor': backtest_results['profit_factor'],
                    'max_drawdown': backtest_results['max_drawdown'],
                    'sharpe_ratio': backtest_results['sharpe_ratio'],
                    'total_trades': backtest_results['total_trades'],
                    'score': backtest_results['score'],
                }
                results.append(result_dict)

                if i % 10 == 0:
                    print(f"Progress: {i}/{len(combinations)} combinations tested")

            except Exception as e:
                print(f"⚠ Combination {i} failed: {e}")
                continue

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        if len(results_df) > 0:
            # Sort by objective metric
            results_df = results_df.sort_values(
                by=objective_metric, ascending=False
            ).reset_index(drop=True)

            print(f"\n{'='*70}")
            print(f"GRID SEARCH COMPLETE")
            print(f"{'='*70}")
            print(f"Valid combinations: {len(results_df)}/{len(combinations)}")
            print(f"\nTop 5 Results:")
            print(results_df.head().to_string())
            print(f"{'='*70}\n")
        else:
            print("⚠ No valid combinations found")

        return results_df


# Parameter space definitions for each strategy
# These can be imported and used in optimization scripts

VOLATILITY_BREAKOUT_SPACE = {
    'k': {
        'type': 'float',
        'low': 0.3,
        'high': 0.8,
        'step': 0.1
    },
    'lookback_period': {
        'type': 'categorical',
        'choices': [4, 8, 12, 24]
    },
    'stop_loss_percent': {
        'type': 'float',
        'low': 1.0,
        'high': 3.0,
        'step': 0.5
    },
    'take_profit_percent': {
        'type': 'float',
        'low': 2.0,
        'high': 6.0,
        'step': 1.0
    },
}

RSI_BOLLINGER_SPACE = {
    'rsi_period': {
        'type': 'categorical',
        'choices': [9, 14, 21]
    },
    'rsi_buy_threshold': {
        'type': 'categorical',
        'choices': [20, 25, 30, 35]
    },
    'rsi_sell_threshold': {
        'type': 'categorical',
        'choices': [65, 70, 75, 80]
    },
    'bb_stddev': {
        'type': 'float',
        'low': 1.8,
        'high': 2.5,
        'step': 0.1
    },
    'stop_loss_percent': {
        'type': 'float',
        'low': 1.0,
        'high': 3.0,
        'step': 0.5
    },
    'take_profit_percent': {
        'type': 'float',
        'low': 2.0,
        'high': 6.0,
        'step': 1.0
    },
}

VOLUME_MA_CROSS_SPACE = {
    'short_window': {
        'type': 'categorical',
        'choices': [5, 10, 15, 20]
    },
    'long_window': {
        'type': 'categorical',
        'choices': [20, 30, 40, 60]
    },
    'vol_multiplier': {
        'type': 'float',
        'low': 1.2,
        'high': 3.0,
        'step': 0.3
    },
    'stop_loss_percent': {
        'type': 'float',
        'low': 1.0,
        'high': 3.0,
        'step': 0.5
    },
    'take_profit_percent': {
        'type': 'float',
        'low': 2.0,
        'high': 6.0,
        'step': 1.0
    },
}

SCALPING_GRID_SPACE = {
    'grid_lines': {
        'type': 'categorical',
        'choices': [3, 4, 5]
    },
    'gap_percent': {
        'type': 'categorical',
        'choices': [0.2, 0.3, 0.4, 0.5]
    },
    'atr_period': {
        'type': 'categorical',
        'choices': [10, 14, 20]
    },
    'atr_multiplier': {
        'type': 'categorical',
        'choices': [0.5, 1.0, 1.5, 2.0]
    },
    'use_dynamic_gap': {
        'type': 'categorical',
        'choices': [True, False]
    },
    'stop_trigger_percent': {
        'type': 'categorical',
        'choices': [1.0, 1.5, 2.0, 2.5, 3.0]
    },
    'stop_loss_percent': {
        'type': 'float',
        'low': 2.0,
        'high': 4.0,
        'step': 0.5
    },
    'take_profit_percent': {
        'type': 'categorical',
        'choices': [0.2, 0.3, 0.4, 0.5]
    },
}
