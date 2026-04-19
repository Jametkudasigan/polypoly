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
        
        Returns:
            List of matching markets with metadata
        """
        try:
            # Search for active BTC markets
            url = f"{self.config.gamma_host}/events"
            params = {
                "active": "true",
                "closed": "false",
                "archived": "false",
                "limit": 100,
                "order": "volume_24hr",
                "ascending": "false"
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            events = response.json()
            
            btc_markets = []
            now = datetime.now().astimezone()
            
            for event in events:
                title = event.get("title", "").lower()
                
                # Filter for BTC/Bitcoin markets
                if not ("btc" in title or "bitcoin" in title):
                    continue
                
                # Filter for Up/Down markets
                if not ("up" in title and "down" in title):
                    continue
                
                # Filter for 5-minute markets
                if not ("5m" in title or "5 minute" in title or "5-minute" in title):
                    continue
                
                markets = event.get("markets", [])
                for market in markets:
                    # Check time remaining
                    end_date = market.get("endDate")
                    if not end_date:
                        continue
                    
                    try:
                        end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        time_remaining = (end_time - now).total_seconds() / 60
                        
                        # Apply time filter
                        if self.config.min_time_remaining <= time_remaining <= self.config.max_time_remaining:
                            market_data = {
                                "event": event,
                                "market": market,
                                "time_remaining": time_remaining,
                                "end_time": end_time,
                                "condition_id": market.get("conditionId"),
                                "question": market.get("question", event.get("title", "Unknown")),
                                "token_ids": self._extract_token_ids(market)
                            }
                            btc_markets.append(market_data)
                            
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Error parsing end date: {e}")
                        continue
            
            # Sort by closest to ideal time (5 minutes)
            btc_markets.sort(key=lambda x: abs(x["time_remaining"] - 5))
            
            logger.info(f"Found {len(btc_markets)} BTC 5m markets")
            return btc_markets
            
        except requests.RequestException as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    def _extract_token_ids(self, market: Dict) -> Dict[str, str]:
        """Extract Yes/No token IDs from market data"""
        token_ids = {
            "yes": None,
            "no": None
        }
        
        try:
            # Try to get from clobTokenIds
            clob_tokens = market.get("clobTokenIds")
            if clob_tokens:
                if isinstance(clob_tokens, str):
                    clob_tokens = json.loads(clob_tokens)
                
                if len(clob_tokens) >= 2:
                    token_ids["yes"] = clob_tokens[0]
                    token_ids["no"] = clob_tokens[1]
            
            # Alternative: get from tokens array
            if not token_ids["yes"]:
                tokens = market.get("tokens", [])
                for token in tokens:
                    outcome = token.get("outcome", "").lower()
                    if "yes" in outcome or "up" in outcome:
                        token_ids["yes"] = token.get("token_id") or token.get("tokenId")
                    elif "no" in outcome or "down" in outcome:
                        token_ids["no"] = token.get("token_id") or token.get("tokenId")
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing token IDs: {e}")
        
        return token_ids
    
    def get_market_by_condition_id(self, condition_id: str) -> Optional[Dict]:
        """Get specific market by condition ID"""
        try:
            url = f"{self.config.gamma_host}/markets/{condition_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching market: {e}")
            return None
