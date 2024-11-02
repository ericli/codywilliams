from typing import Optional, Dict, List
from dataclasses import dataclass
from decimal import Decimal
import logging
from enum import Enum
import asyncio
from datetime import datetime
import alpaca_trade_api as tradeapi

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "day"
    
@dataclass
class OrderResult:
    order_id: str
    status: str
    filled_qty: float
    filled_avg_price: float
    symbol: str
    side: str
    error: Optional[str] = None

class OrderExecutor:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.alpaca.markets",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_position_size: float = 10000,  # Maximum position size in dollars
        max_single_order: float = 5000,    # Maximum single order size in dollars
    ):
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_position_size = max_position_size
        self.max_single_order = max_single_order
        
        # In-memory order cache
        self._order_cache: Dict[str, OrderResult] = {}
        
    async def _check_risk_limits(self, order: OrderRequest, current_price: float) -> bool:
        """Check if order passes risk management rules"""
        try:
            # Calculate order value
            order_value = float(order.quantity) * current_price
            
            # Check single order size limit
            if order_value > self.max_single_order:
                self.logger.warning(f"Order value ${order_value} exceeds single order limit ${self.max_single_order}")
                return False
            
            # Get current position
            position = None
            try:
                position = self.api.get_position(order.symbol)
            except:
                # No position exists
                pass
            
            # Calculate potential new position size
            current_position_value = float(position.market_value) if position else 0
            if order.side == OrderSide.BUY:
                new_position_value = current_position_value + order_value
            else:
                new_position_value = current_position_value - order_value
                
            # Check position size limit
            if abs(new_position_value) > self.max_position_size:
                self.logger.warning(f"New position value ${new_position_value} would exceed position limit ${self.max_position_size}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in risk check: {str(e)}")
            return False
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            bars = self.api.get_barset(symbol, 'minute', limit=1)
            return float(bars[symbol][0].c)
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None
    
    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order with retries and safety checks"""
        for attempt in range(self.max_retries):
            try:
                # Get current price for risk checks
                current_price = await self._get_current_price(order.symbol)
                if not current_price:
                    return OrderResult(
                        order_id="",
                        status="failed",
                        filled_qty=0,
                        filled_avg_price=0,
                        symbol=order.symbol,
                        side=order.side.value,
                        error="Could not get current price"
                    )
                
                # Perform risk checks
                if not await self._check_risk_limits(order, current_price):
                    return OrderResult(
                        order_id="",
                        status="rejected",
                        filled_qty=0,
                        filled_avg_price=0,
                        symbol=order.symbol,
                        side=order.side.value,
                        error="Failed risk management checks"
                    )
                
                # Submit the order
                alpaca_order = self.api.submit_order(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=order.side.value,
                    type=order.order_type.value,
                    limit_price=order.limit_price,
                    stop_price=order.stop_price,
                    time_in_force=order.time_in_force
                )
                
                # Create result
                result = OrderResult(
                    order_id=alpaca_order.id,
                    status=alpaca_order.status,
                    filled_qty=float(alpaca_order.filled_qty or 0),
                    filled_avg_price=float(alpaca_order.filled_avg_price or 0),
                    symbol=order.symbol,
                    side=order.side.value
                )
                
                # Cache the result
                self._order_cache[alpaca_order.id] = result
                
                self.logger.info(f"Order submitted successfully: {result}")
                return result
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Order attempt {attempt + 1} failed: {str(e)}, retrying...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All order attempts failed: {str(e)}")
                    return OrderResult(
                        order_id="",
                        status="failed",
                        filled_qty=0,
                        filled_avg_price=0,
                        symbol=order.symbol,
                        side=order.side.value,
                        error=str(e)
                    )
    
    async def get_order_status(self, order_id: str) -> Optional[OrderResult]:
        """Get current status of an order"""
        try:
            # Check cache first
            if order_id in self._order_cache:
                return self._order_cache[order_id]
            
            # If not in cache, get from API
            order = self.api.get_order(order_id)
            
            result = OrderResult(
                order_id=order.id,
                status=order.status,
                filled_qty=float(order.filled_qty or 0),
                filled_avg_price=float(order.filled_avg_price or 0),
                symbol=order.symbol,
                side=order.side
            )
            
            # Update cache
            self._order_cache[order_id] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {str(e)}")
            return None
            
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        try:
            self.api.cancel_order(order_id)
            
            # Update cache
            if order_id in self._order_cache:
                self._order_cache[order_id].status = "canceled"
                
            return True
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            return False