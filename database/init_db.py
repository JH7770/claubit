"""
Database Initialization Script
Creates the SQLite database and all required tables.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


class DatabaseManager:
    """Manages database creation and operations."""

    def __init__(self, db_path: str = "database/trading_bot.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None

    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def initialize_database(self):
        """Create all required tables."""
        print(f"Initializing database at {self.db_path}...")

        self.connect()

        # Create strategy_pool table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS strategy_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL UNIQUE,
                description TEXT,
                params_template TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create backtest_results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                strategy_id INTEGER,
                strategy_name TEXT NOT NULL,
                params TEXT,
                total_return REAL,
                win_rate REAL,
                profit_factor REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                total_trades INTEGER,
                score REAL,
                rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategy_pool(id)
            )
        """)

        # Create trade_history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                amount REAL,
                leverage INTEGER,
                pnl REAL,
                pnl_percent REAL,
                strategy_id INTEGER,
                strategy_name TEXT,
                exit_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategy_pool(id)
            )
        """)

        # Create daily_summary table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                total_pnl REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                strategy_used TEXT,
                starting_balance REAL,
                ending_balance REAL,
                max_drawdown REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create positions table (for tracking open positions)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                amount REAL NOT NULL,
                leverage INTEGER,
                stop_loss REAL,
                take_profit REAL,
                strategy_id INTEGER,
                strategy_name TEXT,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open',
                FOREIGN KEY (strategy_id) REFERENCES strategy_pool(id)
            )
        """)

        # Create bot_status table (for tracking bot state)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                mode TEXT,
                current_balance REAL,
                daily_pnl REAL,
                active_positions INTEGER DEFAULT 0,
                last_heartbeat TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better query performance
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_backtest_date
            ON backtest_results(date)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp
            ON trade_history(timestamp)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_symbol
            ON trade_history(symbol)
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_date
            ON daily_summary(date)
        """)

        self.conn.commit()
        print("Database initialized successfully!")

        # Insert default strategies
        self._insert_default_strategies()

        self.close()

    def _insert_default_strategies(self):
        """Insert default strategies into strategy_pool."""
        default_strategies = [
            {
                'name': 'SMA_Cross',
                'description': 'Simple Moving Average Crossover Strategy',
                'params': '{"fast_period": 10, "slow_period": 20}'
            },
            {
                'name': 'Volatility_Breakout',
                'description': 'Volatility-based Breakout Strategy',
                'params': '{"k": 0.5, "window": 20}'
            },
            {
                'name': 'RSI_Scalping',
                'description': 'RSI-based Scalping Strategy',
                'params': '{"rsi_period": 14, "oversold": 30, "overbought": 70}'
            }
        ]

        for strategy in default_strategies:
            try:
                self.conn.execute("""
                    INSERT OR IGNORE INTO strategy_pool
                    (strategy_name, description, params_template)
                    VALUES (?, ?, ?)
                """, (strategy['name'], strategy['description'], strategy['params']))
            except sqlite3.IntegrityError:
                pass  # Strategy already exists

        self.conn.commit()
        print("Default strategies added to pool.")

    def add_strategy(self, name: str, description: str, params: str):
        """Add a new strategy to the pool."""
        self.connect()
        try:
            self.conn.execute("""
                INSERT INTO strategy_pool (strategy_name, description, params_template)
                VALUES (?, ?, ?)
            """, (name, description, params))
            self.conn.commit()
            print(f"Strategy '{name}' added successfully!")
        except sqlite3.IntegrityError:
            print(f"Strategy '{name}' already exists.")
        finally:
            self.close()

    def log_trade(self, trade_data: dict):
        """Log a completed trade to database."""
        self.connect()
        self.conn.execute("""
            INSERT INTO trade_history
            (timestamp, symbol, side, entry_price, exit_price, amount, leverage,
             pnl, pnl_percent, strategy_name, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('timestamp', datetime.now()),
            trade_data['symbol'],
            trade_data['side'],
            trade_data['entry_price'],
            trade_data['exit_price'],
            trade_data['amount'],
            trade_data.get('leverage', 1),
            trade_data['pnl'],
            trade_data['pnl_percent'],
            trade_data.get('strategy_name', 'Unknown'),
            trade_data.get('exit_reason', 'Manual')
        ))
        self.conn.commit()
        self.close()

    def get_daily_trades(self, date: str):
        """Get all trades for a specific date."""
        self.connect()
        cursor = self.conn.execute("""
            SELECT * FROM trade_history
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp DESC
        """, (date,))
        trades = cursor.fetchall()
        self.close()
        return trades

    def update_daily_summary(self, summary_data: dict):
        """Update or insert daily summary."""
        self.connect()
        self.conn.execute("""
            INSERT OR REPLACE INTO daily_summary
            (date, total_pnl, total_trades, winning_trades, losing_trades,
             win_rate, strategy_used, starting_balance, ending_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_data['date'],
            summary_data['total_pnl'],
            summary_data['total_trades'],
            summary_data['winning_trades'],
            summary_data['losing_trades'],
            summary_data['win_rate'],
            summary_data['strategy_used'],
            summary_data['starting_balance'],
            summary_data['ending_balance']
        ))
        self.conn.commit()
        self.close()

    def reset_database(self):
        """Drop all tables and recreate them. WARNING: This deletes all data!"""
        print("WARNING: This will delete all data!")
        confirm = input("Type 'YES' to confirm: ")

        if confirm == 'YES':
            self.connect()

            # Get all table names
            cursor = self.conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()

            # Drop all tables
            for table in tables:
                self.conn.execute(f"DROP TABLE IF EXISTS {table[0]}")

            self.conn.commit()
            self.close()

            # Reinitialize
            self.initialize_database()
            print("Database reset complete!")
        else:
            print("Reset cancelled.")


def main():
    """Main function to initialize or reset database."""
    import sys

    db_manager = DatabaseManager()

    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        db_manager.reset_database()
    else:
        db_manager.initialize_database()


if __name__ == "__main__":
    main()
