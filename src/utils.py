"""
Utility functions for Polymarket BTC Bot
"""
import logging
import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Suppress noisy third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

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
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler - only show bot messages, not HTTP logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    console_handler.addFilter(lambda record: not record.name.startswith(('httpx', 'httpcore', 'urllib3')))
    logger.addHandler(console_handler)
    
    # File handler - log everything including HTTP
    log_file = os.path.join(log_dir, 'bot.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str, color: str = Fore.CYAN):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"{color}{Style.BRIGHT}{title.center(70)}{Style.RESET_ALL}")
    print("="*70)

def print_footer():
    """Print footer separator"""
    print("="*70 + "\n")

def print_scanning_status(balance: float, rsi: float, market_title: str, time_remaining: float, markets_found: int = 0):
    """Print clean scanning status"""
    clear_screen()
    print_header("🔍  SCANNING MARKET", Fore.CYAN)
    
    print(f"  💰  Balance (Proxy) : {Fore.YELLOW}{balance:.2f} USDC{Style.RESET_ALL}")
    
    rsi_color = Fore.RED if rsi < 30 else (Fore.GREEN if rsi > 70 else Fore.WHITE)
    rsi_status = "OVERSOLD" if rsi < 30 else ("OVERBOUGHT" if rsi > 70 else "NEUTRAL")
    print(f"  📊  BTC RSI (5m)    : {rsi_color}{rsi:.2f}{Style.RESET_ALL} ({rsi_status})")
    
    if market_title:
        print(f"  🎯  Market          : {Fore.MAGENTA}{market_title}{Style.RESET_ALL}")
        print(f"  ⏰  Time Remaining  : {Fore.CYAN}{time_remaining:.1f} minutes{Style.RESET_ALL}")
    else:
        print(f"  🎯  Market          : {Fore.RED}No suitable market found{Style.RESET_ALL}")
    
    if markets_found > 0:
        print(f"  📈  Markets Found   : {Fore.GREEN}{markets_found}{Style.RESET_ALL}")
    
    print_footer()

def print_monitoring_status(amount: float, side: str, market_title: str, time_left: float, pnl: float = 0):
    """Print clean monitoring status"""
    clear_screen()
    print_header("📈  MONITORING POSITION", Fore.GREEN)
    
    print(f"  💰  Entry Amount    : {Fore.YELLOW}{amount:.2f} USDC{Style.RESET_ALL}")
    print(f"  🎲  Side            : {Fore.BLUE}{side}{Style.RESET_ALL}")
    print(f"  🎯  Market          : {Fore.MAGENTA}{market_title}{Style.RESET_ALL}")
    print(f"  ⏰  Time Left       : {Fore.CYAN}{time_left:.1f} minutes{Style.RESET_ALL}")
    
    if pnl != 0:
        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
        print(f"  📊  P&L             : {pnl_color}{pnl:+.2f} USDC{Style.RESET_ALL}")
    
    print_footer()

def print_signal(signal: str, price: float, threshold: tuple):
    """Print trading signal info"""
    if signal == "BUY_UP":
        print(f"\n  🟢  SIGNAL: {Fore.GREEN}BUY UP{Style.RESET_ALL} (RSI Oversold)")
    elif signal == "BUY_DOWN":
        print(f"\n  🔴  SIGNAL: {Fore.RED}BUY DOWN{Style.RESET_ALL} (RSI Overbought)")
    else:
        print(f"\n  ⚪  SIGNAL: {Fore.WHITE}NEUTRAL{Style.RESET_ALL} (No Trade)")
    
    print(f"  💵  Price: {price:.4f} | Threshold: {threshold[0]}-{threshold[1]}")

def print_trade_result(success: bool, order_id: str = None):
    """Print trade execution result"""
    if success:
        print(f"\n  ✅  {Fore.GREEN}Trade Executed Successfully{Style.RESET_ALL}")
        if order_id:
            print(f"  📝  Order ID: {order_id}")
    else:
        print(f"\n  ❌  {Fore.RED}Trade Execution Failed{Style.RESET_ALL}")

def format_timestamp(dt: datetime) -> str:
    """Format datetime to timestamp string"""
    return dt.strftime("%Y%m%d%H%M")

def parse_end_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime"""
    if date_str:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return datetime.now()
