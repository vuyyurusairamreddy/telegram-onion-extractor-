import os
import re
import json
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, errors
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - API credentials hardcoded (replace these with your own)
API_ID = 25262555  # Your API ID
API_HASH = "5224bfadc781602a211184c49a9646a8"  # Your API hash
CHANNEL_USERNAME = 'toronionlinks'  # The channel to monitor
OUTPUT_FILE = 'onion_links.json'
LAST_MESSAGE_ID_FILE = 'last_message_id.txt'

# Regex pattern for .onion URLs
ONION_URL_PATTERN = re.compile(r'https?://[a-zA-Z0-9\-\.]+\.onion\b')


class TelegramOnionExtractor:
    """Class to extract .onion links from Telegram channels"""

    def __init__(self, api_id: str, api_hash: str, channel: str) -> None:
        """Initialize the extractor with API credentials and channel info"""
        if not api_id or not api_hash:
            raise ValueError("API_ID and API_HASH must be provided")

        self.api_id = api_id
        self.api_hash = api_hash
        self.channel = channel
        self.client = TelegramClient('onion_extractor', api_id, api_hash)
        self.last_processed_id = self._load_last_message_id()

    def _load_last_message_id(self) -> Optional[int]:
        """Load the last processed message ID from file if it exists"""
        try:
            if os.path.exists(LAST_MESSAGE_ID_FILE):
                with open(LAST_MESSAGE_ID_FILE, 'r') as f:
                    return int(f.read().strip())
        except (IOError, ValueError) as e:
            logger.warning(f"Error loading last message ID: {e}")
        return None

    def _save_last_message_id(self, message_id: int) -> None:
        """Save the last processed message ID to a file"""
        try:
            with open(LAST_MESSAGE_ID_FILE, 'w') as f:
                f.write(str(message_id))
        except IOError as e:
            logger.error(f"Error saving last message ID: {e}")

    async def extract_links(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Extract .onion links from the specified channel
        
        Args:
            limit: Maximum number of messages to process
            
        Returns:
            List of dictionaries containing link information
        """
        extracted_links = []
        newest_id = None

        try:
            await self.client.start()
            logger.info(f"Connected to Telegram API")
            
            # Get the entity for the channel
            entity = await self.client.get_entity(self.channel)
            
            # Get messages, filtering to start after the last processed ID if available
            kwargs = {'limit': limit}
            if self.last_processed_id:
                kwargs['min_id'] = self.last_processed_id
                
            messages = await self.client.get_messages(entity, **kwargs)
            
            if not messages:
                logger.info(f"No new messages found in channel @{self.channel}")
                return extracted_links
                
            logger.info(f"Processing {len(messages)} messages from @{self.channel}")
            
            # Process messages in reverse order (oldest first)
            for message in reversed(messages):
                if message.id and (newest_id is None or message.id > newest_id):
                    newest_id = message.id
                
                if not message.text:
                    continue
                    
                # Find all .onion links in the message
                matches = ONION_URL_PATTERN.findall(message.text)
                
                for url in matches:
                    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    link_info = {
                        "source": "telegram",
                        "url": url,
                        "discovered_at": current_time,
                        "context": f"Found in Telegram channel @{self.channel}",
                        "status": "pending"
                    }
                    extracted_links.append(link_info)
                    logger.debug(f"Found link: {url}")
            
            # Update the last processed message ID
            if newest_id and (self.last_processed_id is None or newest_id > self.last_processed_id):
                self._save_last_message_id(newest_id)
                logger.info(f"Updated last processed message ID to {newest_id}")
                
        except errors.FloodWaitError as e:
            logger.error(f"Rate limit exceeded. Need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return await self.extract_links(limit)
        except errors.RPCError as e:
            logger.error(f"Telegram API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.client.disconnect()
            
        return extracted_links

    async def save_to_json(self, links: List[Dict[str, Any]]) -> None:
        """Save extracted links to a JSON file (one object per line)"""
        mode = 'a' if os.path.exists(OUTPUT_FILE) else 'w'
        
        try:
            with open(OUTPUT_FILE, mode) as f:
                for link in links:
                    f.write(json.dumps(link) + '\n')
                    
            if links:
                logger.info(f"Saved {len(links)} links to {OUTPUT_FILE}")
            
        except IOError as e:
            logger.error(f"Error writing to file: {e}")


async def main():
    """Main function to run the extractor"""
    try:
        extractor = TelegramOnionExtractor(API_ID, API_HASH, CHANNEL_USERNAME)
        links = await extractor.extract_links()
        await extractor.save_to_json(links)
        logger.info("Extraction completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
