"""
Configuration management for MLB Alert System
"""
import os
from typing import Dict, Any

class Config:
    """Environment-based configuration"""
    
    # Environment
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = APP_ENV == "development"
    
    # Flask settings
    SECRET_KEY = os.getenv("SESSION_SECRET", "dev-secret-key")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
    MYSPORTSFEEDS_API_KEY = os.getenv("MYSPORTSFEEDS_API_KEY")
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Monitoring settings
    MONITORING_INTERVAL = float(os.getenv("MONITORING_INTERVAL", "0.5"))
    MAX_ALERTS_PER_HOUR = int(os.getenv("MAX_ALERTS_PER_HOUR", "100"))
    
    @classmethod
    def validate_required_secrets(cls) -> Dict[str, bool]:
        """Validate that required secrets are present"""
        required_secrets = {
            "OPENAI_API_KEY": bool(cls.OPENAI_API_KEY),
            "TELEGRAM_BOT_TOKEN": bool(cls.TELEGRAM_BOT_TOKEN),
            "TELEGRAM_CHAT_ID": bool(cls.TELEGRAM_CHAT_ID),
            "SESSION_SECRET": bool(cls.SECRET_KEY != "dev-secret-key"),
        }
        
        optional_secrets = {
            "API_SPORTS_KEY": bool(cls.API_SPORTS_KEY),
            "MYSPORTSFEEDS_API_KEY": bool(cls.MYSPORTSFEEDS_API_KEY),
            "DATABASE_URL": bool(cls.DATABASE_URL)
        }
        
        return {
            "required": required_secrets,
            "optional": optional_secrets,
            "all_required_present": all(required_secrets.values())
        }
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get configuration summary for health checks"""
        secrets_status = cls.validate_required_secrets()
        
        return {
            "environment": cls.APP_ENV,
            "debug": cls.DEBUG,
            "secrets_configured": secrets_status["all_required_present"],
            "monitoring_interval": cls.MONITORING_INTERVAL,
            "max_alerts_per_hour": cls.MAX_ALERTS_PER_HOUR
        }