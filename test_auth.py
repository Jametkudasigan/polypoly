#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import BotConfig
from src.executor import TradeExecutor

config = BotConfig()
config.validate()

print(f"Private Key: {config.private_key[:20]}...")
print(f"Funder: {config.funder_address}")
print(f"Signature Type: {config.signature_type}")

try:
    executor = TradeExecutor(config)
    balance = executor.get_balance()
    print(f"✅ Success! Balance: {balance} USDC")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
