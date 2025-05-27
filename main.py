#!/usr/bin/env python3
"""
Telegram Bot for handling restricted message links
This bot receives restricted message links and sends the content back to users
"""

import os
import re
import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from telethon import TelegramClient, events
from telethon.tl.types import (
    Message, MessageMediaPhoto, MessageMediaDocument, 
    MessageMediaWebPage
)
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    FloodWaitError, ChatAdminRequiredError, ChannelPrivateError,
    MessageNotModifiedError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RestrictedMessageBot:
    def __init__(self):
        # Get credentials from environment variables
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        
        if not all([self.api_id, self.api_hash]):
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        
        # Initialize clients
        self.bot_client = None
        self.user_client = None
        
        # Cache for processed messages
        self.message_cache: Dict[str, Any] = {}
        
    async def initialize_clients(self):
        """Initialize both bot and user clients"""
        try:
            # Initialize bot client
            if self.bot_token:
                self.bot_client = TelegramClient('bot_session', self.api_id, self.api_hash)
                await self.bot_client.start(bot_token=self.bot_token)
                logger.info("Bot client initialized successfully")
            
            # Initialize user client (needed for accessing restricted content)
            if self.phone_number:
                self.user_client = TelegramClient('user_session', self.api_id, self.api_hash)
                await self.user_client.start(phone=self.phone_number)
                logger.info("User client initialized successfully")
            
            if not self.user_client:
                logger.warning("User client not available - some restricted content may not be accessible")
                
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
    
    def parse_telegram_link(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse Telegram message link and extract channel/chat and message ID"""
        try:
            # Pattern for t.me links including thread support
            patterns = [
                r't\.me/c/(-?\d+)/(\d+)(?:/(\d+))?',  # t.me/c/chat_id/message_id or t.me/c/chat_id/thread_id/message_id
                r't\.me/([^/]+)/(\d+)(?:/(\d+))?',  # t.me/channel/message_id or t.me/channel/thread_id/message_id
                r'telegram\.me/([^/]+)/(\d+)(?:/(\d+))?',  # telegram.me/channel/message_id or telegram.me/channel/thread_id/message_id
            ]
            
            for i, pattern in enumerate(patterns):
                match = re.search(pattern, url)
                if match:
                    if i == 0:  # t.me/c/ pattern
                        # Private chat link
                        chat_id = int(match.group(1))
                        if chat_id > 0:
                            chat_id = int(f"-100{chat_id}")
                        
                        # Check if it's a threaded message (3 groups) or regular message (2 groups)
                        if match.group(3):  # threaded message: chat_id/thread_id/message_id
                            message_id = int(match.group(3))
                            thread_id = int(match.group(2))
                        else:  # regular message: chat_id/message_id
                            message_id = int(match.group(2))
                            thread_id = None
                    else:
                        # Public channel link
                        chat_id = match.group(1)
                        
                        # Check if it's a threaded message
                        if match.group(3):  # threaded message: channel/thread_id/message_id
                            message_id = int(match.group(3))
                            thread_id = int(match.group(2))
                        else:  # regular message: channel/message_id
                            message_id = int(match.group(2))
                            thread_id = None
                    
                    result = {
                        'chat_id': chat_id,
                        'message_id': message_id,
                        'original_url': url
                    }
                    
                    if thread_id:
                        result['thread_id'] = thread_id
                    
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Telegram link: {e}")
            return None
    
    async def get_message_content(self, chat_id, message_id: int) -> Optional[Message]:
        """Fetch message content from Telegram"""
        try:
            # Try with user client first (can access restricted content)
            if self.user_client:
                try:
                    entity = await self.user_client.get_entity(chat_id)
                    message = await self.user_client.get_messages(entity, ids=message_id)
                    if message and not isinstance(message, list):
                        return message
                    elif isinstance(message, list) and message:
                        return message[0]
                except (ChannelPrivateError, ChatAdminRequiredError) as e:
                    logger.warning(f"User client couldn't access {chat_id}: {e}")
            
            # Fallback to bot client
            if self.bot_client:
                try:
                    entity = await self.bot_client.get_entity(chat_id)
                    message = await self.bot_client.get_messages(entity, ids=message_id)
                    if message and not isinstance(message, list):
                        return message
                    elif isinstance(message, list) and message:
                        return message[0]
                except Exception as e:
                    logger.warning(f"Bot client couldn't access {chat_id}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching message content: {e}")
            return None
    
    async def format_message_content(self, message: Message) -> Dict[str, Any]:
        """Format message content for sending"""
        try:
            result = {
                'text': '',
                'media': None,
                'media_type': None,
                'caption': '',
                'file_name': None
            }
            
            # Get message text
            if message.text:
                result['text'] = message.text
            
            # Handle media
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    result['media'] = message.media.photo
                    result['media_type'] = 'photo'
                    result['caption'] = message.text or ''
                    
                elif isinstance(message.media, MessageMediaDocument):
                    doc = message.media.document
                    result['media'] = doc
                    result['media_type'] = 'document'
                    result['caption'] = message.text or ''
                    
                    # Try to get filename
                    for attr in doc.attributes:
                        if hasattr(attr, 'file_name'):
                            result['file_name'] = attr.file_name
                            break
                    
                    # Check if it's a video, audio, etc.
                    if doc.mime_type:
                        if doc.mime_type.startswith('video/'):
                            result['media_type'] = 'video'
                        elif doc.mime_type.startswith('audio/'):
                            result['media_type'] = 'audio'
                

                
                elif isinstance(message.media, MessageMediaWebPage):
                    # Handle web page previews
                    webpage = message.media.webpage
                    if hasattr(webpage, 'title') and webpage.title:
                        result['text'] += f"\n\n🔗 {webpage.title}"
                    if hasattr(webpage, 'description') and webpage.description:
                        result['text'] += f"\n{webpage.description}"
                    if hasattr(webpage, 'url') and webpage.url:
                        result['text'] += f"\n{webpage.url}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting message content: {e}")
            return {'text': 'Error processing message content', 'media': None}
    
    async def send_content_to_user(self, chat_id: int, content: Dict[str, Any], original_url: str, reply_to_msg_id: int = None, sender_id: int = None):
        """Send the fetched content back to the user"""
        try:
            if not self.bot_client:
                logger.error("Bot client not available")
                return
            
            # Prepare header message with user tag if sender_id is provided
            header = ""
            
            # Send media if available
            if content.get('media') and content.get('media_type'):
                media_caption = header
                if content.get('caption'):
                    media_caption += content['caption']
                elif content.get('text'):
                    media_caption += content['text']
                
                # Limit caption length (Telegram limit is 1024 characters)
                if len(media_caption) > 1000:
                    media_caption = media_caption[:997] + "..."
                
                try:
                    if content['media_type'] == 'photo':
                        await self.bot_client.send_file(
                            chat_id, 
                            content['media'],
                            caption=media_caption,
                            parse_mode='markdown',
                            reply_to=reply_to_msg_id
                        )
                    elif content['media_type'] in ['video', 'audio', 'document']:
                        await self.bot_client.send_file(
                            chat_id,
                            content['media'],
                            caption=media_caption,
                            parse_mode='markdown',
                            reply_to=reply_to_msg_id
                        )
                except Exception as e:
                    logger.error(f"Error sending media: {e}")
                    # Fallback to text only
                    await self.bot_client.send_message(
                        chat_id,
                        f"{header}❌ Media could not be sent, but here's the text:\n\n{content.get('text', 'No text content')}",
                        parse_mode='markdown',
                        reply_to=reply_to_msg_id
                    )
            
            # Send text content if no media or as additional message
            elif content.get('text'):
                full_text = header + content['text']
                
                # Split long messages
                if len(full_text) > 4000:
                    await self.bot_client.send_message(chat_id, header, parse_mode='markdown', reply_to=reply_to_msg_id)
                    
                    # Split text into chunks
                    text_chunks = [content['text'][i:i+4000] for i in range(0, len(content['text']), 4000)]
                    for chunk in text_chunks:
                        await self.bot_client.send_message(chat_id, chunk, reply_to=reply_to_msg_id)
                else:
                    await self.bot_client.send_message(chat_id, full_text, parse_mode='markdown', reply_to=reply_to_msg_id)
            
            else:
                await self.bot_client.send_message(
                    chat_id,
                    f"{header}❌ No content found in the message.",
                    parse_mode='markdown',
                    reply_to=reply_to_msg_id
                )
                
        except Exception as e:
            logger.error(f"Error sending content to user: {e}")
            try:
                await self.bot_client.send_message(
                    chat_id,
                    f"❌ Error processing your request: {str(e)}",
                    reply_to=reply_to_msg_id
                )
            except:
                pass
    
    async def handle_message(self, event):
        """Handle incoming messages"""
        try:
            message_text = event.message.text
            chat_id = event.chat_id
            original_msg_id = event.message.id
            sender_id = event.sender_id
            
            # Only process messages that contain Telegram links using regex
            telegram_link_pattern = r'https?://(?:t\.me|telegram\.me)/[^\s]+'
            telegram_links = re.findall(telegram_link_pattern, message_text)
            
            # If no Telegram links found, ignore the message silently
            if not telegram_links:
                return
            
            # Process each link
            for link in telegram_links:
                processing_msg = await event.reply("🔄 Processing your request...")
                
                try:
                    # Parse the link
                    parsed = self.parse_telegram_link(link)
                    if not parsed:
                        await processing_msg.edit(f"❌ Invalid Telegram link format: {link}")
                        continue
                    
                    # Check cache first
                    cache_key = f"{parsed['chat_id']}_{parsed['message_id']}"
                    if cache_key in self.message_cache:
                        logger.info(f"Using cached content for {cache_key}")
                        content = self.message_cache[cache_key]
                    else:
                        # Fetch message content
                        message = await self.get_message_content(parsed['chat_id'], parsed['message_id'])
                        if not message:
                            await processing_msg.edit(f"❌ Could not access the message. It might be from a private channel or the message doesn't exist.")
                            continue
                        
                        # Format content
                        content = await self.format_message_content(message)
                        
                        # Cache the content
                        self.message_cache[cache_key] = content
                    
                    # Send content to user
                    await self.send_content_to_user(chat_id, content, link, original_msg_id, sender_id)
                    
                    # Delete the processing message after successful send
                    try:
                        await processing_msg.delete()
                    except Exception as delete_error:
                        logger.warning(f"Could not delete processing message: {delete_error}")
                        
                except Exception as process_error:
                    logger.error(f"Error processing link {link}: {process_error}")
                    try:
                        await processing_msg.edit(f"❌ Error processing link: {str(process_error)}")
                    except Exception as edit_error:
                        logger.warning(f"Could not edit processing message: {edit_error}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await event.reply(f"❌ An error occurred: {str(e)}")
            except:
                pass
    
    async def run(self):
        """Main bot runner"""
        try:
            await self.initialize_clients()
            
            if not self.bot_client:
                logger.error("Bot client not available. Please set TELEGRAM_BOT_TOKEN.")
                return
            
            # Set up event handlers
            # Only handle messages that contain Telegram links
            @self.bot_client.on(events.NewMessage(pattern=re.compile(r'.*(?:https?://(?:t\.me|telegram\.me)/[^\s]+).*', re.IGNORECASE)))
            async def message_handler(event):
                await self.handle_message(event)
            
            # Start command handler
            @self.bot_client.on(events.NewMessage(pattern=r'/(?:start|help)'))
            async def start_handler(event):
                welcome_text = """
👋 **Welcome to Restricted Message Bot!**

I can help you access content from restricted Telegram channels.

**How to use:**
1. Send me a Telegram message link (e.g., https://t.me/channel/12345)
2. I'll fetch and send you the content

**Features:**
✅ Access restricted content
✅ Support for text, photos, videos, documents
✅ Handle multiple links at once

**Note:** I need proper permissions to access private channels.

Just send me a link to get started! 🚀

**Supported link formats:**
• https://t.me/channel/message_id
• https://t.me/c/chat_id/message_id
• https://t.me/c/chat_id/thread_id/message_id (threaded messages)
• https://telegram.me/channel/message_id
"""
                await event.reply(welcome_text, parse_mode='markdown')
            
            logger.info("Bot is running...")
            await self.bot_client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            if self.bot_client:
                await self.bot_client.disconnect()
            if self.user_client:
                await self.user_client.disconnect()

def main():
    """Main entry point"""
    # Check for required environment variables
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        print("- TELEGRAM_API_ID: Your Telegram API ID")
        print("- TELEGRAM_API_HASH: Your Telegram API Hash")
        print("- TELEGRAM_BOT_TOKEN: Your bot token (optional, for bot mode)")
        print("- TELEGRAM_PHONE_NUMBER: Your phone number (optional, for user mode)")
        print("\nGet API credentials from: https://my.telegram.org/apps")
        return
    
    try:
        bot = RestrictedMessageBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()