"""
Utility functions for Polymarket BTC Bot
"""
import logging
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging():
    """Setup colored logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/bot.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

def print_scanning_header(balance: float, rsi: float, market_title: str, time_remaining: float):
    """Print scanning status header"""
    print("\n" + "="*60)
    print(Fore.CYAN + "🔍 SCANNING MARKET" + Style.RESET_ALL)
    print("="*60)
    print(f"💰 Balance (Proxy): {Fore.YELLOW}{balance:.2f} USDC{Style.RESET_ALL}")
    
    rsi_color = Fore.RED if rsi < 30 else (Fore.GREEN if rsi > 70 else Fore.WHITE)
    print(f"📊 BTC RSI (5m): {rsi_color}{rsi:.2f}{Style.RESET_ALL}")
    
    if market_title:
        print(f"🎯 Market: {Fore.MAGENTA}{market_title}{Style.RESET_ALL}")
        print(f"⏰ Time Remaining: {Fore.CYAN}{time_remaining:.1f} minutes{Style.RESET_ALL}")
    else:
        print(f"🎯 Market: {Fore.RED}No suitable market found{Style.RESET_ALL}")
    print("="*60)

def print_monitoring_header(amount: float, side: str, market_title: str, time_left: float):
    """Print monitoring status header"""
    print("\n" + "="*60)
    print(Fore.GREEN + "📈 MONITORING POSITION" + Style.RESET_ALL)
    print("="*60)
    print(f"💰 Entry Amount: {Fore.YELLOW}{amount:.2f} USDC{Style.RESET_ALL}")
    print(f"🎲 Side: {Fore.BLUE}{side}{Style.RESET_ALL}")
    print(f"🎯 Market: {Fore.MAGENTA}{market_title}{Style.RESET_ALL}")
    print(f"⏰ Time Left: {Fore.CYAN}{time_left:.1f} minutes{Style.RESET_ALL}")
    print("="*60)

def format_timestamp(dt: datetime) -> str:
    """Format datetime to timestamp string"""
    return dt.strftime("%Y%m%d%H%M")

def parse_end_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime"""
    if date_str:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return datetime.now()
