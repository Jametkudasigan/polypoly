# Update utils.py - border hanya di pinggir kiri kanan
utils_py = '''"""
Utility functions for Polymarket BTC Bot - Terminal UI Style (Side Borders Only)
"""
import logging
import sys
import os
import shutil
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Suppress noisy third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Box characters - hanya vertical borders
V = "║"

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
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))
    console_handler.addFilter(lambda record: not record.name.startswith(('httpx', 'httpcore', 'urllib3')))
    logger.addHandler(console_handler)
    
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

def side_line(text="", width=68, color=Fore.GREEN, label_color=Fore.CYAN):
    """Create line with side borders only"""
    # Format: ║  Label : Value  ║
    return f"{Fore.GREEN}{V}{Style.RESET_ALL}  {color}{text.ljust(width)}{Style.RESET_ALL}  {Fore.GREEN}{V}{Style.RESET_ALL}"

def side_border(text="", width=70, color=Fore.GREEN, align="center"):
    """Create top/bottom border line"""
    if align == "center":
        text = text.center(width - 4)
    elif align == "left":
        text = text.ljust(width - 4)
    else:
        text = text.rjust(width - 4)
    return f"{color}{V}{Style.RESET_ALL}  {text}  {color}{V}{Style.RESET_ALL}"

def format_rsi_status(rsi, oversold, overbought):
    """Format RSI with color and status"""
    if rsi < oversold:
        return Fore.RED, "OVERSOLD ↓", "BUY UP", Fore.RED
    elif rsi > overbought:
        return Fore.GREEN, "OVERBOUGHT ↑", "BUY DOWN", Fore.GREEN
    else:
        return Fore.YELLOW, "NEUTRAL ↔", "SKIP", Fore.YELLOW

def format_time_status(time_remaining, min_time, max_time):
    """Format time with status"""
    if min_time <= time_remaining <= max_time:
        return Fore.GREEN, "✅ SWEET SPOT"
    elif time_remaining < min_time:
        return Fore.RED, "❌ TOO SHORT"
    else:
        return Fore.YELLOW, "⏳ WAITING"

def print_scanning_ui(scan_num, balance, rsi, market_data, config, markets_found=0, yes_price=0, no_price=0):
    """Print scanning UI dengan border hanya di pinggir"""
    clear_screen()
    w = 68
    
    # Header border
    print(side_border(f"🔍 SCANNING MARKET #{scan_num}", w, Fore.CYAN + Style.BRIGHT))
    print()
    
    # WALLET Section
    print(side_border("💰 WALLET", w, Fore.CYAN, "left"))
    print(side_line(f"USDC Balance : ${balance:,.2f}", w, Fore.GREEN))
    print()
    
    # MOMENTUM Section
    print(side_border("📊 MOMENTUM (Yahoo Finance)", w, Fore.CYAN, "left"))
    
    rsi_color, rsi_status, signal, action_color = format_rsi_status(rsi, config.rsi_oversold, config.rsi_overbought)
    print(side_line(f"BTC RSI (5m) : {rsi_color}{rsi:.2f}{Style.RESET_ALL}", w, Fore.GREEN))
    print(side_line(f"Status       : {rsi_color}{rsi_status}{Style.RESET_ALL}", w, Fore.GREEN))
    print()
    
    # MARKET Section
    if market_data:
        print(side_border("🎯 MARKET", w, Fore.CYAN, "left"))
        
        question = market_data.get("question", "Unknown")
        condition_id = market_data.get("condition_id", "")[:30] + "..."
        
        print(side_line(f"Question   : {Fore.MAGENTA}{question}{Style.RESET_ALL}", w, Fore.GREEN))
        print(side_line(f"Condition  : {Fore.CYAN}{condition_id}{Style.RESET_ALL}", w, Fore.GREEN))
        
        if yes_price and no_price:
            spread = abs(yes_price - no_price)
            print(side_line(f"YES Price  : $ {yes_price:.3f}", w, Fore.GREEN))
            print(side_line(f"NO Price   : $ {no_price:.3f}", w, Fore.GREEN))
            print(side_line(f"Spread     : $ {spread:.3f}", w, Fore.GREEN))
        
        time_remaining = market_data.get("time_remaining", 0)
        time_color, time_status = format_time_status(time_remaining, config.min_time_remaining, config.max_time_remaining)
        
        print(side_line(f"Time Left  : {time_color}{time_remaining:.1f}m {time_status}{Style.RESET_ALL}", w, Fore.GREEN))
        print(side_line(f"Status     : {Fore.GREEN}ACTIVE{Style.RESET_ALL}", w, Fore.GREEN))
        print()
        
        # SIGNAL ANALYSIS Section
        print(side_border("🎯 SIGNAL ANALYSIS", w, Fore.CYAN, "left"))
        
        confidence = "HIGH" if rsi < 20 or rsi > 80 else ("MEDIUM" if rsi < 30 or rsi > 70 else "NONE")
        
        print(side_line(f"Action     : {action_color}{signal}{Style.RESET_ALL}", w, Fore.GREEN))
        print(side_line(f"Confidence : {Fore.YELLOW}{confidence}{Style.RESET_ALL}", w, Fore.GREEN))
        print(side_line(f"Position   : {action_color}{signal}{Style.RESET_ALL}", w, Fore.GREEN))
        print()
        
        # Bottom note
        print(f"{Fore.CYAN}• RSI {rsi:.2f} {rsi_status.lower().split()[0]}{Style.RESET_ALL}")
    else:
        print(side_border("🎯 MARKET", w, Fore.RED, "left"))
        print(side_line(f"Status     : {Fore.RED}NO MARKET FOUND{Style.RESET_ALL}", w, Fore.RED))
        print(side_line(f"Markets    : {Fore.YELLOW}{markets_found} found{Style.RESET_ALL}", w, Fore.RED))
        print()

def print_monitoring_ui(position, time_left, pnl=0):
    """Print monitoring UI dengan border hanya di pinggir"""
    clear_screen()
    w = 68
    
    # Header
    print(side_border("📈 MONITORING POSITION", w, Fore.GREEN + Style.BRIGHT))
    print()
    
    # Position Details
    print(side_border("💰 POSITION", w, Fore.CYAN, "left"))
    print(side_line(f"Entry Amount : ${position.get('entry_amount', 0):.2f} USDC", w, Fore.GREEN))
    print(side_line(f"Side         : {Fore.BLUE}{position.get('side', 'UNKNOWN')}{Style.RESET_ALL}", w, Fore.GREEN))
    print(side_line(f"Market       : {Fore.MAGENTA}{position.get('market_question', 'Unknown')[:50]}{Style.RESET_ALL}", w, Fore.GREEN))
    print(side_line(f"Time Left    : {Fore.CYAN}{time_left:.1f} minutes{Style.RESET_ALL}", w, Fore.GREEN))
    
    if pnl != 0:
        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
        print(side_line(f"P&L          : {pnl_color}{pnl:+.2f} USDC{Style.RESET_ALL}", w, Fore.GREEN))
    
    print()

def print_trade_signal(signal, price, threshold):
    """Print trade signal box dengan border pinggir"""
    w = 68
    
    if signal == "BUY_UP":
        print(side_border("🟢 SIGNAL: BUY UP (RSI Oversold)", w, Fore.GREEN + Style.BRIGHT))
    elif signal == "BUY_DOWN":
        print(side_border("🔴 SIGNAL: BUY DOWN (RSI Overbought)", w, Fore.RED + Style.BRIGHT))
    else:
        print(side_border("⚪ SIGNAL: NEUTRAL (No Trade)", w, Fore.YELLOW))
    
    print(side_line(f"Price: {price:.4f} | Threshold: {threshold[0]}-{threshold[1]}", w, Fore.CYAN))
    print()

def format_timestamp(dt: datetime) -> str:
    """Format datetime to timestamp string"""
    return dt.strftime("%Y%m%d%H%M")

def parse_end_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime"""
    if date_str:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return datetime.now()
'''

with open(f"{base_path}/src/utils.py", "w") as f:
    f.write(utils_py)

print("✅ utils.py updated - border hanya di pinggir kiri kanan")
