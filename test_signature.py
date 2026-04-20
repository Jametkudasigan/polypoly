#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from config.settings import BotConfig

config = BotConfig()

print(f"Testing with:")
print(f"  Funder: {config.funder_address}")
print(f"  Chain ID: {config.chain_id}")
print(f"  Signature Type: {config.signature_type}")
print(f"  Private Key: {config.private_key[:20]}...")

# Test 1: Derive API key
print("\n--- Test 1: Derive API Key ---")
try:
    client = ClobClient(
        host=config.clob_host,
        key=config.private_key,
        chain_id=config.chain_id,
        signature_type=config.signature_type,
        funder=config.funder_address
    )
    
    creds = client.create_or_derive_api_creds()
    print(f"✅ API Key: {creds.api_key[:30]}...")
    print(f"✅ Passphrase: {creds.api_passphrase[:20]}...")
    
    # Test 2: Re-init dengan creds
    print("\n--- Test 2: Re-init dengan Creds ---")
    client2 = ClobClient(
        host=config.clob_host,
        key=config.private_key,
        chain_id=config.chain_id,
        signature_type=config.signature_type,
        funder=config.funder_address,
        creds=ApiCreds(
            api_key=creds.api_key,
            api_secret=creds.api_secret,
            api_passphrase=creds.api_passphrase
        )
    )
    
    # Test 3: Get balance
    print("\n--- Test 3: Get Balance ---")
    from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
    balance = client2.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )
    print(f"✅ Balance: {int(balance['balance']) / 1e6} USDC")
    
    # Test 4: Get API keys
    print("\n--- Test 4: Get API Keys ---")
    keys = client2.get_api_keys()
    print(f"✅ API Keys: {keys}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
