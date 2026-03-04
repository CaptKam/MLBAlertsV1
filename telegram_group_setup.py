#!/usr/bin/env python3
"""
Telegram Group Setup Helper for MLB Monitor
============================================
This script helps you configure Telegram notifications to send to a group.
"""

import os
import requests
import json

def get_updates(bot_token):
    """Get recent updates from Telegram to find group chat IDs"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def find_group_chats(updates):
    """Extract group chat information from updates"""
    groups = {}
    if updates and updates.get('ok'):
        for update in updates.get('result', []):
            message = update.get('message', {})
            chat = message.get('chat', {})
            
            # Check if it's a group or supergroup
            if chat.get('type') in ['group', 'supergroup']:
                chat_id = chat.get('id')
                title = chat.get('title', 'Unknown Group')
                if chat_id and chat_id not in groups:
                    groups[chat_id] = title
    
    return groups

def test_group_message(bot_token, chat_id):
    """Send a test message to the group"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': '⚾ MLB Monitor Test Message\nYour group is now configured to receive MLB alerts!',
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print("=" * 60)
    print("TELEGRAM GROUP SETUP FOR MLB MONITOR")
    print("=" * 60)
    print()
    
    # Check if bot token exists
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        print("\nTo set up Telegram group notifications:")
        print("1. Create a bot using @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Add it as a secret named TELEGRAM_BOT_TOKEN")
        return
    
    print("✅ Bot token found")
    print("\n📋 SETUP INSTRUCTIONS:")
    print("-" * 40)
    print("1. Add your bot to the Telegram group")
    print("2. Send a message in the group (any message)")
    print("3. Run this script to find your group ID")
    print()
    
    input("Press Enter after completing steps 1-2...")
    
    print("\n🔍 Searching for groups...")
    updates = get_updates(bot_token)
    groups = find_group_chats(updates)
    
    if not groups:
        print("\n❌ No groups found!")
        print("\nTroubleshooting:")
        print("• Make sure the bot is added to your group")
        print("• Send a message in the group")
        print("• Try removing and re-adding the bot")
        print("• For private groups, make the bot an admin")
        return
    
    print(f"\n✅ Found {len(groups)} group(s):")
    print("-" * 40)
    for chat_id, title in groups.items():
        print(f"Group: {title}")
        print(f"Chat ID: {chat_id}")
        print()
    
    # If only one group, use it
    if len(groups) == 1:
        chat_id = list(groups.keys())[0]
        title = groups[chat_id]
    else:
        # Let user choose
        chat_id = input("Enter the Chat ID for the group you want to use: ").strip()
        if not chat_id or int(chat_id) not in groups:
            print("Invalid selection")
            return
        chat_id = int(chat_id)
        title = groups[chat_id]
    
    print(f"\n📨 Testing message to '{title}'...")
    if test_group_message(bot_token, chat_id):
        print("✅ Test message sent successfully!")
        print("\n🎯 NEXT STEPS:")
        print("-" * 40)
        print(f"1. Add TELEGRAM_CHAT_ID as a secret with value: {chat_id}")
        print("2. Your MLB alerts will now go to the group!")
        print("\n💡 GROUP CHAT IDs:")
        print("• Groups have negative IDs (like -123456789)")
        print("• Supergroups have IDs starting with -100 (like -1001234567890)")
        print("• Your group ID:", chat_id)
    else:
        print("❌ Failed to send test message")
        print("Make sure the bot has permission to send messages in the group")

if __name__ == "__main__":
    main()