import requests
import logging
import os
from typing import Dict, Any, Optional

class TelegramNotifier:
    """
    Sends MLB alerts to Telegram using bot API
    """
    
    def __init__(self):
        # Get and strip whitespace from environment variables
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        self.bot_token = bot_token.strip() if bot_token else None
        self.chat_id = chat_id.strip() if chat_id else None
        
        if not self.bot_token or not self.chat_id:
            logging.warning("Telegram bot token or chat ID not found. Telegram notifications disabled.")
            self.enabled = False
            self.base_url = None
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
            logging.info("Telegram notifier initialized successfully")
    
    def send_alert(self, game_info: str, message: str, alert_type: str) -> bool:
        """
        Send an MLB alert to Telegram
        
        Args:
            game_info: Game information (e.g., "Yankees @ Red Sox")
            message: Alert message
            alert_type: Type of alert (runners, hit, score, etc.)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Format the message with emoji based on alert type
            emoji = self._get_alert_emoji(alert_type)
            
            formatted_message = f"{emoji} **{game_info}**\n{message}"
            
            # Send message via Telegram API
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"Telegram alert sent: {alert_type} - {game_info}")
                return True
            else:
                logging.error(f"Failed to send Telegram alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Telegram alert: {e}")
            return False
    
    def _get_alert_emoji(self, alert_type: str) -> str:
        """Get appropriate emoji for different alert types"""
        emoji_map = {
            'runners': '🏃',
            'hit': '⚾',
            'score': '🏆',
            'inning': '🔄',
            'home_run': '🚀',
            'strikeout': '❌',
            'connection': '🔗',
            'test_connection': '✅'
        }
        return emoji_map.get(alert_type, '📢')
    
    def send_test_message(self) -> bool:
        """Send a test message to verify Telegram connection"""
        if not self.enabled:
            logging.error("Cannot send test message - Telegram not enabled")
            return False
        
        try:
            test_message = "🏟️ **MLB Monitor Connected**\nTelegram alerts are now active! You'll receive notifications for live game events."
            
            url = f"{self.base_url}/sendMessage"
            logging.info(f"Sending test message to Telegram API: {url}")
            logging.info(f"Chat ID: {self.chat_id}")
            
            payload = {
                'chat_id': self.chat_id,
                'text': test_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info("Telegram test message sent successfully")
                return True
            else:
                logging.error(f"Failed to send test message: {response.status_code} - {response.text}")
                logging.error(f"URL used: {url}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending test message: {e}")
            logging.error(f"Bot token: {self.bot_token[:10]}..." if self.bot_token else "No bot token")
            logging.error(f"Chat ID: {self.chat_id}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Telegram notifier status"""
        return {
            'enabled': self.enabled,
            'bot_token_set': bool(self.bot_token),
            'chat_id_set': bool(self.chat_id)
        }