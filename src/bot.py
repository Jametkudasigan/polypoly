#!/usr/bin/env python3
"""
Polymarket BTC Up/Down 5-Minute Automation Bot
"""
import sys
import os
from pathlib import Path

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
    print_scanning_ui, 
    print_monitoring_ui,
    print_trade_signal,
    format_rsi_status,
    format_time_status,
    clear_screen
)

logger = logging.getLogger(__name__)

class PolymarketBTCBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.config.validate()
        
        self.analyzer = BTCAnalyzer(config)
        self.scanner = MarketScanner(config)
        self.executor = TradeExecutor(config)
        self.monitor = PositionMonitor(config)
        
        self.state = "SCANNING"
        self.current_position = None
        self.scan_count = 0
        
        # Startup screen
        clear_screen()
        print(f"\n{'='*70}")
        print("🚀  POLYMARKET BTC BOT v1.0".center(70))
        print(f"{'='*70}")
        print(f"  💰 Position Size : ${config.position_size}")
        print(f"  📊 RSI Threshold : <{config.rsi_oversold} (UP) | >{config.rsi_overbought} (DOWN)")
        print(f"  ⏱  Time Window   : {config.min_time_remaining}-{config.max_time_remaining} min")
        print(f"  💵 Price Range   : {config.price_min}-{config.price_max}")
        print(f"{'='*70}\n")
        
        logger.info("Bot initialized")
    
    def scan_market(self) -> Optional[Dict]:
        """Scan market and analyze momentum"""
        self.scan_count += 1
        logger.info("Scanning for BTC 5m markets...")
        
        # Get RSI
        rsi = self.analyzer.get_rsi()
        signal = self.analyzer.get_signal(rsi)
        
        # Get balance
        balance = self.executor.get_balance()
        
        # Find markets
        markets = self.scanner.get_btc_5min_markets()
        best_market = markets[0] if markets else None
        
        # Get prices if market found
        yes_price = 0
        no_price = 0
        if best_market:
            token_ids = best_market["token_ids"]
            if token_ids["yes"]:
                prices = self.executor.get_market_price(token_ids["yes"])
                yes_price = prices["best_ask"]
            if token_ids["no"]:
                prices = self.executor.get_market_price(token_ids["no"])
                no_price = prices["best_ask"]
        
        # Display UI
        print_scanning_ui(
            scan_num=self.scan_count,
            balance=balance,
            rsi=rsi or 0,
            market_data=best_market,
            config=self.config,
            markets_found=len(markets),
            yes_price=yes_price,
            no_price=no_price
        )
        
        if not best_market:
            logger.info("No suitable BTC 5m markets found")
            return None
        
        if signal == "NEUTRAL":
            logger.info(f"RSI {rsi:.2f} neutral, skipping")
            return None
        
        # Check price threshold
        token_ids = best_market["token_ids"]
        if not token_ids["yes"] or not token_ids["no"]:
            logger.warning("Missing token IDs")
            return None
        
        target_token = token_ids["yes"] if signal == "BUY_UP" else token_ids["no"]
        prices = self.executor.get_market_price(target_token)
        best_ask = prices["best_ask"]
        
        if not (self.config.price_min <= best_ask <= self.config.price_max):
            logger.info(f"Price {best_ask:.4f} outside threshold")
            return None
        
        return {
            "market": best_market,
            "signal": signal,
            "rsi": rsi,
            "token_id": target_token,
            "price": best_ask,
            "side": "UP" if signal == "BUY_UP" else "DOWN"
        }
    
    def execute_entry(self, trade_data: Dict) -> bool:
        """Execute entry trade"""
        market = trade_data["market"]
        signal = trade_data["signal"]
        token_id = trade_data["token_id"]
        
        logger.info(f"Executing {signal} entry")
        
        result = self.executor.place_market_order(
            token_id=token_id,
            side="BUY",
            amount_usdc=self.config.position_size
        )
        
        if result and result.get("success"):
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
            logger.info("Entry executed, monitoring...")
            return True
        else:
            logger.error("Entry failed")
            return False
    
    def monitor_position(self):
        """Monitor current position"""
        if not self.current_position:
            self.state = "SCANNING"
            return
        
        condition_id = self.current_position["condition_id"]
        
        if self.monitor.is_market_resolved(condition_id):
            logger.info("Market resolved!")
            self.state = "EXITING"
            return
        
        end_time = self.current_position.get("end_time")
        if end_time:
            time_left = (end_time - datetime.now().astimezone()).total_seconds() / 60
        else:
            time_left = 0
        
        print_monitoring_ui(
            position=self.current_position,
            time_left=max(0, time_left)
        )
        
        if time_left <= 0:
            logger.info("Market expired")
            self.state = "EXITING"
    
    def exit_position(self):
        """Handle position exit"""
        if not self.current_position:
            self.state = "SCANNING"
            return
        
        winning_outcome = self.monitor.get_winning_outcome(
            self.current_position["condition_id"]
        )
        
        if winning_outcome:
            won = winning_outcome.upper() == self.current_position["side"]
            logger.info(f"Position {'WON' if won else 'LOST'}")
        
        self.current_position = None
        self.state = "SCANNING"
        logger.info("Back to scanning")
    
    def run(self):
        """Main bot loop"""
        logger.info("Bot started")
        
        try:
            while True:
                if self.state == "SCANNING":
                    trade_data = self.scan_market()
                    
                    if trade_data:
                        success = self.execute_entry(trade_data)
                        if not success:
                            logger.warning("Entry failed, retry next scan")
                    
                    time.sleep(30)
                    
                elif self.state == "MONITORING":
                    self.monitor_position()
                    time.sleep(10)
                    
                elif self.state == "EXITING":
                    self.exit_position()
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            time.sleep(60)
            self.run()

def main():
    setup_logging()
    config = BotConfig()
    
    try:
        bot = PolymarketBTCBot(config)
        bot.run()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        print("\n⚠️  Check your .env configuration")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
