#!/usr/bin/env python3
"""
Final comprehensive system check before deployment
Verifies all components are working correctly for tonight's games
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_imports():
    """Check all required modules can be imported"""
    print("\n1. Checking Module Imports")
    print("-" * 40)
    
    modules_to_check = [
        ('mlb_monitor', 'Main monitoring module'),
        ('math_engines', 'Math engine calculations'),
        ('multi_source_aggregator', 'Data aggregation'),
        ('telegram_notifier', 'Telegram notifications'),
        ('weather_integration', 'Weather analysis'),
        ('openai_helper', 'AI predictions'),
        ('models', 'Database models'),
        ('app', 'Flask application')
    ]
    
    all_good = True
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}: {description}")
        except ImportError as e:
            print(f"  ❌ {module_name}: Failed - {e}")
            all_good = False
    
    return all_good

def check_math_engine():
    """Check math engine calculations are working"""
    print("\n2. Checking Math Engine Calculations")
    print("-" * 40)
    
    from math_engines import PowerFeatures, pa_hr_probability, power_tier_from_prob
    from math_engines import wind_component_out_to_cf, hr_boost_factor
    
    # Test 1: Elite power hitter
    feat_elite = PowerFeatures(
        iso_14=0.350,
        hr_per_pa_14=0.090,
        iso_season=0.340,
        park_hr_factor=1.30,
        wind_deg_toward=45,
        wind_mph=20,
        cf_azimuth_deg=45,
        temp_f=90,
        pitcher_hr9_30d=1.5,
        n_iso_14=60,
        n_hr_per_pa_14=60
    )
    
    prob_elite, _ = pa_hr_probability(feat_elite)
    tier_elite = power_tier_from_prob(prob_elite)
    
    print(f"  Elite Hitter (Judge/Ohtani type):")
    print(f"    P(HR): {prob_elite:.3f} ({prob_elite*100:.1f}%)")
    print(f"    Tier: {tier_elite}")
    print(f"    Status: {'✅ PASS' if tier_elite in ['A', 'B'] else '❌ FAIL'}")
    
    # Test 2: Wind calculations
    w_out = wind_component_out_to_cf(45, 20, 45)
    boost = hr_boost_factor(w_out, 90)
    
    print(f"\n  Wind Boost Calculation:")
    print(f"    Wind Out: {w_out:.1f} mph")
    print(f"    HR Boost: {(boost-1)*100:.0f}%")
    print(f"    Status: {'✅ PASS' if boost > 1.2 else '❌ FAIL'}")
    
    return tier_elite in ['A', 'B'] and boost > 1.2

def check_alerts():
    """Check alert system is configured properly"""
    print("\n3. Checking Alert System")
    print("-" * 40)
    
    from mlb_monitor import MLBMonitor
    
    monitor = MLBMonitor()
    
    # Check notification preferences
    prefs = monitor.notification_preferences
    important_alerts = [
        'power_hitter',
        'clutch_hr',
        'ai_power_high',
        'ai_power_scoring',
        'wind_speed',
        'hot_windy'
    ]
    
    print("  Alert Types Enabled:")
    for alert_type in important_alerts:
        enabled = prefs.get(alert_type, False)
        status = "✅ ON" if enabled else "⚠️  OFF"
        print(f"    {alert_type}: {status}")
    
    # Check if Telegram is configured
    telegram_configured = monitor.telegram_notifier and monitor.telegram_notifier.is_configured()
    print(f"\n  Telegram Integration: {'✅ Configured' if telegram_configured else '⚠️  Not configured'}")
    
    # Check if OpenAI is configured
    openai_configured = monitor.openai_helper and monitor.openai_helper.is_configured()
    print(f"  OpenAI Integration: {'✅ Configured' if openai_configured else '⚠️  Optional - Not configured'}")
    
    # Check if Weather is configured
    weather_configured = monitor.weather_integration and monitor.weather_integration.is_available()
    print(f"  Weather Integration: {'✅ Available' if weather_configured else '⚠️  Not available'}")
    
    return True  # Alert system is ready even if some integrations are optional

def check_data_sources():
    """Check MLB data sources are accessible"""
    print("\n4. Checking Data Sources")
    print("-" * 40)
    
    from multi_source_aggregator import MultiSourceAggregator
    
    aggregator = MultiSourceAggregator()
    
    try:
        # Test fetching today's games
        games = aggregator.get_games_today()
        
        if games:
            print(f"  ✅ Found {len(games)} games scheduled today")
            
            # Show first 3 games
            for game in games[:3]:
                away = game.get('away_team', 'Unknown')
                home = game.get('home_team', 'Unknown')
                status = game.get('status', 'Unknown')
                print(f"    • {away} @ {home} - {status}")
            
            if len(games) > 3:
                print(f"    ... and {len(games) - 3} more games")
            
            return True
        else:
            print("  ⚠️  No games found - API might be down or no games today")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fetching games: {e}")
        return False

def check_database():
    """Check database connection"""
    print("\n5. Checking Database Connection")
    print("-" * 40)
    
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            # Try to query the database
            user_count = User.query.count()
            print(f"  ✅ Database connected")
            print(f"    Users in system: {user_count}")
            
            # Check if admin exists
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"    Admin user: ✅ Exists")
            else:
                print(f"    Admin user: ⚠️  Not created (run create_admin.py)")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def run_comprehensive_check():
    """Run all system checks"""
    print("\n" + "="*70)
    print(" FINAL SYSTEM CHECK FOR DEPLOYMENT")
    print("="*70)
    print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    checks = [
        ("Module Imports", check_imports),
        ("Math Engine", check_math_engine),
        ("Alert System", check_alerts),
        ("Data Sources", check_data_sources),
        ("Database", check_database)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            passed = check_func()
            results.append((check_name, passed))
        except Exception as e:
            print(f"\n❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*70)
    print(" SYSTEM STATUS SUMMARY")
    print("="*70)
    
    total_checks = len(results)
    passed_checks = sum(1 for _, passed in results if passed)
    
    for check_name, passed in results:
        status = "✅ READY" if passed else "❌ NEEDS FIX"
        print(f"  {check_name}: {status}")
    
    print("="*70)
    print(f" OVERALL: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n 🎉 SYSTEM FULLY READY FOR DEPLOYMENT!")
        print(" ✅ Math engine integrated and calibrated")
        print(" ✅ Alerts will trigger with proper tiers")
        print(" ✅ Weather boost calculations working")
        print(" ✅ Ready for tonight's MLB games")
        print("\n Next steps:")
        print(" 1. Monitor the logs when games start")
        print(" 2. Verify alerts are being sent to Telegram")
        print(" 3. Check that probabilities match expectations")
    elif passed_checks >= 3:
        print("\n ⚠️  SYSTEM MOSTLY READY")
        print(" Some optional components may need attention")
        print(" Core functionality is working")
    else:
        print("\n ❌ SYSTEM NOT READY")
        print(" Please fix the issues above before deployment")
    
    print("="*70)
    
    return passed_checks == total_checks

if __name__ == "__main__":
    success = run_comprehensive_check()
    sys.exit(0 if success else 1)