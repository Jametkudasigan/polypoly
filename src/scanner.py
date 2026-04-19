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
        Try multiple methods: events endpoint, markets endpoint, direct search
        """
        markets = []
        
        # Method 1: Search via /events endpoint
        markets.extend(self._scan_events())
        
        # Method 2: Search via /markets endpoint
        if not markets:
            markets.extend(self._scan_markets())
        
        # Method 3: Direct search by slug/timestamp pattern
        if not markets:
            markets.extend(self._scan_by_timestamp())
        
        return markets
    
    def _scan_events(self) -> List[Dict]:
        """Scan via Gamma events endpoint"""
        try:
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
            
            return self._filter_btc_markets(events, source="events")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching events: {e}")
            return []
    
    def _scan_markets(self) -> List[Dict]:
        """Scan via Gamma markets endpoint directly"""
        try:
            url = f"{self.config.gamma_host}/markets"
            params = {
                "active": "true",
                "closed": "false",
                "archived": "false",
                "limit": 100
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            markets_data = response.json()
            
            btc_markets = []
            now = datetime.now().astimezone()
            
            for market in markets_data:
                question = market.get("question", "").lower()
                description = market.get("description", "").lower()
                slug = market.get("slug", "").lower()
                
                # Broader search terms
                is_btc = any(term in question or term in description or term in slug 
                           for term in ["btc", "bitcoin", "up/down", "up or down"])
                is_5min = any(term in question or term in description or term in slug 
                            for term in ["5m", "5 minute", "5-minute", "5 min"])
                
                if not (is_btc and is_5min):
                    continue
                
                end_date = market.get("endDate")
                if not end_date:
                    continue
                
                try:
                    end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    time_remaining = (end_time - now).total_seconds() / 60
                    
                    if self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining:
                        btc_markets.append({
                            "event": {"title": market.get("question", "")},
                            "market": market,
                            "time_remaining": time_remaining,
                            "end_time": end_time,
                            "condition_id": market.get("conditionId"),
                            "question": market.get("question", "Unknown"),
                            "token_ids": self._extract_token_ids(market)
                        })
                        
                except (ValueError, TypeError):
                    continue
            
            btc_markets.sort(key=lambda x: abs(x["time_remaining"] - 5))
            logger.info(f"Markets scan found {len(btc_markets)} BTC 5m markets")
            return btc_markets
            
        except requests.RequestException as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    def _scan_by_timestamp(self) -> List[Dict]:
        """
        Generate timestamp-based market URLs
        Pattern: https://polymarket.com/event/btc-updown-5m-{timestamp}
        """
        try:
            now = datetime.utcnow()
            # Round to nearest 5 minutes
            minutes = (now.minute // 5) * 5
            current_window = now.replace(minute=minutes, second=0, microsecond=0)
            
            # Generate timestamps untuk window saat ini dan beberapa window ke depan
            timestamps = []
            for i in range(-1, 3):  # Check 1 window back, current, and 2 forward
                ts = current_window + timedelta(minutes=5*i)
                timestamps.append(ts.strftime("%Y%m%d%H%M"))
            
            btc_markets = []
            
            for ts in timestamps:
                slug = f"btc-updown-5m-{ts}"
                url = f"{self.config.gamma_host}/events/slug/{slug}"
                
                try:
                    response = self.session.get(url, timeout=5)
                    if response.status_code == 200:
                        event = response.json()
                        markets = event.get("markets", [])
                        
                        for market in markets:
                            end_date = market.get("endDate")
                            if end_date:
                                end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                                time_remaining = (end_time - datetime.now().astimezone()).total_seconds() / 60
                                
                                if self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining:
                                    btc_markets.append({
                                        "event": event,
                                        "market": market,
                                        "time_remaining": time_remaining,
                                        "end_time": end_time,
                                        "condition_id": market.get("conditionId"),
                                        "question": market.get("question", event.get("title", "Unknown")),
                                        "token_ids": self._extract_token_ids(market)
                                    })
                                    logger.info(f"Found market via timestamp slug: {slug}")
                        
                except requests.RequestException:
                    continue
            
            return btc_markets
            
        except Exception as e:
            logger.error(f"Error in timestamp scan: {e}")
            return []
    
    def _filter_btc_markets(self, events: List[Dict], source: str = "events") -> List[Dict]:
        """Filter events/markets for BTC 5m"""
        btc_markets = []
        now = datetime.now().astimezone()
        
        for event in events:
            title = event.get("title", "").lower()
            slug = event.get("slug", "").lower()
            
            # Broader matching
            has_btc = any(term in title or term in slug for term in ["btc", "bitcoin"])
            has_updown = any(term in title or term in slug for term in ["up", "down", "up/down", "up or down"])
            has_5m = any(term in title or term in slug for term in ["5m", "5 minute", "5-minute", "5 min", "5min"])
            
            if not (has_btc and has_updown and has_5m):
                continue
            
            markets = event.get("markets", [])
            for market in markets:
                end_date = market.get("endDate")
                if not end_date:
                    continue
                
                try:
                    end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    time_remaining = (end_time - now).total_seconds() / 60
                    
                    if self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining:
                        btc_markets.append({
                            "event": event,
                            "market": market,
                            "time_remaining": time_remaining,
                            "end_time": end_time,
                            "condition_id": market.get("conditionId"),
                            "question": market.get("question", event.get("title", "Unknown")),
                            "token_ids": self._extract_token_ids(market)
                        })
                        
                except (ValueError, TypeError):
                    continue
        
        btc_markets.sort(key=lambda x: abs(x["time_remaining"] - 5))
        logger.info(f"Events scan found {len(btc_markets)} BTC 5m markets")
        return btc_markets
    
    def _extract_token_ids(self, market: Dict) -> Dict[str, str]:
        """Extract Yes/No token IDs from market data"""
        token_ids = {"yes": None, "no": None}
        
        try:
            # Try clobTokenIds
            clob_tokens = market.get("clobTokenIds")
            if clob_tokens:
                if isinstance(clob_tokens, str):
                    clob_tokens = json.loads(clob_tokens)
                if len(clob_tokens) >= 2:
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
        
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Error parsing token IDs: {e}")
        
        return token_ids
