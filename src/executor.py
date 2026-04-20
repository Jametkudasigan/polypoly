"""
Trade Executor for Polymarket using py-clob-client
"""
import logging
from typing import Optional, Dict
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    OrderArgs, MarketOrderArgs, OrderType, 
    BalanceAllowanceParams, AssetType, ApiCreds
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
        """Initialize CLOB client dengan proper API credential derivation"""
        try:
            # Step 1: Create client untuk derive API key
            temp_client = ClobClient(
                host=self.config.clob_host,
                key=self.config.private_key,
                chain_id=self.config.chain_id,
                signature_type=self.config.signature_type,
                funder=self.config.funder_address
            )
            
            # Step 2: Derive API credentials
            logger.info("Deriving API credentials...")
            creds = temp_client.create_or_derive_api_creds()
            
            logger.info(f"API Key derived: {creds.api_key[:20]}...")
            
            # Step 3: Re-initialize client dengan credentials
            client = ClobClient(
                host=self.config.clob_host,
                key=self.config.private_key,
                chain_id=self.config.chain_id,
                signature_type=self.config.signature_type,
                funder=self.config.funder_address,
                creds=ApiCreds(
                    api_key=creds.api_key,
                    api_secret=creds.api_secret,
                    api_passphrase=creds.api_passphrase
                )
            )
            
            logger.info(f"CLOB Client connected (Type: {self.config.signature_type})")
            logger.info(f"Funder: {self.config.funder_address[:25]}...")
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
        Place a market order using FOK (Fill or Kill)
        
        FOK = Fill entirely immediately or cancel (all-or-nothing)
        """
        try:
            logger.info(f"Placing MARKET {side} order: ${amount_usdc} (FOK)")
            logger.debug(f"Token: {token_id[:40]}...")
            
            # Gunakan FOK (Fill or Kill) untuk all-or-nothing execution
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount_usdc,
                side=BUY if side == "BUY" else SELL,
                order_type=OrderType.FOK  # Fill or Kill
            )
            
            # Buat signed order
            signed_order = self.client.create_market_order(order_args)
            logger.debug("Order signed successfully")
            
            # Submit order dengan FOK
            response = self.client.post_order(signed_order, OrderType.FOK)
            
            if response:
                # Cek response format
                success = response.get("success", False)
                order_id = response.get("orderID") or response.get("order_id") or response.get("id")
                status = response.get("status", "UNKNOWN")
                
                if success or order_id:
                    logger.info(f"✅ Order executed: {order_id} | Status: {status}")
                    return {
                        "success": True,
                        "orderID": order_id,
                        "status": status,
                        "response": response
                    }
                else:
                    error_msg = response.get("error", response.get("message", "Unknown error"))
                    logger.error(f"❌ Order rejected: {error_msg}")
                    logger.debug(f"Full response: {response}")
                    return None
            else:
                logger.error("❌ Empty response from server")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing market order: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            result = self.client.cancel_all()
            logger.info(f"Orders cancelled: {result}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return False
