# Telegram Group Notifications Setup

## Overview
Your MLB Monitor can send alerts to a Telegram group instead of direct messages. This allows multiple people to receive game alerts in a shared group chat.

## Quick Setup Steps

### 1. Create Your Telegram Bot
- Open Telegram and search for **@BotFather**
- Send `/newbot` and follow the prompts
- Save the bot token you receive

### 2. Add Bot to Your Group
- Create a new group or use an existing one
- Add your bot as a member to the group
- **Important**: Send at least one message in the group after adding the bot

### 3. Get Your Group Chat ID
Run the helper script:
```bash
python telegram_group_setup.py
```

This script will:
- Find all groups your bot is in
- Show you the group chat IDs
- Send a test message to verify it works

### 4. Configure Secrets
Add these secrets to your Replit project:
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `TELEGRAM_CHAT_ID`: The group chat ID (negative number like -1001234567890)

## Important Notes

### Group Chat IDs
- Regular groups have negative IDs (e.g., -123456789)
- Supergroups have IDs starting with -100 (e.g., -1001234567890)
- Private chats have positive IDs

### Bot Permissions
- For regular groups: Bot just needs to be a member
- For channels/supergroups: Bot may need admin rights
- Bot must have permission to send messages

### Privacy Settings
- In groups with privacy mode enabled, the bot might only see commands directed at it
- Consider making the bot an admin if you have issues

## Troubleshooting

### Bot Not Finding Group
1. Make sure bot is added to the group
2. Send a message in the group after adding the bot
3. Try removing and re-adding the bot
4. For private groups, make the bot an admin

### Messages Not Sending
1. Verify the chat ID is correct (should be negative for groups)
2. Check bot has permission to send messages
3. Ensure bot token and chat ID secrets are set correctly
4. Test with the helper script first

### Finding Chat ID Manually
If the script doesn't work, you can find your chat ID manually:
1. Add bot to group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the `"chat":{"id":` value in the response

## Features
- All MLB alerts will be sent to the group
- Multiple people can receive notifications
- Works with both regular groups and supergroups
- Maintains all existing alert formatting and emojis

## Security
- Never share your bot token publicly
- Group chat IDs are safe to share (they're just identifiers)
- Consider using a dedicated bot for your MLB alerts