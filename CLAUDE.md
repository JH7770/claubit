# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

US Market Volatility Hunter is a high-leverage cryptocurrency futures trading bot that dynamically selects optimal trading strategies based on real-time market conditions. The system targets volatility spikes during US market opening hours (KST 22:30/23:30) on Binance Futures, trading BTC/USDT and ETH/USDT.

Core philosophy: "Static Strategy is Dead" - Instead of fixed strategies, the bot performs daily backtesting to select the best-performing strategy and parameters for current market conditions (meta-strategy approach).

## Common Commands

### Setup and Initialization
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (creates all tables and schema)
python database/init_db.py

# Reset database (WARNING: deletes all data)
python database/init_db.py --reset

# Verify configuration
python config/config.py
```

### Testing
```bash
# Run Phase 1 integration tests
python test_phase1.py

# Test data collection
python -c "from modules.collector import DataCollector; collector = DataCollector('binance'); collector.download_historical_data('BTC/USDT', '1m', days=1)"
```

### Configuration
Configuration is managed through `.env` file (copy from `config/.env.example`). Required variables:
- `EXCHANGE_NAME`: Exchange to use (default: binance)
- `API_KEY`, `API_SECRET`: Exchange API credentials
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Telegram notifications
- `TRADING_MODE`: 'Live' or 'Paper'
- `LEVERAGE`: Leverage multiplier (default: 10)
- Primary/secondary trading symbols

## Architecture

### Module Structure

The codebase follows a modular architecture with clear separation of concerns:

**`modules/`** - Core functional modules:
- `collector.py`: CCXT-based data collection, downloads/stores OHLCV data in Parquet format
- `executor.py`: Order execution and position management via CCXT
- `notifier.py`: Telegram bot integration for trade alerts, daily reports, errors, and heartbeats

**`strategies/`** - Trading strategy implementations:
- `base_strategy.py`: Abstract base class defining strategy interface (generate_signals, calculate_position_size, calculate_sl_tp)
- Concrete strategies inherit from BaseStrategy and implement signal generation logic

**`config/`** - Configuration management:
- `config.py`: Centralized Config class loading from .env, includes validation methods

**`database/`** - SQLite database layer:
- `init_db.py`: DatabaseManager handles schema creation and operations
- Tables: strategy_pool, backtest_results, trade_history, daily_summary

**`data/`** - OHLCV data storage (Parquet files)

### Key Design Patterns

1. **Meta-Strategy System**: Daily strategy selection process runs before market open:
   - Load recent data (3-7 days)
   - Backtest all strategies in pool with various parameters
   - Score strategies using composite metric: (TotalReturn × 0.4) + (WinRate × 0.3) + (1/|MDD| × 0.3)
   - Select best strategy/params as "Today_Config"

2. **Daily Trading Cycle** (as per 기획문서.md):
   - 20:30-21:30: Data synchronization
   - 21:30-22:20: Daily strategy selection via backtesting
   - 22:30-01:00: Live trading session (US market open)
   - 01:00+: Position cleanup and daily report

3. **Risk Management**:
   - Per-trade loss limits (MAX_DAILY_LOSS_PERCENT)
   - Circuit breaker on max loss threshold
   - TP/SL automatic setup via executor
   - Leverage configuration per Config class

4. **Strategy Pool** (see STRATEGIES.md for details):
   - ST-01: Volatility Breakout (Larry Williams inspired)
   - ST-02: RSI + Bollinger Reversion
   - ST-03: Volume Weighted MA Cross
   - ST-04: Dynamic Scalping Grid
   - Each strategy has optimizable hyperparameters

### Data Flow

1. **Data Collection**: DataCollector fetches OHLCV via CCXT → saves to `data/*.parquet`
2. **Strategy Signal**: BaseStrategy subclasses read DataFrame → generate signals (1=buy, -1=sell, 0=hold)
3. **Position Sizing**: Strategy calculates position size based on account balance and risk percent
4. **Order Execution**: OrderExecutor submits orders to exchange with TP/SL
5. **Trade Recording**: DatabaseManager logs trades to trade_history table
6. **Notification**: TelegramNotifier sends alerts for entries/exits/errors

## Development Phases

Currently at Phase 1 completion (foundation modules implemented). See README.md for phase breakdown:
- Phase 1: Foundation modules (CCXT, data collection, basic strategy, database, Telegram)
- Phase 2: 3 representative strategies + vectorized backtesting engine + Optuna integration
- Phase 3: Meta-strategy selector logic + paper trading simulator
- Phase 4: Streamlit dashboard + full system integration

## Testing Approach

Phase 1 test script (test_phase1.py) validates:
1. Configuration loading and validation
2. Database initialization and CRUD operations
3. Strategy signal generation and position sizing
4. Data collector functionality (with live price fetch if online)
5. Order executor initialization (requires API credentials)
6. Telegram notifier module structure

## Important Notes

- This is a live trading bot - always test in paper mode first (set TRADING_MODE=Paper)
- Never commit actual API keys or .env file
- Database uses SQLite for simplicity, designed for single-instance operation
- Timezone-aware operations use KST (Asia/Seoul) for US market alignment
- Data files are in Parquet format for efficiency
- Leverage and position sizing controlled via Config class
- Telegram notifications include: trade entry/exit, daily summary, error alerts, hourly heartbeat, strategy selection announcements, and risk warnings
