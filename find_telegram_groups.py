#!/usr/bin/env python3
"""Find Telegram groups for your bot"""

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

def find_all_chats(updates):
    """Extract all chat information from updates"""
    chats = {}
    if updates and updates.get('ok'):
        for update in updates.get('result', []):
            message = update.get('message', {})
            chat = message.get('chat', {})
            
            chat_id = chat.get('id')
            chat_type = chat.get('type', 'private')
            title = chat.get('title') or chat.get('first_name') or chat.get('username') or 'Unknown'
            
            if chat_id and chat_id not in chats:
                chats[chat_id] = {
                    'title': title,
                    'type': chat_type
                }
    
    return chats

def main():
    print("=" * 60)
    print("FINDING TELEGRAM CHATS FOR YOUR BOT")
    print("=" * 60)
    print()
    
    # Check if bot token exists
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        return
    
    print("✅ Bot token found: @chirpbetabot")
    print()
    print("🔍 Fetching recent messages...")
    
    updates = get_updates(bot_token)
    chats = find_all_chats(updates)
    
    if not chats:
        print("\n❌ No chats found yet!")
        print("\n📋 TO SET UP GROUP NOTIFICATIONS:")
        print("-" * 40)
        print("1. Open Telegram and go to @chirpbetabot")
        print("2. Start a chat with /start")
        print("3. Add the bot to your group")
        print("4. Send any message in the group")
        print("5. Run this script again")
        print("\n💡 For existing groups:")
        print("• Remove and re-add the bot")
        print("• Make sure to send a message after adding")
        return
    
    print(f"\n✅ Found {len(chats)} chat(s):")
    print("-" * 40)
    
    groups = []
    private_chats = []
    
    for chat_id, info in chats.items():
        if info['type'] in ['group', 'supergroup']:
            groups.append((chat_id, info))
        else:
            private_chats.append((chat_id, info))
    
    if groups:
        print("\n📢 GROUPS:")
        for chat_id, info in groups:
            print(f"  • {info['title']}")
            print(f"    Chat ID: {chat_id}")
            print(f"    Type: {info['type']}")
    
    if private_chats:
        print("\n👤 PRIVATE CHATS:")
        for chat_id, info in private_chats:
            print(f"  • {info['title']}")
            print(f"    Chat ID: {chat_id}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("-" * 40)
    
    if groups:
        group_id = groups[0][0]  # Use first group found
        print(f"1. Your group chat ID is: {group_id}")
        print(f"2. Add TELEGRAM_CHAT_ID secret with value: {group_id}")
        print(f"3. MLB alerts will be sent to: {groups[0][1]['title']}")
    else:
        print("1. No groups found - add your bot to a group first")
        print("2. Send a message in the group")
        print("3. Run this script again")

if __name__ == "__main__":
    main()