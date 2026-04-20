"""
Polymarket Market Scanner for BTC Up/Down 5-minute markets
"""
import logging
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from config.settings import BotConfig

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scan and discover BTC Up/Down 5-minute markets"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
    
    def get_btc_5min_markets(self) -> List[Dict]:
        """Find BTC Up/Down 5-minute markets"""
        all_markets = []
        
        # Method 1: Cari via slug dengan Unix timestamp
        ts_markets = self._scan_by_unix_timestamp()
        all_markets.extend(ts_markets)
        
        # Method 2: Fallback ke events endpoint
        if not all_markets:
            try:
                events_markets = self._scan_events()
                all_markets.extend(events_markets)
            except Exception as e:
                logger.debug(f"Events scan error: {e}")
        
        # Sort by closest to ideal 5-minute window
        all_markets.sort(key=lambda x: abs(x["time_remaining"] - 5))
        
        if all_markets:
            logger.info(f"Found {len(all_markets)} BTC 5m market(s)")
        else:
            logger.info("No BTC 5m markets found")
        
        return all_markets
    
    def _scan_by_unix_timestamp(self) -> List[Dict]:
        """
        Generate Unix timestamp-based slugs seperti:
        btc-updown-5m-1776634800
        """
        now = datetime.now(timezone.utc)
        btc_markets = []
        
        # Generate beberapa timestamp window (5 menit interval)
        # Cari yang aktif dalam range waktu yang valid
        for i in range(-5, 10):
            # Round ke kelipatan 5 menit terdekat
            minutes = (now.minute // 5) * 5
            base_time = now.replace(minute=minutes, second=0, microsecond=0)
            target_time = base_time + timedelta(minutes=5*i)
            
            unix_ts = int(target_time.timestamp())
            slug = f"btc-updown-5m-{unix_ts}"
            
            try:
                url = f"{self.config.gamma_host}/events/slug/{slug}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    event = response.json()
                    markets = event.get("markets", [])
                    
                    for market in markets:
                        processed = self._process_single_market(market, event)
                        if processed:
                            btc_markets.append(processed)
                            logger.debug(f"Found market via slug: {slug}")
                            
            except requests.RequestException:
                continue
        
        return btc_markets
    
    def _scan_events(self) -> List[Dict]:
        """Scan via /events endpoint sebagai fallback"""
        url = f"{self.config.gamma_host}/events"
        params = {
            "active": "true",
            "closed": "false",
            "archived": "false",
            "limit": 100
        }
        
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        events = response.json()
        
        btc_markets = []
        now = datetime.now().astimezone()
        
        for event in events:
            title = event.get("title", "").lower()
            slug = event.get("slug", "").lower()
            
            # Cek apakah BTC 5m market
            is_btc = any(term in title or term in slug for term in ["btc", "bitcoin"])
            is_5m = "5m" in slug or "5-minute" in slug or "5min" in slug
            
            if not (is_btc and is_5m):
                continue
            
            for market in event.get("markets", []):
                processed = self._process_single_market(market, event)
                if processed:
                    btc_markets.append(processed)
        
        return btc_markets
    
    def _process_single_market(self, market: Dict, event: Optional[Dict]) -> Optional[Dict]:
        """Process single market dan cek time filter"""
        if not market:
            return None
        
        end_date = market.get("endDate")
        if not end_date:
            return None
        
        try:
            # Parse ISO date
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            now = datetime.now().astimezone()
            time_remaining = (end_time - now).total_seconds() / 60
            
            # Apply time filter dari config
            if not (self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining):
                logger.debug(f"Time remaining {time_remaining:.1f}m outside range")
                return None
            
            return {
                "event": event or {},
                "market": market,
                "time_remaining": time_remaining,
                "end_time": end_time,
                "condition_id": market.get("conditionId"),
                "question": market.get("question", event.get("title", "Unknown") if event else "Unknown"),
                "token_ids": self._extract_token_ids(market),
                "slug": event.get("slug", "") if event else market.get("slug", "")
            }
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Error processing market: {e}")
            return None
    
    def _extract_token_ids(self, market: Dict) -> Dict[str, str]:
        """Extract Yes/No token IDs dari market data"""
        token_ids = {"yes": None, "no": None}
        
        try:
            # Try clobTokenIds
            clob_tokens = market.get("clobTokenIds")
            if clob_tokens:
                if isinstance(clob_tokens, str):
                    clob_tokens = json.loads(clob_tokens)
                if isinstance(clob_tokens, list) and len(clob_tokens) >= 2:
                    token_ids["yes"] = clob_tokens[0]
                    token_ids["no"] = clob_tokens[1]
            
            # Alternative: tokens array
            if not token_ids["yes"]:
                tokens = market.get("tokens", [])
                for token in tokens:
                    outcome = token.get("outcome", "").lower()
                    if outcome in ["yes", "up"]:
                        token_ids["yes"] = token.get("token_id") or token.get("tokenId")
                    elif outcome in ["no", "down"]:
                        token_ids["no"] = token.get("token_id") or token.get("tokenId")
        
        except Exception as e:
            logger.debug(f"Error parsing token IDs: {e}")
        
        return token_ids
