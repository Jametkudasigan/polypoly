"""
BTC Momentum Analyzer using Yahoo Finance RSI
"""
import logging
import yfinance as yf
import pandas as pd
import numpy as np
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
        
        Args:
            symbol: Yahoo Finance symbol (default: BTC-USD)
            interval: Candle interval (default: 5m)
        
        Returns:
            Current RSI value or None if error
        """
        try:
            logger.info(f"Fetching BTC data from Yahoo Finance ({interval})...")
            
            # Download BTC data
            ticker = yf.Ticker(symbol)
            
            # Get 5-minute data for last 24 hours
            df = ticker.history(period="1d", interval=interval)
            
            if df.empty:
                logger.warning("No data received from Yahoo Finance")
                return None
            
            if len(df) < self.config.rsi_period + 1:
                logger.warning(f"Insufficient data. Got {len(df)} candles, need {self.config.rsi_period + 1}")
                return None
            
            # Calculate RSI
            rsi = self._calculate_rsi(df['Close'], self.config.rsi_period)
            current_rsi = rsi.iloc[-1]
            
            logger.info(f"BTC {interval} RSI: {current_rsi:.2f}")
            return float(current_rsi)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI using Wilder's smoothing method
        
        Args:
            prices: Price series
            period: RSI period
        
        Returns:
            RSI series
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss using Wilder's smoothing
        avg_gain = gain.ewm(com=period-1, adjust=False).mean()
        avg_loss = loss.ewm(com=period-1, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_signal(self, rsi: Optional[float]) -> str:
        """
        Determine trading signal based on RSI
        
        Args:
            rsi: Current RSI value
        
        Returns:
            Signal: "BUY_UP", "BUY_DOWN", or "NEUTRAL"
        """
        if rsi is None:
            return "NEUTRAL"
        
        if rsi < self.config.rsi_oversold:
            logger.info(f"RSI {rsi:.2f} < {self.config.rsi_oversold} → BUY UP (oversold)")
            return "BUY_UP"
        elif rsi > self.config.rsi_overbought:
            logger.info(f"RSI {rsi:.2f} > {self.config.rsi_overbought} → BUY DOWN (overbought)")
            return "BUY_DOWN"
        else:
            logger.info(f"RSI {rsi:.2f} neutral → SKIP")
            return "NEUTRAL"
    
    def get_signal_strength(self, rsi: float) -> str:
        """
        Get signal strength for position sizing
        
        Args:
            rsi: Current RSI value
        
        Returns:
            Strength: "STRONG", "MODERATE", or "WEAK"
        """
        if rsi < 20 or rsi > 80:
            return "STRONG"
        elif rsi < 30 or rsi > 70:
            return "MODERATE"
        return "WEAK"
