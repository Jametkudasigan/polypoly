# test_connection.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import BotConfig
from src.executor import TradeExecutor

config = BotConfig()
config.validate()

print(f"Funder: {config.funder_address}")
print(f"Signature Type: {config.signature_type}")

executor = TradeExecutor(config)
balance = executor.get_balance()
print(f"Balance: {balance} USDC")
