"""
Trade Executor for Polymarket using py-clob-client
"""
import logging
from typing import Optional, Dict
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    OrderArgs, MarketOrderArgs, OrderType, 
    BalanceAllowanceParams, AssetType
)
from py_clob_client.order_builder.constants import BUY, SELL
from config.settings import BotConfig

logger = logging.getLogger(__name__)

class TradeExecutor:
    """Execute trades on Polymarket CLOB"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> ClobClient:
        """Initialize CLOB client with authentication"""
        try:
            client = ClobClient(
                host=self.config.clob_host,
                key=self.config.private_key,
                chain_id=self.config.chain_id,
                signature_type=self.config.signature_type,
                funder=self.config.funder_address
            )
            
            # Create or derive API credentials
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)
            
            logger.info("CLOB Client connected")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize CLOB client: {e}")
            raise
    
    def get_balance(self) -> float:
        """Get USDC balance in proxy wallet"""
        try:
            balance = self.client.get_balance_allowance(
                BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
            )
            balance_usdc = int(balance["balance"]) / 1e6
            return balance_usdc
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def get_market_price(self, token_id: str) -> Dict[str, float]:
        """Get current market prices for token"""
        try:
            midpoint = self.client.get_midpoint(token_id)
            best_ask = self.client.get_price(token_id, side="BUY")
            best_bid = self.client.get_price(token_id, side="SELL")
            
            return {
                "midpoint": float(midpoint.get("mid", 0)),
                "best_ask": float(best_ask.get("price", 0)),
                "best_bid": float(best_bid.get("price", 0))
            }
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return {"midpoint": 0, "best_ask": 0, "best_bid": 0}
    
    def place_market_order(self, token_id: str, side: str, amount_usdc: float) -> Optional[Dict]:
        """
        Place a market order (Fill or Kill)
        
        Args:
            token_id: Token ID to trade
            side: "BUY" or "SELL"
            amount_usdc: Amount in USDC
        
        Returns:
            Order response or None if failed
        """
        try:
            logger.info(f"Placing MARKET {side} order: ${amount_usdc}")
            
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount_usdc,
                side=BUY if side == "BUY" else SELL,
                order_type=OrderType.FOK  # Fill or Kill
            )
            
            signed_order = self.client.create_market_order(order_args)
            response = self.client.post_order(signed_order, OrderType.FOK)
            
            if response and response.get("success"):
                logger.info(f"Order executed: {response.get('orderID', 'N/A')}")
                return response
            else:
                logger.error(f"Order failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(self, token_id: str, side: str, price: float, size: float) -> Optional[Dict]:
        """
        Place a limit order (Good Till Cancelled)
        
        Args:
            token_id: Token ID to trade
            side: "BUY" or "SELL"
            price: Limit price (0-1)
            size: Position size
        
        Returns:
            Order response or None if failed
        """
        try:
            logger.info(f"Placing LIMIT {side} order: {size} @ {price}")
            
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=BUY if side == "BUY" else SELL
            )
            
            signed_order = self.client.create_order(order_args)
            response = self.client.post_order(signed_order, OrderType.GTC)
            
            if response and response.get("success"):
                logger.info(f"Limit order placed: {response.get('orderID', 'N/A')}")
                return response
            else:
                logger.error(f"Limit order failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    def get_open_orders(self) -> list:
        """Get list of open orders"""
        try:
            return self.client.get_orders()
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            self.client.cancel_all()
            logger.info("All orders cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return False
