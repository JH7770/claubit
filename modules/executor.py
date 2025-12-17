"""
Order Executor Module
Handles order execution and position management using CCXT.
"""

import ccxt
from typing import Optional, Dict, List
from datetime import datetime
import time


class OrderExecutor:
    """Executes orders and manages positions on cryptocurrency exchanges."""

    def __init__(
        self,
        exchange_name: str = 'binance',
        api_key: str = '',
        api_secret: str = '',
        testnet: bool = False
    ):
        """
        Initialize the order executor.

        Args:
            exchange_name: Name of the exchange
            api_key: API key
            api_secret: API secret
            testnet: Whether to use testnet/sandbox
        """
        self.exchange_name = exchange_name
        self.testnet = testnet
        self.exchange = self._initialize_exchange(exchange_name, api_key, api_secret, testnet)

    def _initialize_exchange(
        self,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        testnet: bool
    ):
        """Initialize CCXT exchange instance."""
        exchange_class = getattr(ccxt, exchange_name)

        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        }

        if testnet:
            config['options']['sandboxMode'] = True

        exchange = exchange_class(config)

        return exchange

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol.

        Args:
            symbol: Trading pair symbol
            leverage: Leverage multiplier

        Returns:
            True if successful, False otherwise
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            print(f"Set leverage to {leverage}x for {symbol}")
            return True
        except Exception as e:
            print(f"Error setting leverage: {e}")
            return False

    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        reduce_only: bool = False
    ) -> Optional[Dict]:
        """
        Create a market order.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order amount in base currency
            reduce_only: Whether this is a reduce-only order

        Returns:
            Order information dict or None if failed
        """
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True

            order = self.exchange.create_market_order(symbol, side, amount, params)

            print(f"Market order created: {side.upper()} {amount} {symbol}")
            print(f"Order ID: {order['id']}")

            return order

        except Exception as e:
            print(f"Error creating market order: {e}")
            return None

    def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        reduce_only: bool = False
    ) -> Optional[Dict]:
        """
        Create a limit order.

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in base currency
            price: Limit price
            reduce_only: Whether this is a reduce-only order

        Returns:
            Order information dict or None if failed
        """
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True

            order = self.exchange.create_limit_order(symbol, side, amount, price, params)

            print(f"Limit order created: {side.upper()} {amount} {symbol} @ ${price}")
            print(f"Order ID: {order['id']}")

            return order

        except Exception as e:
            print(f"Error creating limit order: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: ID of the order to cancel
            symbol: Trading pair symbol

        Returns:
            True if successful, False otherwise
        """
        try:
            self.exchange.cancel_order(order_id, symbol)
            print(f"Order {order_id} cancelled successfully")
            return True

        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False

    def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """
        Cancel all open orders.

        Args:
            symbol: Trading pair symbol (if None, cancels all orders)

        Returns:
            True if successful, False otherwise
        """
        try:
            if symbol:
                self.exchange.cancel_all_orders(symbol)
                print(f"All orders for {symbol} cancelled")
            else:
                # Cancel orders for all symbols
                open_orders = self.get_open_orders()
                for order in open_orders:
                    self.cancel_order(order['id'], order['symbol'])
                print("All orders cancelled")

            return True

        except Exception as e:
            print(f"Error cancelling orders: {e}")
            return False

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders.

        Args:
            symbol: Trading pair symbol (if None, gets all open orders)

        Returns:
            List of open orders
        """
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders

        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Position information dict or None if no position
        """
        try:
            positions = self.exchange.fetch_positions([symbol])

            for pos in positions:
                if pos['symbol'] == symbol and float(pos['contracts']) != 0:
                    return {
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'contracts': float(pos['contracts']),
                        'entry_price': float(pos['entryPrice']),
                        'unrealized_pnl': float(pos['unrealizedPnl']),
                        'leverage': float(pos['leverage']),
                        'liquidation_price': float(pos['liquidationPrice']) if pos['liquidationPrice'] else None
                    }

            return None

        except Exception as e:
            print(f"Error fetching position: {e}")
            return None

    def close_position(self, symbol: str) -> bool:
        """
        Close an existing position using market order.

        Args:
            symbol: Trading pair symbol

        Returns:
            True if successful, False otherwise
        """
        try:
            position = self.get_position(symbol)

            if not position:
                print(f"No open position for {symbol}")
                return False

            # Determine close side (opposite of position side)
            close_side = 'sell' if position['side'] == 'long' else 'buy'
            amount = abs(position['contracts'])

            # Create reduce-only market order
            order = self.create_market_order(symbol, close_side, amount, reduce_only=True)

            if order:
                print(f"Position closed for {symbol}")
                return True
            else:
                return False

        except Exception as e:
            print(f"Error closing position: {e}")
            return False

    def close_all_positions(self, reason: str = "manual") -> Dict[str, any]:
        """
        Close all open positions using market orders.

        Args:
            reason: Reason for closing positions (e.g., "manual", "emergency", "dashboard_force_close")

        Returns:
            Dict containing:
                - success: bool
                - positions_closed: int
                - positions_failed: int
                - total_pnl: float
                - closed_positions: List[Dict]
                - errors: List[Dict]
        """
        closed_positions = []
        errors = []
        total_pnl = 0.0

        try:
            # Cancel all pending orders first
            self.cancel_all_orders()

            # Get all active positions from exchange
            positions = self.exchange.fetch_positions()
            active_positions = [pos for pos in positions if float(pos.get('contracts', 0)) != 0]

            if not active_positions:
                print("No active positions to close")
                return {
                    'success': True,
                    'positions_closed': 0,
                    'positions_failed': 0,
                    'total_pnl': 0.0,
                    'closed_positions': [],
                    'errors': []
                }

            # Close each position
            for position in active_positions:
                try:
                    symbol = position['symbol']
                    side = position['side']
                    contracts = abs(float(position['contracts']))
                    unrealized_pnl = float(position.get('unrealizedPnl', 0))

                    # Determine close side (opposite of position side)
                    close_side = 'sell' if side == 'long' else 'buy'

                    # Create reduce-only market order
                    order = self.create_market_order(symbol, close_side, contracts, reduce_only=True)

                    if order:
                        closed_positions.append({
                            'symbol': symbol,
                            'side': side,
                            'contracts': contracts,
                            'pnl': unrealized_pnl,
                            'order_id': order['id']
                        })
                        total_pnl += unrealized_pnl
                        print(f"Closed position: {symbol} {side} ({contracts} contracts), PNL: ${unrealized_pnl:.2f}")
                    else:
                        errors.append({
                            'symbol': symbol,
                            'error': 'Order creation failed'
                        })
                        print(f"Failed to close position: {symbol}")

                except Exception as e:
                    errors.append({
                        'symbol': position.get('symbol', 'Unknown'),
                        'error': str(e)
                    })
                    print(f"Error closing position {position.get('symbol', 'Unknown')}: {e}")

        except Exception as e:
            print(f"Error fetching positions: {e}")
            errors.append({
                'symbol': 'ALL',
                'error': f'Failed to fetch positions: {str(e)}'
            })

        return {
            'success': len(errors) == 0,
            'positions_closed': len(closed_positions),
            'positions_failed': len(errors),
            'total_pnl': total_pnl,
            'closed_positions': closed_positions,
            'errors': errors
        }

    def set_stop_loss_take_profit(
        self,
        symbol: str,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Dict[str, bool]:
        """
        Set stop loss and take profit orders.

        Args:
            symbol: Trading pair symbol
            stop_loss_price: Stop loss trigger price
            take_profit_price: Take profit trigger price

        Returns:
            Dict with success status for SL and TP
        """
        result = {'stop_loss': False, 'take_profit': False}

        position = self.get_position(symbol)
        if not position:
            print(f"No open position for {symbol}")
            return result

        amount = abs(position['contracts'])
        close_side = 'sell' if position['side'] == 'long' else 'buy'

        # Set Stop Loss
        if stop_loss_price:
            try:
                params = {
                    'stopPrice': stop_loss_price,
                    'reduceOnly': True
                }
                sl_order = self.exchange.create_order(
                    symbol,
                    'STOP_MARKET',
                    close_side,
                    amount,
                    None,
                    params
                )
                print(f"Stop Loss set at ${stop_loss_price}")
                result['stop_loss'] = True

            except Exception as e:
                print(f"Error setting stop loss: {e}")

        # Set Take Profit
        if take_profit_price:
            try:
                params = {
                    'stopPrice': take_profit_price,
                    'reduceOnly': True
                }
                tp_order = self.exchange.create_order(
                    symbol,
                    'TAKE_PROFIT_MARKET',
                    close_side,
                    amount,
                    None,
                    params
                )
                print(f"Take Profit set at ${take_profit_price}")
                result['take_profit'] = True

            except Exception as e:
                print(f"Error setting take profit: {e}")

        return result

    def get_balance(self, currency: str = 'USDT') -> float:
        """
        Get account balance for a specific currency.

        Args:
            currency: Currency symbol (default: USDT)

        Returns:
            Available balance
        """
        try:
            balance = self.exchange.fetch_balance()
            return float(balance.get(currency, {}).get('free', 0))

        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    def get_account_info(self) -> Dict:
        """
        Get comprehensive account information.

        Returns:
            Dict with account info including balance and positions
        """
        try:
            balance = self.exchange.fetch_balance()
            positions = self.exchange.fetch_positions()

            # Filter out zero positions
            active_positions = [
                pos for pos in positions
                if float(pos.get('contracts', 0)) != 0
            ]

            return {
                'total_balance': float(balance.get('USDT', {}).get('total', 0)),
                'available_balance': float(balance.get('USDT', {}).get('free', 0)),
                'positions': active_positions,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error fetching account info: {e}")
            return {}


if __name__ == "__main__":
    # Test the executor (in testnet mode)
    print("Testing Order Executor...")

    # Note: Add your testnet API credentials to test
    executor = OrderExecutor('binance', testnet=True)

    # Get balance
    balance = executor.get_balance('USDT')
    print(f"\nUSDT Balance: ${balance:,.2f}")

    # Get account info
    account_info = executor.get_account_info()
    print(f"\nAccount Info: {account_info}")
