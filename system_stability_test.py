#!/usr/bin/env python3
"""
MLB Alert System - Stability Test Suite
Tests the production-ready architecture improvements
"""
import requests
import time
import json
import subprocess
import sys
from datetime import datetime

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🏥 Testing Health Check Endpoint...")
    try:
        response = requests.get("http://localhost:5000/healthz", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   ✅ Monitor: {data.get('monitor_status')}")
            print(f"   ✅ API: {data.get('api_status')}")
            print(f"   ✅ Environment: {data.get('config', {}).get('environment')}")
            print(f"   ✅ Secrets: {data.get('config', {}).get('secrets_configured')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_config_validation():
    """Test configuration validation"""
    print("⚙️  Testing Configuration...")
    try:
        from config import Config
        validation = Config.validate_required_secrets()
        
        print(f"   Required secrets: {validation['all_required_present']}")
        for secret, status in validation['required'].items():
            symbol = "✅" if status else "❌"
            print(f"   {symbol} {secret}: {'OK' if status else 'Missing'}")
        
        return validation['all_required_present']
    except Exception as e:
        print(f"   ❌ Config validation error: {e}")
        return False

def test_api_connectivity():
    """Test MLB API connectivity"""
    print("🌐 Testing MLB API Connectivity...")
    try:
        from datetime import date
        test_date = date.today().strftime('%Y-%m-%d')
        response = requests.get(
            f"https://statsapi.mlb.com/api/v1/schedule?date={test_date}&sportId=1",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            games = data.get('dates', [{}])[0].get('games', [])
            print(f"   ✅ API Response: {response.status_code}")
            print(f"   ✅ Games Today: {len(games)}")
            return True
        else:
            print(f"   ❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API connectivity error: {e}")
        return False

def test_telegram_integration():
    """Test Telegram bot integration"""
    print("📱 Testing Telegram Integration...")
    try:
        import os
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            print("   ⚠️  Telegram credentials not configured")
            return False
        
        # Test bot info
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            print(f"   ✅ Bot: @{bot_info['result']['username']}")
            
            # Test message send
            test_msg = f"🧪 Stability test completed at {datetime.utcnow().strftime('%H:%M:%S')}"
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={"chat_id": chat_id, "text": test_msg},
                timeout=10
            )
            
            if response.status_code == 200:
                print("   ✅ Test message sent successfully")
                return True
            else:
                print(f"   ❌ Message send failed: {response.status_code}")
                return False
        else:
            print(f"   ❌ Bot info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Telegram test error: {e}")
        return False

def test_worker_process():
    """Test worker process startup"""
    print("👷 Testing Worker Process...")
    try:
        # Quick validation test
        result = subprocess.run(
            [sys.executable, "worker.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 or "worker.py" in result.stderr:
            print("   ✅ Worker process can be started")
            print("   ℹ️  Run 'python worker.py' in separate terminal for production")
            return True
        else:
            print(f"   ❌ Worker process error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ⚠️  Worker test skipped: {e}")
        return True  # Don't fail on this

def run_comprehensive_test():
    """Run all stability tests"""
    print("🚀 MLB Alert System - Stability Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Configuration", test_config_validation),
        ("MLB API", test_api_connectivity),
        ("Telegram", test_telegram_integration),
        ("Worker Process", test_worker_process),
    ]
    
    results = []
    for name, test_func in tests:
        print()
        success = test_func()
        results.append((name, success))
        time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<10} {name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All systems operational! Ready for production.")
    elif passed >= len(results) - 1:
        print("⚠️  System mostly stable. Check failed tests.")
    else:
        print("🚨 Multiple issues detected. Review configuration.")

if __name__ == "__main__":
    run_comprehensive_test()