"""
Utility functions for Polymarket BTC Bot - Single Bingkai Style
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

# Bingkai characters
H = "═"
V = "║"
TL = "╔"
TR = "╗"
BL = "╚"
BR = "╝"
L = "╠"
R = "╣"

def bingkai_top(width=70, color=Fore.GREEN):
    """Print top border bingkai"""
    print(f"{color}{TL}{H * (width - 2)}{TR}{Style.RESET_ALL}")

def bingkai_bottom(width=70, color=Fore.GREEN):
    """Print bottom border bingkai"""
    print(f"{color}{BL}{H * (width - 2)}{BR}{Style.RESET_ALL}")

def bingkai_separator(width=70, color=Fore.GREEN):
    """Print separator line (horizontal dalam bingkai)"""
    print(f"{color}{L}{H * (width - 2)}{R}{Style.RESET_ALL}")

def bingkai_line(text="", width=68, color=Fore.GREEN, align="left"):
    """Print line inside bingkai"""
    if align == "center":
        text = text.center(width)
    elif align == "right":
        text = text.rjust(width)
    else:
        text = text.ljust(width)
    return f"{Fore.GREEN}{V}{Style.RESET_ALL} {color}{text}{Style.RESET_ALL} {Fore.GREEN}{V}{Style.RESET_ALL}"

def format_rsi_status(rsi, oversold, overbought):
    """Format RSI dengan color dan status"""
    if rsi < oversold:
        return Fore.RED, "OVERSOLD ↓", "BUY UP", Fore.RED
    elif rsi > overbought:
        return Fore.GREEN, "OVERBOUGHT ↑", "BUY DOWN", Fore.GREEN
    else:
        return Fore.YELLOW, "NEUTRAL ↔", "SKIP", Fore.YELLOW

def format_time_status(time_remaining, min_time, max_time):
    """Format time dengan status"""
    if min_time <= time_remaining <= max_time:
        return Fore.GREEN, "✅ SWEET SPOT"
    elif time_remaining < min_time:
        return Fore.RED, "❌ TOO SHORT"
    else:
        return Fore.YELLOW, "⏳ WAITING"

def print_scanning_ui(scan_num, balance, rsi, market_data, config, markets_found=0, yes_price=0, no_price=0):
    """Print scanning UI dalam SATU bingkai besar"""
    clear_screen()
    w = 70
    
    # === SATU BINGKAI BESAR ===
    bingkai_top(w, Fore.GREEN)
    
    # Header
    print(bingkai_line(f"🔍 SCANNING MARKET #{scan_num}", w-2, Fore.CYAN + Style.BRIGHT, "center"))
    bingkai_separator(w, Fore.GREEN)
    
    # WALLET Section
    print(bingkai_line("💰 WALLET", w-2, Fore.CYAN, "left"))
    print(bingkai_line(f"USDC Balance : ${balance:,.2f}", w-2, Fore.GREEN))
    bingkai_separator(w, Fore.GREEN)
    
    # MOMENTUM Section
    print(bingkai_line("📊 MOMENTUM (Yahoo Finance)", w-2, Fore.CYAN, "left"))
    
    rsi_color, rsi_status, signal, action_color = format_rsi_status(rsi, config.rsi_oversold, config.rsi_overbought)
    print(bingkai_line(f"BTC RSI (5m) : {rsi_color}{rsi:.2f}{Style.RESET_ALL}", w-2, Fore.GREEN))
    print(bingkai_line(f"Status       : {rsi_color}{rsi_status}{Style.RESET_ALL}", w-2, Fore.GREEN))
    bingkai_separator(w, Fore.GREEN)
    
    # MARKET Section
    if market_data:
        print(bingkai_line("🎯 MARKET", w-2, Fore.CYAN, "left"))
        
        question = market_data.get("question", "Unknown")
        condition_id = market_data.get("condition_id", "")[:35] + "..."
        
        print(bingkai_line(f"Question   : {Fore.MAGENTA}{question}{Style.RESET_ALL}", w-2, Fore.GREEN))
        print(bingkai_line(f"Condition  : {Fore.CYAN}{condition_id}{Style.RESET_ALL}", w-2, Fore.GREEN))
        bingkai_separator(w, Fore.GREEN)
        
        if yes_price and no_price:
            spread = abs(yes_price - no_price)
            print(bingkai_line(f"YES Price  : $ {yes_price:.3f}", w-2, Fore.GREEN))
            print(bingkai_line(f"NO Price   : $ {no_price:.3f}", w-2, Fore.GREEN))
            print(bingkai_line(f"Spread     : $ {spread:.3f}", w-2, Fore.GREEN))
            bingkai_separator(w, Fore.GREEN)
        
        time_remaining = market_data.get("time_remaining", 0)
        time_color, time_status = format_time_status(time_remaining, config.min_time_remaining, config.max_time_remaining)
        
        print(bingkai_line(f"Time Left  : {time_color}{time_remaining:.1f}m {time_status}{Style.RESET_ALL}", w-2, Fore.GREEN))
        print(bingkai_line(f"Status     : {Fore.GREEN}ACTIVE{Style.RESET_ALL}", w-2, Fore.GREEN))
        bingkai_separator(w, Fore.GREEN)
        
        # SIGNAL ANALYSIS Section
        print(bingkai_line("🎯 SIGNAL ANALYSIS", w-2, Fore.CYAN, "left"))
        
        confidence = "HIGH" if rsi < 20 or rsi > 80 else ("MEDIUM" if rsi < 30 or rsi > 70 else "NONE")
        
        print(bingkai_line(f"Action     : {action_color}{signal}{Style.RESET_ALL}", w-2, Fore.GREEN))
        print(bingkai_line(f"Confidence : {Fore.YELLOW}{confidence}{Style.RESET_ALL}", w-2, Fore.GREEN))
        print(bingkai_line(f"Position   : {action_color}{signal}{Style.RESET_ALL}", w-2, Fore.GREEN))
    else:
        print(bingkai_line("🎯 MARKET", w-2, Fore.CYAN, "left"))
        print(bingkai_line(f"Status     : {Fore.RED}NO MARKET FOUND{Style.RESET_ALL}", w-2, Fore.RED))
        print(bingkai_line(f"Markets    : {Fore.YELLOW}{markets_found} found{Style.RESET_ALL}", w-2, Fore.RED))
    
    bingkai_bottom(w, Fore.GREEN)
    print()
    
    # Bottom note (di luar bingkai)
    if market_data:
        print(f"{Fore.CYAN}• RSI {rsi:.2f} {rsi_status.lower().split()[0]}{Style.RESET_ALL}")

def print_monitoring_ui(position, time_left, pnl=0):
    """Print monitoring UI dalam SATU bingkai besar"""
    clear_screen()
    w = 70
    
    bingkai_top(w, Fore.GREEN)
    
    # Header
    print(bingkai_line("📈 MONITORING POSITION", w-2, Fore.GREEN + Style.BRIGHT, "center"))
    bingkai_separator(w, Fore.GREEN)
    
    # Position Details
    print(bingkai_line("💰 POSITION", w-2, Fore.CYAN, "left"))
    print(bingkai_line(f"Entry Amount : ${position.get('entry_amount', 0):.2f} USDC", w-2, Fore.GREEN))
    print(bingkai_line(f"Side         : {Fore.BLUE}{position.get('side', 'UNKNOWN')}{Style.RESET_ALL}", w-2, Fore.GREEN))
    print(bingkai_line(f"Market       : {Fore.MAGENTA}{position.get('market_question', 'Unknown')[:55]}{Style.RESET_ALL}", w-2, Fore.GREEN))
    bingkai_separator(w, Fore.GREEN)
    
    print(bingkai_line(f"Time Left    : {Fore.CYAN}{time_left:.1f} minutes{Style.RESET_ALL}", w-2, Fore.GREEN))
    
    if pnl != 0:
        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
        print(bingkai_line(f"P&L          : {pnl_color}{pnl:+.2f} USDC{Style.RESET_ALL}", w-2, Fore.GREEN))
    
    bingkai_bottom(w, Fore.GREEN)
    print()

def print_trade_signal(signal, price, threshold):
    """Print trade signal dalam bingkai"""
    w = 70
    
    if signal == "BUY_UP":
        bingkai_top(w, Fore.GREEN)
        print(bingkai_line("🟢 SIGNAL: BUY UP (RSI Oversold)", w-2, Fore.GREEN + Style.BRIGHT, "center"))
    elif signal == "BUY_DOWN":
        bingkai_top(w, Fore.RED)
        print(bingkai_line("🔴 SIGNAL: BUY DOWN (RSI Overbought)", w-2, Fore.RED + Style.BRIGHT, "center"))
    else:
        bingkai_top(w, Fore.YELLOW)
        print(bingkai_line("⚪ SIGNAL: NEUTRAL (No Trade)", w-2, Fore.YELLOW, "center"))
    
    bingkai_separator(w, Fore.GREEN)
    print(bingkai_line(f"Price: {price:.4f} | Threshold: {threshold[0]}-{threshold[1]}", w-2, Fore.CYAN, "center"))
    bingkai_bottom(w, Fore.YELLOW)
    print()

def format_timestamp(dt: datetime) -> str:
    """Format datetime ke timestamp string"""
    return dt.strftime("%Y%m%d%H%M")

def parse_end_date(date_str: str) -> datetime:
    """Parse ISO date string ke datetime"""
    if date_str:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return datetime.now()
