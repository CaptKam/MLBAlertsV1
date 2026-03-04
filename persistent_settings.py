import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class PersistentSettings:
    """Manages persistent application settings across restarts"""
    
    def __init__(self, settings_file='mlb_monitor_settings.json'):
        self.settings_file = settings_file
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file, create default if doesn't exist"""
        default_settings = {
            'monitored_games': [],
            'notification_preferences': {
                'runners': True,
                'hits': True,
                'scoring': True,
                'inning_change': False,
                'home_runs': True,  # Enable home run alerts by default
                'strikeouts': False,
                'runners_23_no_outs': True,      # 87% probability
                'bases_loaded_no_outs': True,     # 85% probability
                'runner_3rd_no_outs': True,       # 75% probability
                'runners_13_no_outs': True,       # 70% probability
                'runners_23_one_out': True,       # 65% probability
                'runners_12_no_outs': True,       # 60% probability
                'runner_2nd_no_outs': True,       # 60% probability
                'bases_loaded_one_out': True,     # 60% probability
                'runner_3rd_one_out': True,       # 55% probability
                'runners_13_one_out': True,       # 55% probability
                # AI-Enhanced Power Alerts (ROI-focused)
                'ai_power_plus_scoring': True,    # Power hitter + runners on base
                'ai_power_high': True,           # High-confidence power (Tier A only)
                'pitcher_softening': True,       # Pitcher fatigue/contact patterns
                # Enhanced AI Features (optional)
                'ai_enhance_alerts': False,      # AI enhancements to alerts
                'ai_summarize_events': False,    # AI game summaries
                'ai_analyze_hits': False,        # AI hit analysis
                'ai_analyze_power_hitter': False, # AI power hitter predictions
                'ai_analyze_runners': False,     # AI runner situation analysis
                'ai_predict_scoring': False,     # AI scoring probability predictions
                # Weather alerts
                'seventh_inning': True,
                'game_start': True,
                'tie_ninth': True,
                'hot_windy': True,
                'power_hitter': True,
                'temp_wind': True,
                'wind_shift': True,
                'wind_speed': True,
                # Additional power alerts
                'clutch_hr': True,               # Power hitter + RISP in late innings
                'hot_hitter': True               # Hot hitting streaks
            },
            'auto_monitoring_enabled': True,
            'last_updated': None,
            'monitoring_active': False
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(loaded_settings)
                    logging.debug(f"Loaded persistent settings from {self.settings_file}")
                    return default_settings
            else:
                logging.debug(f"Creating new settings file: {self.settings_file}")
                self._save_settings(default_settings)
                return default_settings
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            return default_settings
    
    def _save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Save settings to file"""
        try:
            settings_to_save = settings if settings is not None else self.settings
            settings_to_save['last_updated'] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            logging.debug(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False
    
    def update_monitored_games(self, game_ids: List[int]) -> bool:
        """Update monitored games and persist"""
        self.settings['monitored_games'] = game_ids
        self.settings['monitoring_active'] = len(game_ids) > 0
        return self._save_settings()
    
    def update_notification_preferences(self, preferences: Dict[str, bool]) -> bool:
        """Update notification preferences and persist"""
        self.settings['notification_preferences'].update(preferences)
        return self._save_settings()
    
    def set_monitoring_active(self, active: bool) -> bool:
        """Set monitoring active state and persist"""
        self.settings['monitoring_active'] = active
        return self._save_settings()
    
    def set_auto_monitoring_enabled(self, enabled: bool) -> bool:
        """Enable/disable automatic monitoring restoration on startup"""
        self.settings['auto_monitoring_enabled'] = enabled
        return self._save_settings()
    
    def get_monitored_games(self) -> List[int]:
        """Get currently monitored game IDs"""
        return self.settings.get('monitored_games', [])
    
    def get_notification_preferences(self) -> Dict[str, bool]:
        """Get notification preferences"""
        return self.settings.get('notification_preferences', {})
    
    def is_monitoring_active(self) -> bool:
        """Check if monitoring should be active"""
        return self.settings.get('monitoring_active', False)
    
    def is_auto_monitoring_enabled(self) -> bool:
        """Check if auto-monitoring restoration is enabled"""
        return self.settings.get('auto_monitoring_enabled', True)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def clear_monitored_games(self) -> bool:
        """Clear all monitored games and stop monitoring"""
        self.settings['monitored_games'] = []
        self.settings['monitoring_active'] = False
        return self._save_settings()
    
    def get_settings_summary(self) -> str:
        """Get a human-readable summary of current settings"""
        monitored_count = len(self.get_monitored_games())
        prefs = self.get_notification_preferences()
        enabled_notifications = [k.replace('_', ' ').title() for k, v in prefs.items() if v]
        
        summary = f"🎯 {monitored_count} games monitored"
        if enabled_notifications:
            summary += f"\n📢 Alerts: {', '.join(enabled_notifications)}"
        
        return summary