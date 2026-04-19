#!/usr/bin/env python3
"""
Debug scanner untuk melihat semua market yang tersedia di Polymarket
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

import requests
import json
from datetime import datetime

GAMMA_HOST = "https://gamma-api.polymarket.com"

def get_all_events():
    """Ambil semua events aktif"""
    url = f"{GAMMA_HOST}/events"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    
    response = requests.get(url, params=params, timeout=15)
    events = response.json()
    
    print(f"Total events aktif: {len(events)}")
    print("="*80)
    
    # Filter yang mengandung BTC
    btc_events = []
    for event in events:
        title = event.get("title", "").lower()
        slug = event.get("slug", "").lower()
        
        if "btc" in title or "bitcoin" in title or "btc" in slug:
            btc_events.append(event)
            print(f"\n🎯 EVENT: {event.get('title')}")
            print(f"   Slug: {event.get('slug')}")
            print(f"   ID: {event.get('id')}")
            
            markets = event.get("markets", [])
            print(f"   Markets: {len(markets)}")
            
            for m in markets:
                print(f"      - {m.get('question')}")
                print(f"        ConditionId: {m.get('conditionId')}")
                print(f"        EndDate: {m.get('endDate')}")
                print(f"        Active: {m.get('active')}")
    
    print(f"\n{'='*80}")
    print(f"Total BTC-related events: {len(btc_events)}")
    return btc_events

def get_all_markets():
    """Ambil semua markets aktif langsung"""
    url = f"{GAMMA_HOST}/markets"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    
    response = requests.get(url, params=params, timeout=15)
    markets = response.json()
    
    print(f"\nTotal markets aktif: {len(markets)}")
    print("="*80)
    
    # Filter BTC
    btc_markets = []
    for market in markets:
        question = market.get("question", "").lower()
        slug = market.get("slug", "").lower()
        
        if "btc" in question or "bitcoin" in question or "btc" in slug:
            btc_markets.append(market)
            print(f"\n📊 MARKET: {market.get('question')}")
            print(f"   Slug: {market.get('slug')}")
            print(f"   ConditionId: {market.get('conditionId')}")
            print(f"   EndDate: {market.get('endDate')}")
            print(f"   clobTokenIds: {market.get('clobTokenIds')}")
    
    print(f"\n{'='*80}")
    print(f"Total BTC-related markets: {len(btc_markets)}")
    return btc_markets

def search_by_slug():
    """Coba cari dengan slug pattern"""
    now = datetime.utcnow()
    timestamps = []
    
    # Generate beberapa timestamp (sekarang, +5min, +10min, -5min)
    for i in range(-2, 5):
        ts = now + __import__('datetime').timedelta(minutes=5*i)
        ts_str = ts.strftime("%Y%m%d%H%M")
        timestamps.append(ts_str)
    
    print(f"\nMencoba {len(timestamps)} timestamp patterns...")
    
    for ts in timestamps:
        slug = f"btc-updown-5m-{ts}"
        url = f"{GAMMA_HOST}/events/slug/{slug}"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ FOUND: {slug}")
                print(json.dumps(response.json(), indent=2))
                return response.json()
            else:
                print(f"❌ Not found: {slug} (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {slug} - {e}")
    
    return None

if __name__ == "__main__":
    print("🔍 POLYMARKET SCANNER DEBUG\n")
    
    print("METHOD 1: Scan Events")
    print("-"*80)
    get_all_events()
    
    print("\n\nMETHOD 2: Scan Markets")
    print("-"*80)
    get_all_markets()
    
    print("\n\nMETHOD 3: Search by Timestamp Slug")
    print("-"*80)
    search_by_slug()
