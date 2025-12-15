"""
Configuration module for the trading bot.
Loads settings from environment variables and provides centralized access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Central configuration class for the trading bot."""

    # Exchange Configuration
    EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'binance')
    API_KEY = os.getenv('API_KEY', '')
    API_SECRET = os.getenv('API_SECRET', '')

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Trading Configuration
    TRADING_MODE = os.getenv('TRADING_MODE', 'Paper')  # 'Live' or 'Paper'
    LEVERAGE = int(os.getenv('LEVERAGE', 10))
    MAX_POSITION_SIZE_USDT = float(os.getenv('MAX_POSITION_SIZE_USDT', 100))
    MAX_DAILY_LOSS_PERCENT = float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5.0))

    # Trading Symbols
    PRIMARY_SYMBOL = os.getenv('PRIMARY_SYMBOL', 'BTC/USDT')
    SECONDARY_SYMBOL = os.getenv('SECONDARY_SYMBOL', 'ETH/USDT')

    # Database Configuration
    DB_PATH = os.getenv('DB_PATH', 'database/trading_bot.db')

    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Seoul')

    @classmethod
    def is_live_mode(cls):
        """Check if bot is running in live trading mode."""
        return cls.TRADING_MODE.lower() == 'live'

    @classmethod
    def validate(cls):
        """Validate critical configuration parameters."""
        errors = []

        if not cls.API_KEY or cls.API_KEY == 'your_api_key_here':
            errors.append("API_KEY is not set or is using default value")

        if not cls.API_SECRET or cls.API_SECRET == 'your_api_secret_here':
            errors.append("API_SECRET is not set or is using default value")

        if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token_here':
            errors.append("TELEGRAM_BOT_TOKEN is not set or is using default value")

        if not cls.TELEGRAM_CHAT_ID or cls.TELEGRAM_CHAT_ID == 'your_telegram_chat_id_here':
            errors.append("TELEGRAM_CHAT_ID is not set or is using default value")

        if cls.TRADING_MODE not in ['Live', 'Paper']:
            errors.append(f"Invalid TRADING_MODE: {cls.TRADING_MODE}. Must be 'Live' or 'Paper'")

        return errors

    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)."""
        print("=" * 50)
        print("Trading Bot Configuration")
        print("=" * 50)
        print(f"Exchange: {cls.EXCHANGE_NAME}")
        print(f"Trading Mode: {cls.TRADING_MODE}")
        print(f"Leverage: {cls.LEVERAGE}x")
        print(f"Max Position Size: ${cls.MAX_POSITION_SIZE_USDT}")
        print(f"Max Daily Loss: {cls.MAX_DAILY_LOSS_PERCENT}%")
        print(f"Primary Symbol: {cls.PRIMARY_SYMBOL}")
        print(f"Secondary Symbol: {cls.SECONDARY_SYMBOL}")
        print(f"Database Path: {cls.DB_PATH}")
        print(f"Timezone: {cls.TIMEZONE}")
        print(f"API Key: {'*' * 8}{cls.API_KEY[-4:] if len(cls.API_KEY) > 4 else '****'}")
        print("=" * 50)


# Create a global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    config.print_config()

    # Validate configuration
    errors = config.validate()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nConfiguration is valid!")
