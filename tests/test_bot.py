"""
Unit tests for Polymarket BTC Bot
"""
import unittest
from datetime import datetime
from config.settings import BotConfig
from src.analyzer import BTCAnalyzer

class TestBTCAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.config = BotConfig()
        self.analyzer = BTCAnalyzer(self.config)
    
    def test_rsi_calculation(self):
        """Test RSI calculation logic"""
        import pandas as pd
        import numpy as np
        
        # Create sample price data
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110])
        rsi = self.analyzer._calculate_rsi(prices, period=5)
        
        # RSI should be between 0 and 100
        self.assertTrue(0 <= rsi.iloc[-1] <= 100)
    
    def test_signal_generation(self):
        """Test signal generation"""
        # Test oversold
        self.assertEqual(self.analyzer.get_signal(25), "BUY_UP")
        
        # Test overbought
        self.assertEqual(self.analyzer.get_signal(75), "BUY_DOWN")
        
        # Test neutral
        self.assertEqual(self.analyzer.get_signal(50), "NEUTRAL")
        
        # Test None
        self.assertEqual(self.analyzer.get_signal(None), "NEUTRAL")

class TestBotConfig(unittest.TestCase):
    
    def test_default_values(self):
        """Test default configuration values"""
        config = BotConfig()
        
        self.assertEqual(config.rsi_period, 14)
        self.assertEqual(config.rsi_oversold, 30)
        self.assertEqual(config.rsi_overbought, 70)
        self.assertEqual(config.price_min, 0.45)
        self.assertEqual(config.price_max, 0.55)

if __name__ == '__main__':
    unittest.main()
