#!/usr/bin/env python3
import re

# Test the regex pattern used in the bot
pattern = r'.*(?:https?://(?:t\.me|telegram\.me)/[^\s]+).*'
link_extract_pattern = r'https?://(?:t\.me|telegram\.me)/[^\s]+'

test_messages = [
    'https://t.me/ikan_live/29914',
    'Check this out: https://t.me/channel/12345',
    'Hello world',
    'https://telegram.me/test/456',
    'Multiple links: https://t.me/a/1 and https://t.me/b/2',
    '/start',
    'Random text without links',
    'https://t.me/c/2059632753/17/577843',  # New threaded format
    'https://t.me/c/1234567890/123',        # Regular private chat
]

# Test parsing patterns
parse_patterns = [
    r't\.me/c/(-?\d+)/(\d+)(?:/(\d+))?',   # t.me/c/chat_id/message_id or t.me/c/chat_id/thread_id/message_id
    r't\.me/([^/]+)/(\d+)(?:/(\d+))?',     # t.me/channel/message_id or t.me/channel/thread_id/message_id
    r'telegram\.me/([^/]+)/(\d+)(?:/(\d+))?',  # telegram.me/channel/message_id or telegram.me/channel/thread_id/message_id
]

print('Testing message filtering pattern:')
for msg in test_messages:
    match = re.match(pattern, msg, re.IGNORECASE)
    links = re.findall(link_extract_pattern, msg)
    print(f'Message: "{msg}"')
    print(f'  -> Filter match: {bool(match)}')
    print(f'  -> Links found: {links}')
    
    # Test parsing for each found link
    for link in links:
        print(f'  -> Parsing "{link}":')
        for i, parse_pattern in enumerate(parse_patterns):
            parse_match = re.search(parse_pattern, link)
            if parse_match:
                print(f'    Pattern {i+1} matched: {parse_match.groups()}')
                break
        else:
            print('    No parsing pattern matched')
    print()
