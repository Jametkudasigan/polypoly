"""
Utility functions for Polymarket BTC Bot - Terminal UI Style
"""
import logging
import sys
import os
import shutil
from datetime import datetime
from colorama import init, Fore, Style, Back

# Initialize colorama
init(autoreset=True)

# Suppress noisy third-party logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Box drawing characters (Unicode)
H = "═"
V = "║"
TL = "╔"
TR = "╗"
BL = "╚"
BR = "╝"
L = "╠"
R = "╣"
T = "╦"
B = "╩"

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

def get_terminal_width():
    """Get terminal width, default to 70"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 70

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def box_line(text="", width=68, align="left", color=Fore.GREEN):
    """Create a box line with text"""
    if align == "center":
        text = text.center(width)
    elif align == "right":
        text = text.rjust(width)
    else:
        text = text.ljust(width)
    return f"{Fore.GREEN}{V}{Style.RESET_ALL} {color}{text}{Style.RESET_ALL} {Fore.GREEN}{V}{Style.RESET_ALL}"

def box_border(top=True, width=70, color=Fore.GREEN):
    """Print box border"""
    char = TL if top else BL
    char2 = TR if top else BR
    line = H * (width - 2)
    print(f"{color}{char}{line}{char2}{Style.RESET_ALL}")

def box_separator(width=70):
    """Print separator line inside box"""
    line = H * (width - 2)
    print(f"{Fore.GREEN}{L}{line}{R}{Style.RESET_ALL}")

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
    """Print beautiful scanning UI like screenshot"""
    clear_screen()
    w = 70
    
    # Header
    box_border(True, w)
    print(box_line(f"🔍 SCANNING MARKET #{scan_num}", w, "center", Fore.CYAN + Style.BRIGHT))
    box_border(False, w)
    print()
    
    # WALLET Section
    box_border(True, w)
    print(box_line("💰 WALLET", w, "left", Fore.CYAN))
    box_separator(w)
    print(box_line(f"USDC Balance : ${balance:,.2f}", w, "left", Fore.GREEN))
    box_border(False, w)
    print()
    
    # MOMENTUM Section
    box_border(True, w)
    print(box_line("📊 MOMENTUM (Yahoo Finance)", w, "left", Fore.CYAN))
    box_separator(w)
    
    rsi_color, rsi_status, signal, action_color = format_rsi_status(rsi, config.rsi_oversold, config.rsi_overbought)
    print(box_line(f"BTC RSI (5m) : {rsi_color}{rsi:.2f}{Style.RESET_ALL}", w, "left", Fore.GREEN))
    print(box_line(f"Status       : {rsi_color}{rsi_status}{Style.RESET_ALL}", w, "left", Fore.GREEN))
    box_border(False, w)
    print()
    
    # MARKET Section
    if market_data:
        box_border(True, w)
        print(box_line("🎯 MARKET", w, "left", Fore.CYAN))
        box_separator(w)
        
        question = market_data.get("question", "Unknown")
        condition_id = market_data.get("condition_id", "")[:25] + "..."
        
        print(box_line(f"Question   : {Fore.MAGENTA}{question}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        print(box_line(f"Condition  : {Fore.CYAN}{condition_id}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        box_separator(w)
        
        if yes_price and no_price:
            spread = abs(yes_price - no_price)
            print(box_line(f"YES Price  : $ {yes_price:.3f}", w, "left", Fore.GREEN))
            print(box_line(f"NO Price   : $ {no_price:.3f}", w, "left", Fore.GREEN))
            print(box_line(f"Spread     : $ {spread:.3f}", w, "left", Fore.GREEN))
            box_separator(w)
        
        time_remaining = market_data.get("time_remaining", 0)
        time_color, time_status = format_time_status(time_remaining, config.min_time_remaining, config.max_time_remaining)
        
        print(box_line(f"Time Left  : {time_color}{time_remaining:.1f}m {time_status}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        print(box_line(f"Status     : {Fore.GREEN}ACTIVE{Style.RESET_ALL}", w, "left", Fore.GREEN))
        box_border(False, w)
        print()
        
        # SIGNAL ANALYSIS Section
        box_border(True, w)
        print(box_line("🎯 SIGNAL ANALYSIS", w, "left", Fore.CYAN))
        box_separator(w)
        
        confidence = "HIGH" if rsi < 20 or rsi > 80 else ("MEDIUM" if rsi < 30 or rsi > 70 else "NONE")
        
        print(box_line(f"Action     : {action_color}{signal}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        print(box_line(f"Confidence : {Fore.YELLOW}{confidence}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        print(box_line(f"Position   : {action_color}{signal}{Style.RESET_ALL}", w, "left", Fore.GREEN))
        box_border(False, w)
        print()
        
        # Bottom note
        print(f"{Fore.CYAN}• RSI {rsi:.2f} {rsi_status.lower().split()[0]}{Style.RESET_ALL}")
    else:
        box_border(True, w, Fore.RED)
        print(box_line("🎯 MARKET", w, "left", Fore.CYAN))
        box_separator(w, Fore.RED)
        print(box_line(f"Status     : {Fore.RED}NO MARKET FOUND{Style.RESET_ALL}", w, "left", Fore.RED))
        print(box_line(f"Markets    : {Fore.YELLOW}{markets_found} found{Style.RESET_ALL}", w, "left", Fore.RED))
        box_border(False, w, Fore.RED)
        print()

def print_monitoring_ui(position, time_left, pnl=0):
    """Print beautiful monitoring UI"""
    clear_screen()
    w = 70
    
    # Header
    box_border(True, w)
    print(box_line("📈 MONITORING POSITION", w, "center", Fore.GREEN + Style.BRIGHT))
    box_border(False, w)
    print()
    
    # Position Details
    box_border(True, w)
    print(box_line("💰 POSITION", w, "left", Fore.CYAN))
    box_separator(w)
    print(box_line(f"Entry Amount : ${position.get('entry_amount', 0):.2f} USDC", w, "left", Fore.GREEN))
    print(box_line(f"Side         : {Fore.BLUE}{position.get('side', 'UNKNOWN')}{Style.RESET_ALL}", w, "left", Fore.GREEN))
    print(box_line(f"Market       : {Fore.MAGENTA}{position.get('market_question', 'Unknown')[:45]}{Style.RESET_ALL}", w, "left", Fore.GREEN))
    box_separator(w)
    print(box_line(f"Time Left    : {Fore.CYAN}{time_left:.1f} minutes{Style.RESET_ALL}", w, "left", Fore.GREEN))
    
    if pnl != 0:
        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
        print(box_line(f"P&L          : {pnl_color}{pnl:+.2f} USDC{Style.RESET_ALL}", w, "left", Fore.GREEN))
    
    box_border(False, w)
    print()

def print_trade_signal(signal, price, threshold):
    """Print trade signal box"""
    w = 70
    box_border(True, w, Fore.YELLOW)
    
    if signal == "BUY_UP":
        print(box_line("🟢 SIGNAL: BUY UP (RSI Oversold)", w, "center", Fore.GREEN + Style.BRIGHT))
    elif signal == "BUY_DOWN":
        print(box_line("🔴 SIGNAL: BUY DOWN (RSI Overbought)", w, "center", Fore.RED + Style.BRIGHT))
    else:
        print(box_line("⚪ SIGNAL: NEUTRAL (No Trade)", w, "center", Fore.YELLOW))
    
    box_separator(w)
    print(box_line(f"Price: {price:.4f} | Threshold: {threshold[0]}-{threshold[1]}", w, "center", Fore.CYAN))
    box_border(False, w, Fore.YELLOW)
    print()

def print_countdown(seconds, width=70):
    """Print countdown bar"""
    bar_width = width - 20
    filled = int(bar_width * (1 - seconds/30))
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"{Fore.CYAN}Next scan: [{Fore.GREEN}{bar}{Fore.CYAN}] {seconds}s{Style.RESET_ALL}")

def format_timestamp(dt: datetime) -> str:
    """Format datetime to timestamp string"""
    return dt.strftime("%Y%m%d%H%M")

def parse_end_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime"""
    if date_str:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return datetime.now()
