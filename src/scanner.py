"""
Polymarket Market Scanner for BTC Up/Down 5-minute markets
"""
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from config.settings import BotConfig

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scan and discover BTC Up/Down 5-minute markets"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
    
    def get_btc_5min_markets(self) -> List[Dict]:
        """
        Find BTC Up/Down 5-minute markets
        Returns list of valid markets within time filter
        """
        all_markets = []
        
        # Method 1: Events endpoint
        try:
            events_markets = self._scan_events()
            all_markets.extend(events_markets)
            logger.info(f"Events scan: {len(events_markets)} markets")
        except Exception as e:
            logger.debug(f"Events scan error: {e}")
        
        # Method 2: Markets endpoint (if events found nothing)
        if not all_markets:
            try:
                direct_markets = self._scan_markets()
                all_markets.extend(direct_markets)
                logger.info(f"Direct markets scan: {len(direct_markets)} markets")
            except Exception as e:
                logger.debug(f"Markets scan error: {e}")
        
        # Method 3: Timestamp slug search
        if not all_markets:
            try:
                ts_markets = self._scan_by_timestamp()
                all_markets.extend(ts_markets)
                logger.info(f"Timestamp scan: {len(ts_markets)} markets")
            except Exception as e:
                logger.debug(f"Timestamp scan error: {e}")
        
        # Sort by closest to ideal 5-minute window
        all_markets.sort(key=lambda x: abs(x["time_remaining"] - 5))
        
        logger.info(f"Total BTC 5m markets found: {len(all_markets)}")
        return all_markets
    
    def _scan_events(self) -> List[Dict]:
        """Scan via /events endpoint"""
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
        
        return self._process_items(events, item_type="event")
    
    def _scan_markets(self) -> List[Dict]:
        """Scan via /markets endpoint"""
        url = f"{self.config.gamma_host}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "archived": "false",
            "limit": 100
        }
        
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        markets = response.json()
        
        return self._process_items(markets, item_type="market")
    
    def _scan_by_timestamp(self) -> List[Dict]:
        """Generate and check timestamp-based slugs"""
        now = datetime.utcnow()
        btc_markets = []
        
        # Generate timestamps: 10 windows back, current, 10 forward
        for i in range(-10, 11):
            ts = now + timedelta(minutes=5*i)
            ts_str = ts.strftime("%Y%m%d%H%M")
            slug = f"btc-updown-5m-{ts_str}"
            
            try:
                url = f"{self.config.gamma_host}/events/slug/{slug}"
                response = self.session.get(url, timeout=3)
                
                if response.status_code == 200:
                    event = response.json()
                    markets = event.get("markets", [])
                    
                    for market in markets:
                        processed = self._process_single_market(market, event)
                        if processed:
                            btc_markets.append(processed)
                            logger.info(f"Found market via slug: {slug}")
                            
            except requests.RequestException:
                continue
        
        return btc_markets
    
    def _process_items(self, items: List[Dict], item_type: str = "event") -> List[Dict]:
        """Process events or markets to find BTC 5m"""
        btc_markets = []
        now = datetime.now().astimezone()
        
        for item in items:
            if item_type == "event":
                title = item.get("title", "").lower()
                slug = item.get("slug", "").lower()
                markets = item.get("markets", [])
            else:
                title = item.get("question", "").lower()
                slug = item.get("slug", "").lower()
                markets = [item]
            
            # Broader BTC detection
            has_btc = any(term in title or term in slug 
                         for term in ["btc", "bitcoin", "xbt"])
            has_direction = any(term in title or term in slug 
                              for term in ["up", "down", "higher", "lower"])
            has_timeframe = any(term in title or term in slug 
                              for term in ["5m", "5 minute", "5-minute", "5min", "5-min"])
            
            if not (has_btc and has_direction and has_timeframe):
                continue
            
            for market in markets:
                processed = self._process_single_market(market, item if item_type == "event" else None)
                if processed:
                    btc_markets.append(processed)
        
        return btc_markets
    
    def _process_single_market(self, market: Dict, event: Optional[Dict]) -> Optional[Dict]:
        """Process single market and check time filter"""
        if not market:
            return None
        
        end_date = market.get("endDate")
        if not end_date:
            return None
        
        try:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            time_remaining = (end_time - datetime.now().astimezone()).total_seconds() / 60
            
            # Apply time filter
            if not (self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining):
                return None
            
            return {
                "event": event or {},
                "market": market,
                "time_remaining": time_remaining,
                "end_time": end_time,
                "condition_id": market.get("conditionId"),
                "question": market.get("question", event.get("title", "Unknown") if event else "Unknown"),
                "token_ids": self._extract_token_ids(market)
            }
            
        except (ValueError, TypeError):
            return None
    
    def _extract_token_ids(self, market: Dict) -> Dict[str, str]:
        """Extract Yes/No token IDs from market data"""
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
                    if outcome in ["yes", "up", "higher"]:
                        token_ids["yes"] = token.get("token_id") or token.get("tokenId")
                    elif outcome in ["no", "down", "lower"]:
                        token_ids["no"] = token.get("token_id") or token.get("tokenId")
        
        except Exception as e:
            logger.debug(f"Error parsing token IDs: {e}")
        
        return token_ids
