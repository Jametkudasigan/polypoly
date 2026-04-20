"""
BTC Momentum Analyzer using Yahoo Finance RSI
"""
import logging
import yfinance as yf
import pandas as pd
from typing import Optional
from config.settings import BotConfig

logger = logging.getLogger(__name__)

class BTCAnalyzer:
    """Analyze BTC momentum using RSI from Yahoo Finance"""
    
    def __init__(self, config: BotConfig):
        self.config = config
    
    def get_rsi(self, symbol: str = "BTC-USD", interval: str = "5m") -> Optional[float]:
        """
        Get RSI for BTC from Yahoo Finance
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval=interval)
            
            if df.empty or len(df) < self.config.rsi_period + 1:
                logger.warning(f"Insufficient data: {len(df)} candles")
                return None
            
            rsi = self._calculate_rsi(df['Close'], self.config.rsi_period)
            current_rsi = rsi.iloc[-1]
            
            return float(current_rsi)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI using Wilder's smoothing method"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(com=period-1, adjust=False).mean()
        avg_loss = loss.ewm(com=period-1, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_signal(self, rsi: Optional[float]) -> str:
        """Determine trading signal based on RSI"""
        if rsi is None:
            return "NEUTRAL"
        
        if rsi < self.config.rsi_oversold:
            return "BUY_UP"
        elif rsi > self.config.rsi_overbought:
            return "BUY_DOWN"
        else:
            return "NEUTRAL"
