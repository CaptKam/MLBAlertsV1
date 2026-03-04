#!/usr/bin/env python
"""Prepare system for deployment and verify all components"""

import json
import os
import sys
from datetime import datetime

def check_environment():
    """Verify all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'OPENAI_API_KEY',
        'SESSION_SECRET'
    ]
    
    optional_vars = [
        'API_SPORTS_KEY',
        'MYSPORTSFEEDS_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if os.environ.get(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
            missing.append(var)
    
    print("\nOptional APIs:")
    for var in optional_vars:
        if os.environ.get(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ⚠️ {var}: Not set (optional)")
    
    return len(missing) == 0

def verify_configuration():
    """Check that all alerts are properly configured"""
    print("\n📋 Verifying Alert Configuration...")
    
    with open('mlb_monitor_settings.json', 'r') as f:
        settings = json.load(f)
    
    enabled_count = sum(1 for v in settings['notification_preferences'].values() if v)
    print(f"  ✅ Total alerts enabled: {enabled_count}")
    
    # Verify key alerts are enabled
    critical_alerts = [
        'bases_loaded_no_outs',
        'power_hitter',
        'hot_hitter',
        'ai_predict_scoring'
    ]
    
    for alert in critical_alerts:
        if settings['notification_preferences'].get(alert, False):
            print(f"  ✅ {alert}: Enabled")
        else:
            print(f"  ⚠️ {alert}: Disabled")
    
    return enabled_count >= 30

def create_deployment_marker():
    """Create a marker file to indicate deployment readiness"""
    with open('.deployment_ready', 'w') as f:
        f.write(f"Deployment prepared at: {datetime.now().isoformat()}\n")
        f.write("System ready for production\n")
    print("\n✅ Deployment marker created")

def main():
    print("🚀 MLB MONITOR DEPLOYMENT PREPARATION")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Verify configuration
    config_ok = verify_configuration()
    
    # Summary
    print("\n📊 DEPLOYMENT STATUS")
    print("=" * 50)
    
    if env_ok and config_ok:
        print("✅ SYSTEM READY FOR DEPLOYMENT")
        print("\nNext Steps:")
        print("1. Click the Deploy button in Replit")
        print("2. Monitor the Telegram group for alerts")
        print("3. System will auto-detect tonight's games")
        create_deployment_marker()
        return 0
    else:
        print("❌ DEPLOYMENT CHECKS FAILED")
        print("\nPlease fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())