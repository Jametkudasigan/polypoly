#!/usr/bin/env python3
"""
Polymarket BTC Up/Down 5-Minute Automation Bot
Main orchestrator implementing RSI-based momentum strategy
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

import time
import logging
from datetime import datetime
from typing import Optional, Dict

from config.settings import BotConfig
from src.analyzer import BTCAnalyzer
from src.scanner import MarketScanner
from src.executor import TradeExecutor
from src.position_monitor import PositionMonitor
from src.utils import (
    setup_logging, 
    print_scanning_status, 
    print_monitoring_status,
    print_signal,
    print_trade_result
)

logger = logging.getLogger(__name__)

class PolymarketBTCBot:
    """
    Main bot implementing the strategy:
    1. Scanning: Check BTC 5m market + RSI analysis
    2. Entry: Auto-execute based on RSI signal
    3. Monitoring: Monitor position until resolved
    4. Exit: Auto cash-out when market resolved
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.config.validate()
        
        # Initialize components
        self.analyzer = BTCAnalyzer(config)
        self.scanner = MarketScanner(config)
        self.executor = TradeExecutor(config)
        self.monitor = PositionMonitor(config)
        
        # State management
        self.state = "SCANNING"  # SCANNING, MONITORING, EXITING
        self.current_position = None
        self.last_scan_time = None
        
        # Clear screen and show startup
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "="*70)
        print("🚀  POLYMARKET BTC BOT v1.0".center(70))
        print("="*70)
        print(f"  💰 Position Size : ${config.position_size}")
        print(f"  📊 RSI Threshold : <{config.rsi_oversold} (UP) | >{config.rsi_overbought} (DOWN)")
        print(f"  ⏱  Time Window   : {config.min_time_remaining}-{config.max_time_remaining} min")
        print(f"  💵 Price Range   : {config.price_min}-{config.price_max}")
        print("="*70 + "\n")
        
        logger.info("Bot initialized successfully")
    
    def scan_market(self) -> Optional[Dict]:
        """
        Scan market and analyze momentum
        Returns market data if suitable opportunity found
        """
        logger.info("Scanning for BTC 5m markets...")
        
        # Get RSI
        rsi = self.analyzer.get_rsi()
        signal = self.analyzer.get_signal(rsi)
        
        # Get balance
        balance = self.executor.get_balance()
        
        # Find markets
        markets = self.scanner.get_btc_5min_markets()
        
        # Get best market
        best_market = markets[0] if markets else None
        
        # Display clean scanning status
        print_scanning_status(
            balance=balance,
            rsi=rsi or 0,
            market_title=best_market["question"] if best_market else "",
            time_remaining=best_market["time_remaining"] if best_market else 0,
            markets_found=len(markets)
        )
        
        if not best_market:
            logger.info("No suitable BTC 5m markets found")
            return None
        
        # Check if we should trade
        if signal == "NEUTRAL":
            logger.info(f"RSI {rsi:.2f} neutral, skipping trade")
            return None
        
        # Check price threshold
        token_ids = best_market["token_ids"]
        if not token_ids["yes"] or not token_ids["no"]:
            logger.warning("Missing token IDs")
            return None
        
        # Determine which token to buy
        target_token = token_ids["yes"] if signal == "BUY_UP" else token_ids["no"]
        
        # Get current price
        prices = self.executor.get_market_price(target_token)
        best_ask = prices["best_ask"]
        
        # Display signal
        print_signal(signal, best_ask, (self.config.price_min, self.config.price_max))
        
        if not (self.config.price_min <= best_ask <= self.config.price_max):
            logger.info(f"Price {best_ask:.4f} outside threshold range, skipping")
            return None
        
        # All checks passed, return trade data
        return {
            "market": best_market,
            "signal": signal,
            "rsi": rsi,
            "token_id": target_token,
            "price": best_ask,
            "side": "UP" if signal == "BUY_UP" else "DOWN"
        }
    
    def execute_entry(self, trade_data: Dict) -> bool:
        """
        Execute entry trade
        Returns True if successful
        """
        market = trade_data["market"]
        signal = trade_data["signal"]
        token_id = trade_data["token_id"]
        
        logger.info(f"Executing {signal} entry for {market['question']}")
        
        # Place market order
        result = self.executor.place_market_order(
            token_id=token_id,
            side="BUY",
            amount_usdc=self.config.position_size
        )
        
        if result and result.get("success"):
            # Store position data
            self.current_position = {
                "condition_id": market["condition_id"],
                "token_id": token_id,
                "market_question": market["question"],
                "entry_amount": self.config.position_size,
                "side": "YES" if "UP" in signal else "NO",
                "entry_time": datetime.now(),
                "end_time": market["end_time"],
                "order_id": result.get("orderID")
            }
            
            self.state = "MONITORING"
            print_trade_result(True, result.get("orderID"))
            logger.info("Entry executed successfully, switching to MONITORING mode")
            return True
        else:
            print_trade_result(False)
            logger.error("Entry failed")
            return False
    
    def monitor_position(self):
        """Monitor current position"""
        if not self.current_position:
            logger.warning("No position to monitor, returning to SCANNING")
            self.state = "SCANNING"
            return
        
        condition_id = self.current_position["condition_id"]
        
        # Check if market resolved
        if self.monitor.is_market_resolved(condition_id):
            logger.info("Market resolved! Switching to EXITING mode")
            self.state = "EXITING"
            return
        
        # Calculate time remaining
        end_time = self.current_position.get("end_time")
        if end_time:
            time_left = (end_time - datetime.now().astimezone()).total_seconds() / 60
        else:
            time_left = 0
        
        # Display monitoring status
        print_monitoring_status(
            amount=self.current_position["entry_amount"],
            side=f"BUY {self.current_position['side']}",
            market_title=self.current_position["market_question"],
            time_left=max(0, time_left)
        )
        
        # Check if we should force exit (time expired)
        if time_left <= 0:
            logger.info("Market expired, switching to EXITING")
            self.state = "EXITING"
    
    def exit_position(self):
        """Handle position exit"""
        if not self.current_position:
            self.state = "SCANNING"
            return
        
        logger.info("Attempting to exit position...")
        
        winning_outcome = self.monitor.get_winning_outcome(
            self.current_position["condition_id"]
        )
        
        if winning_outcome:
            logger.info(f"Winning outcome: {winning_outcome}")
            if winning_outcome.upper() == self.current_position["side"]:
                logger.info("Position WON!")
            else:
                logger.info("Position LOST")
        
        # Reset position
        self.current_position = None
        self.state = "SCANNING"
        logger.info("Returned to SCANNING mode")
    
    def run(self):
        """Main bot loop"""
        logger.info("Bot started, entering main loop...")
        
        try:
            while True:
                if self.state == "SCANNING":
                    trade_data = self.scan_market()
                    
                    if trade_data:
                        success = self.execute_entry(trade_data)
                        if not success:
                            logger.warning("Entry failed, will retry on next scan")
                    
                    # Scan every 30 seconds
                    time.sleep(30)
                    
                elif self.state == "MONITORING":
                    self.monitor_position()
                    # Check every 10 seconds
                    time.sleep(10)
                    
                elif self.state == "EXITING":
                    self.exit_position()
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            # Attempt to recover
            time.sleep(60)
            self.run()  # Restart

def main():
    """Entry point"""
    # Setup logging
    setup_logging()
    
    # Load configuration
    config = BotConfig()
    
    try:
        # Create and run bot
        bot = PolymarketBTCBot(config)
        bot.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print("\n⚠️  Please check your .env configuration")
        print("   Copy config/.env.example to config/.env and fill in your credentials")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
