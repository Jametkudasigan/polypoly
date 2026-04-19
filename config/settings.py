"""
Configuration settings for Polymarket BTC Bot
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class BotConfig:
    """Bot configuration"""
    
    # Wallet Configuration
    private_key: str = os.getenv("POLYMARKET_PRIVATE_KEY", "")
    funder_address: str = os.getenv("POLYMARKET_FUNDER_ADDRESS", "")
    signature_type: int = int(os.getenv("SIGNATURE_TYPE", "1"))
    
    # Trading Parameters
    position_size: float = float(os.getenv("POSITION_SIZE", "1.0"))
    rsi_period: int = int(os.getenv("RSI_PERIOD", "14"))
    rsi_oversold: int = int(os.getenv("RSI_OVERSOLD", "30"))
    rsi_overbought: int = int(os.getenv("RSI_OVERBOUGHT", "70"))
    price_min: float = float(os.getenv("PRICE_MIN", "0.45"))
    price_max: float = float(os.getenv("PRICE_MAX", "0.55"))
    
    # Time Filters (minutes)
    min_time_remaining: int = int(os.getenv("MIN_TIME_REMAINING", "2"))
    max_time_remaining: int = int(os.getenv("MAX_TIME_REMAINING", "10"))
    
    # API Configuration
    clob_host: str = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    gamma_host: str = os.getenv("GAMMA_HOST", "https://gamma-api.polymarket.com")
    data_host: str = os.getenv("DATA_HOST", "https://data-api.polymarket.com")
    chain_id: int = int(os.getenv("CHAIN_ID", "137"))
    
    # Builder API (Optional - untuk relayer gasless)
    builder_api_key: str = os.getenv("BUILDER_API_KEY", "")
    builder_secret: str = os.getenv("BUILDER_SECRET", "")
    builder_passphrase: str = os.getenv("BUILDER_PASSPHRASE", "")
    
    # Market Filters
    market_keywords: list = None
    
    def __post_init__(self):
        if self.market_keywords is None:
            self.market_keywords = ["btc", "bitcoin", "up", "down", "5m", "5 minute"]
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.private_key:
            raise ValueError("POLYMARKET_PRIVATE_KEY is required")
        if not self.funder_address:
            raise ValueError("POLYMARKET_FUNDER_ADDRESS is required")
        return True
