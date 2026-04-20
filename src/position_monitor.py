"""
Position Monitor and Auto-Redeem for Polymarket
"""
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List
from config.settings import BotConfig

logger = logging.getLogger(__name__)

class PositionMonitor:
    """Monitor positions and handle auto-redeem"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
    
    def get_positions(self) -> List[Dict]:
        """Get current open positions"""
        try:
            url = f"{self.config.data_host}/positions"
            params = {"user": self.config.funder_address}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def get_position_by_market(self, condition_id: str) -> Optional[Dict]:
        """Get specific position by market condition ID"""
        positions = self.get_positions()
        
        for position in positions:
            if position.get("conditionId") == condition_id or position.get("market") == condition_id:
                return position
        
        return None
    
    def is_market_resolved(self, condition_id: str) -> bool:
        """Check if market has been resolved"""
        try:
            url = f"{self.config.gamma_host}/markets/{condition_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                market = response.json()
                return market.get("resolved", False) or market.get("closed", False)
            
            return False
            
        except requests.RequestException as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def get_winning_outcome(self, condition_id: str) -> Optional[str]:
        """Get winning outcome for resolved market"""
        try:
            url = f"{self.config.gamma_host}/markets/{condition_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                market = response.json()
                tokens = market.get("tokens", [])
                
                for token in tokens:
                    if token.get("winner", False):
                        return token.get("outcome")
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching winning outcome: {e}")
            return None
    
    def should_exit_position(self, position: Dict, market_data: Dict) -> bool:
        """Determine if position should be exited"""
        condition_id = position.get("conditionId") or position.get("market")
        
        if self.is_market_resolved(condition_id):
            return True
        
        end_time = market_data.get("end_time")
        if end_time:
            time_remaining = (end_time - datetime.now().astimezone()).total_seconds() / 60
            if time_remaining <= 0:
                return True
        
        return False
