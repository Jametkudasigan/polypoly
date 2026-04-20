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
            # Initialize client dengan funder address
            client = ClobClient(
                host=self.config.clob_host,
                key=self.config.private_key,
                chain_id=self.config.chain_id,
                signature_type=self.config.signature_type,
                funder=self.config.funder_address
            )
            
            # Derive API key dari private key
            logger.info("Deriving API credentials...")
            creds = client.derive_api_key()
            client.set_api_creds(creds)
            
            logger.info(f"CLOB Client connected (Signature Type: {self.config.signature_type})")
            logger.info(f"Funder: {self.config.funder_address[:20]}...")
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
        """
        try:
            logger.info(f"Placing MARKET {side} order: ${amount_usdc}")
            logger.debug(f"Token: {token_id[:30]}...")
            
            # Gunakan GTC (Good Till Cancel) untuk market order yang lebih reliable
            # atau FOK (Fill or Kill) untuk instant execution
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount_usdc,
                side=BUY if side == "BUY" else SELL,
                order_type=OrderType.GTC  # GTC lebih reliable dari FOK
            )
            
            # Buat signed order
            signed_order = self.client.create_market_order(order_args)
            logger.debug(f"Order signed successfully")
            
            # Submit order
            response = self.client.post_order(signed_order, OrderType.GTC)
            
            if response:
                # Cek berbagai format response
                success = response.get("success", False)
                order_id = response.get("orderID") or response.get("order_id") or response.get("id")
                
                if success or order_id:
                    logger.info(f"✅ Order executed: {order_id}")
                    return {
                        "success": True,
                        "orderID": order_id,
                        "response": response
                    }
                else:
                    error_msg = response.get("error", response.get("message", "Unknown error"))
                    logger.error(f"❌ Order failed: {error_msg}")
                    logger.debug(f"Full response: {response}")
                    return None
            else:
                logger.error("❌ Empty response from server")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing market order: {e}")
            # Log detail error untuk debugging
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            self.client.cancel_all()
            logger.info("All orders cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return False
