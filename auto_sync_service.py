#!/usr/bin/env python3
"""
Automatic sync service to keep local development in sync with deployed monitoring
Runs as a background service to continuously mirror production settings
"""

import requests
import json
import time
import logging
import threading
from datetime import datetime
from mlb_monitor import MLBMonitor

class AutoSyncService:
    def __init__(self):
        self.settings_file = "mlb_monitor_settings.json"
        self.sync_interval = 30  # seconds
        self.is_running = False
        self.sync_thread = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_current_local_status(self):
        """Get current local monitoring status"""
        try:
            response = requests.get("http://localhost:5000/api/status", timeout=3)
            if response.status_code == 200:
                return response.json().get('status', {})
        except:
            pass
        return {}
    
    def sync_from_settings(self):
        """Apply settings file to running monitor"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            monitored_games = settings.get('monitored_games', [])
            notification_prefs = settings.get('notification_preferences', {})
            
            # Apply to local monitor via API
            payload = {
                'game_ids': monitored_games,
                'notification_preferences': notification_prefs,
                'sync_source': 'auto_sync'
            }
            
            response = requests.post("http://localhost:5000/api/monitor", 
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                if monitored_games:
                    self.logger.info(f"🔄 Auto-synced {len(monitored_games)} games to local monitor")
                return True
            else:
                self.logger.warning(f"Sync API returned {response.status_code}")
                return False
                
        except FileNotFoundError:
            # Create default settings if file doesn't exist
            default_settings = {
                "monitored_games": [],
                "notification_preferences": {
                    "power_hitter": True,
                    "hot_hitter": True,
                    "scoring": True,
                    "runners": True,
                    "home_runs": True,
                    "bases_loaded_no_outs": True
                },
                "auto_monitoring_enabled": True
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(default_settings, f, indent=2)
                
            self.logger.info("📁 Created default settings file")
            return False
            
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return False
    
    def monitor_settings_changes(self):
        """Monitor for changes in settings file and apply them"""
        last_modified = 0
        
        while self.is_running:
            try:
                import os
                current_modified = os.path.getmtime(self.settings_file)
                
                if current_modified > last_modified:
                    self.logger.info("📄 Settings file changed, applying updates...")
                    self.sync_from_settings()
                    last_modified = current_modified
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Settings monitor error: {e}")
                time.sleep(5)
    
    def sync_loop(self):
        """Main sync loop"""
        self.logger.info("🔄 Auto-sync service started")
        
        # Initial sync
        self.sync_from_settings()
        
        # Monitor settings changes
        self.monitor_settings_changes()
    
    def start(self):
        """Start the auto-sync service"""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("✅ Auto-sync service started")
    
    def stop(self):
        """Stop the auto-sync service"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.info("⏹️ Auto-sync service stopped")

# Global sync service instance
auto_sync = AutoSyncService()

def start_auto_sync():
    """Start auto-sync if not already running"""
    auto_sync.start()

def stop_auto_sync():
    """Stop auto-sync service"""
    auto_sync.stop()

if __name__ == "__main__":
    # Run as standalone service
    try:
        auto_sync.start()
        print("🔄 Auto-sync service running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        auto_sync.stop()
        print("\n⏹️ Auto-sync service stopped")