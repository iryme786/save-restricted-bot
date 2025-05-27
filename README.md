# Restricted Message Bot

A Python Telegram bot that can access and forward content from restricted Telegram channels. The bot receives message links from users and sends back the actual content, bypassing copy/forward restrictions.

## Features

- ✅ Access content from restricted Telegram channels
- ✅ Support for text messages, photos, videos, documents, and audio
- ✅ Handle multiple links in a single message
- ✅ Caching to improve performance
- ✅ Proper error handling and logging
- ✅ Support for both public and private channels
- ✅ Bot mode and user mode support

## Setup Instructions

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your Telegram account
3. Create a new application
4. Note down your `API ID` and `API Hash`

### 2. Create a Telegram Bot (Optional but Recommended)

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Choose a name and username for your bot
4. Note down the bot token

### 3. Install Dependencies

```bash
cd /root/save-restricted-bot
pip3 install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example configuration
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

Fill in your credentials:
```bash
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_PHONE_NUMBER=+1234567890
```

### 5. Run the Bot

```bash
# Load environment variables and run
source .env && python3 main.py
```

Or export variables manually:
```bash
export TELEGRAM_API_ID=12345678
export TELEGRAM_API_HASH=your_api_hash_here
export TELEGRAM_BOT_TOKEN=your_bot_token_here
export TELEGRAM_PHONE_NUMBER=+1234567890

python3 main.py
```

## Usage

1. Start a conversation with your bot
2. Send `/start` to see the welcome message
3. Send any Telegram message link, for example:
   - `https://t.me/ikan_live/29914`
   - `https://t.me/c/1234567890/123`

The bot will fetch and send back the content from those links.

## How It Works

The bot uses two modes:

1. **Bot Mode**: Uses the bot token to interact with users
2. **User Mode**: Uses your user account to access restricted content

The user client is essential for accessing content from channels that restrict copying/forwarding, as it can access content that bots normally cannot.

## Supported Link Formats

- `https://t.me/channel_name/message_id`
- `https://t.me/c/chat_id/message_id`
- `https://telegram.me/channel_name/message_id`

## Content Types Supported

- Text messages
- Photos with captions
- Videos with captions
- Audio files
- Documents
- Web page previews

## Security Notes

- Keep your API credentials secure
- Don't share your session files
- The bot respects Telegram's rate limits
- Only access content you have permission to view

## Troubleshooting

### "Could not access the message"
- The channel might be private and you don't have access
- The message might have been deleted
- Check if your user account has access to the channel

### "Bot client not available"
- Make sure `TELEGRAM_BOT_TOKEN` is set correctly
- Verify the bot token with @BotFather

### "User client couldn't access"
- Make sure `TELEGRAM_PHONE_NUMBER` is set correctly
- You might need to complete 2FA if enabled
- Join the channel with your user account first

## License

This project is for educational purposes. Please respect Telegram's Terms of Service and only access content you have permission to view.
