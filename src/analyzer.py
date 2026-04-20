"""
BTC Momentum Analyzer using RSI + EMA Strategy
"""
import logging
import yfinance as yf
import pandas as pd
from typing import Optional, Tuple
from config.settings import BotConfig

logger = logging.getLogger(__name__)


class BTCAnalyzer:
    """Analyze BTC momentum using RSI + EMA strategy"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.ema_period = 50
    
    def get_market_data(self, symbol: str = "BTC-USD", interval: str = "5m") -> Optional[pd.DataFrame]:
        """Fetch market data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval=interval)
            
            if df.empty or len(df) < self.ema_period + 5:
                logger.warning(f"Insufficient data: {len(df)} candles")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
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
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def _is_green_candle(self, df: pd.DataFrame) -> bool:
        """Check if last candle is green (bullish)"""
        return df['Close'].iloc[-1] > df['Open'].iloc[-1]
    
    def _is_red_candle(self, df: pd.DataFrame) -> bool:
        """Check if last candle is red (bearish)"""
        return df['Close'].iloc[-1] < df['Open'].iloc[-1]
    
    def analyze(self, symbol: str = "BTC-USD", interval: str = "5m") -> Tuple[Optional[float], Optional[float], str]:
        """
        Analyze BTC momentum using RSI + EMA strategy
        
        Returns:
            Tuple of (current_rsi, current_price, signal)
        """
        df = self.get_market_data(symbol, interval)
        
        if df is None:
            return None, None, "NEUTRAL"
        
        # Calculate indicators
        rsi = self._calculate_rsi(df['Close'], self.config.rsi_period)
        ema50 = self._calculate_ema(df['Close'], self.ema_period)
        
        current_price = df['Close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        current_ema = ema50.iloc[-1]
        
        signal = self._get_signal(
            price=current_price,
            ema=current_ema,
            current_rsi=current_rsi,
            prev_rsi=prev_rsi,
            is_green=self._is_green_candle(df),
            is_red=self._is_red_candle(df)
        )
        
        logger.info(
            f"Analysis: Price={current_price:.2f}, EMA50={current_ema:.2f}, "
            f"RSI={current_rsi:.1f}, Prev RSI={prev_rsi:.1f}, Signal={signal}"
        )
        
        return float(current_rsi), float(current_price), signal
    
    def _get_signal(
        self,
        price: float,
        ema: float,
        current_rsi: float,
        prev_rsi: float,
        is_green: bool,
        is_red: bool
    ) -> str:
        """
        Determine trading signal based on RSI + EMA strategy
        
        BUY_UP conditions:
        - Price above EMA 50 (uptrend)
        - Previous RSI was below 30 (oversold)
        - Current RSI rising
        - Last candle is green
        
        BUY_DOWN conditions:
        - Price below EMA 50 (downtrend)
        - Previous RSI was above 70 (overbought)
        - Current RSI falling
        - Last candle is red
        """
        rsi_rising = current_rsi > prev_rsi
        rsi_falling = current_rsi < prev_rsi
        
        # BUY UP: Oversold bounce in uptrend
        if (price > ema and 
            prev_rsi < self.config.rsi_oversold and 
            rsi_rising and 
            is_green):
            return "BUY_UP"
        
        # BUY DOWN: Overbought rejection in downtrend
        if (price < ema and 
            prev_rsi > self.config.rsi_overbought and 
            rsi_falling and 
            is_red):
            return "BUY_DOWN"
        
        return "NEUTRAL"
    
    def should_entry(self, poly_price: float, minutes_left: int) -> Tuple[bool, str]:
        """
        Check Polymarket filters before entry
        
        Args:
            poly_price: Current Polymarket price (0-1)
            minutes_left: Minutes remaining in market
            
        Returns:
            Tuple of (should_enter, reason)
        """
        # Price filter: only enter at 0.45-0.55
        if poly_price < 0.45 or poly_price > 0.55:
            return False, f"Price {poly_price:.2f} outside 0.45-0.55 range"
        
        # Time filter
        if minutes_left < 3:
            return False, f"Only {minutes_left}min left - won't fill in time"
        
        if minutes_left > 10:
            return False, f"{minutes_left}min left - wait for better price"
        
        # Sweet spot: 3-10 minutes
        return True, f"Good entry window: {minutes_left}min left, price {poly_price:.2f}"
    
    # Backward compatibility
    def get_rsi(self, symbol: str = "BTC-USD", interval: str = "5m") -> Optional[float]:
        """Legacy method - returns just RSI"""
        rsi, _, _ = self.analyze(symbol, interval)
        return rsi
    
    def get_signal(self, rsi: Optional[float]) -> str:
        """Legacy method - use analyze() instead for full strategy"""
        if rsi is None:
            return "NEUTRAL"
        
        # Simple RSI-only signal (legacy behavior)
        if rsi < self.config.rsi_oversold:
            return "BUY_UP"
        elif rsi > self.config.rsi_overbought:
            return "BUY_DOWN"
        return "NEUTRAL"
