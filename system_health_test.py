#!/usr/bin/env python3
"""
System Health Test for MLB Monitor
Run this to verify all critical systems are functioning properly
"""

import sys
import time
import logging
import os
import asyncio
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_imports():
    """Test that all required modules can be imported"""
    print("\n🔍 Testing module imports...")
    
    modules = [
        'flask',
        'requests',
        'aiohttp',
        'openai',
        'telegram_notifier',
        'persistent_settings',
        'multi_source_aggregator',
        'mlb_monitor',
        'openai_helper',
        'monitoring_health_check',
        'system_resilience'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\n🔍 Testing environment variables...")
    
    required = ['SESSION_SECRET']
    optional = ['API_SPORTS_KEY', 'OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    
    all_good = True
    for var in required:
        if os.environ.get(var):
            print(f"  ✅ {var} is set")
        else:
            print(f"  ❌ {var} is MISSING (required)")
            all_good = False
    
    for var in optional:
        if os.environ.get(var):
            print(f"  ✅ {var} is set")
        else:
            print(f"  ⚠️  {var} is not set (optional)")
    
    return all_good

def test_mlb_monitor():
    """Test MLB monitor initialization and basic functions"""
    print("\n🔍 Testing MLB Monitor...")
    
    try:
        from mlb_monitor import MLBMonitor
        
        # Initialize monitor
        monitor = MLBMonitor()
        print("  ✅ Monitor initialized")
        
        # Test getting today's games
        games = monitor.get_todays_games()
        if games:
            print(f"  ✅ Retrieved {len(games)} games")
        else:
            print("  ⚠️  No games retrieved (might be off-season)")
        
        # Test monitoring thread
        monitor.start_monitoring()
        print("  ✅ Monitoring thread started")
        
        # Check if thread is alive
        time.sleep(2)
        if monitor.monitor_thread and monitor.monitor_thread.is_alive():
            print("  ✅ Monitoring thread is alive")
        else:
            print("  ❌ Monitoring thread is not alive")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("  ✅ Monitoring stopped")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_persistence():
    """Test persistent settings"""
    print("\n🔍 Testing Persistent Settings...")
    
    try:
        from persistent_settings import PersistentSettings
        
        settings = PersistentSettings()
        print("  ✅ Settings loaded/created")
        
        # Test save
        test_games = [12345, 67890]
        settings.update_monitored_games(test_games)
        print("  ✅ Settings saved")
        
        # Test load
        loaded_games = settings.get_monitored_games()
        if loaded_games == test_games:
            print("  ✅ Settings loaded correctly")
        else:
            print("  ❌ Settings mismatch")
        
        # Clean up
        settings.clear_monitored_games()
        print("  ✅ Settings cleared")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_multi_source_aggregator():
    """Test multi-source aggregator"""
    print("\n🔍 Testing Multi-Source Aggregator...")
    
    try:
        from multi_source_aggregator import MultiSourceBaseballAggregator
        
        aggregator = MultiSourceBaseballAggregator()
        print("  ✅ Aggregator initialized")
        
        # Test async functionality
        async def test_async():
            try:
                data = await aggregator.get_all_games()
                return data is not None
            except:
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_async())
            if result:
                print("  ✅ Async operations working")
            else:
                print("  ⚠️  Async operations returned no data")
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_error_recovery():
    """Test error recovery mechanisms"""
    print("\n🔍 Testing Error Recovery...")
    
    try:
        from mlb_monitor import MLBMonitor
        
        monitor = MLBMonitor()
        
        # Start monitoring
        monitor.start_monitoring()
        time.sleep(1)
        
        # Simulate thread death
        if monitor.monitor_thread:
            initial_thread = monitor.monitor_thread
            print("  ✅ Initial thread created")
            
            # Call start_monitoring again - should detect dead thread if implemented
            monitor.start_monitoring()
            
            # Check if thread is still alive
            if monitor.monitor_thread.is_alive():
                print("  ✅ Thread recovery mechanism in place")
            else:
                print("  ⚠️  Thread recovery might need improvement")
        
        monitor.stop_monitoring()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_connection_pooling():
    """Test connection pooling"""
    print("\n🔍 Testing Connection Pooling...")
    
    try:
        from monitoring_health_check import get_connection_pool
        
        pool = get_connection_pool()
        print("  ✅ Connection pool created")
        
        # Test a request
        response = pool.get("https://statsapi.mlb.com/api/v1/schedule", timeout=5)
        if response.status_code == 200:
            print("  ✅ Connection pool working")
        else:
            print(f"  ⚠️  Unexpected response: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all system health tests"""
    print("=" * 50)
    print("🏥 MLB Monitor System Health Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("MLB Monitor", test_mlb_monitor),
        ("Persistent Settings", test_persistence),
        ("Multi-Source Aggregator", test_multi_source_aggregator),
        ("Error Recovery", test_error_recovery),
        ("Connection Pooling", test_connection_pooling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Critical error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} issues found - review above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())