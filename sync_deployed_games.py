#!/usr/bin/env python3
"""
Sync monitored games from deployed version to local development
This ensures local testing matches production monitoring
"""

import requests
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DeployedGameSync:
    def __init__(self, deployed_url=None):
        # Try to detect deployed URL or use localhost for development
        self.deployed_url = deployed_url or "http://localhost:5000"
        self.local_url = "http://localhost:5000"
        self.settings_file = "mlb_monitor_settings.json"
        
    def get_deployed_status(self):
        """Get current monitoring status from deployed version"""
        try:
            response = requests.get(f"{self.deployed_url}/api/status", timeout=5)
            if response.status_code == 200:
                return response.json().get('status', {})
            else:
                logging.warning(f"Deployed API returned {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Could not reach deployed version: {e}")
            return None
    
    def update_local_settings(self, deployed_status):
        """Update local settings to match deployed monitoring"""
        if not deployed_status:
            return False
            
        try:
            # Load current local settings
            with open(self.settings_file, 'r') as f:
                local_settings = json.load(f)
            
            # Extract deployed configuration
            deployed_games = deployed_status.get('monitored_games', [])
            deployed_prefs = deployed_status.get('notification_preferences', {})
            
            # Update local settings
            local_settings['monitored_games'] = deployed_games
            local_settings['notification_preferences'].update(deployed_prefs)
            local_settings['last_synced'] = datetime.now().isoformat()
            local_settings['sync_source'] = 'deployed_version'
            
            # Save updated settings
            with open(self.settings_file, 'w') as f:
                json.dump(local_settings, f, indent=2)
            
            logging.info(f"✅ Synced {len(deployed_games)} monitored games from deployed version")
            
            # Log the synchronized games
            if deployed_games:
                logging.info(f"📊 Monitoring games: {deployed_games}")
            else:
                logging.info("📊 No games currently being monitored")
                
            return True
            
        except Exception as e:
            logging.error(f"Failed to update local settings: {e}")
            return False
    
    def apply_to_local_monitor(self, deployed_status):
        """Apply deployed settings to local monitor instance"""
        if not deployed_status:
            return False
            
        try:
            deployed_games = deployed_status.get('monitored_games', [])
            deployed_prefs = deployed_status.get('notification_preferences', {})
            
            # Send update to local API
            update_payload = {
                'game_ids': deployed_games,
                'notification_preferences': deployed_prefs
            }
            
            response = requests.post(
                f"{self.local_url}/api/monitor", 
                json=update_payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logging.info("✅ Applied deployed settings to local monitor")
                return True
            else:
                logging.warning(f"Local API update returned {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to apply settings to local monitor: {e}")
            return False
    
    def sync_once(self):
        """Perform one-time sync from deployed to local"""
        logging.info("🔄 Syncing with deployed version...")
        
        # Get deployed status
        deployed_status = self.get_deployed_status()
        if not deployed_status:
            logging.error("❌ Could not get deployed status")
            return False
        
        # Update local settings file
        settings_updated = self.update_local_settings(deployed_status)
        
        # Apply to running monitor
        monitor_updated = self.apply_to_local_monitor(deployed_status)
        
        if settings_updated:
            logging.info("✅ Sync completed successfully")
            
            # Show summary
            games = deployed_status.get('monitored_games', [])
            if games:
                logging.info(f"📋 Now monitoring {len(games)} games locally to match deployment")
            else:
                logging.info("📋 No games being monitored (matching deployment)")
                
            return True
        else:
            logging.error("❌ Sync failed")
            return False
    
    def continuous_sync(self, interval_seconds=30):
        """Continuously sync with deployed version"""
        logging.info(f"🔄 Starting continuous sync (every {interval_seconds}s)")
        
        while True:
            try:
                self.sync_once()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logging.info("⏹️ Sync stopped by user")
                break
            except Exception as e:
                logging.error(f"Sync error: {e}")
                time.sleep(interval_seconds)

def main():
    import sys
    
    sync = DeployedGameSync()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        sync.continuous_sync()
    else:
        sync.sync_once()

if __name__ == "__main__":
    main()