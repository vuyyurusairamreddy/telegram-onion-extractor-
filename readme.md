# Telegram .onion Link Extractor

This Python script connects to the Telegram API and extracts `.onion` links from specified Telegram channels, saving them to a JSON file. This tool was created for the CodeGrills internship assignment.

---

## Features

- Uses the Telethon library to connect to Telegram API  
- Extracts `.onion` links from Telegram messages using regex  
- Saves links in a structured JSON format  
- Tracks the last processed message to avoid duplicate processing  
- Handles rate limits and errors gracefully  
- Uses `async/await` for efficient processing

---

## Requirements

- Python 3.7+
- Telethon library
- Telegram API credentials

---

## Setup Instructions

1. **Create a Telegram account** if you don't have one  
2. **Get your API credentials**:  
   - Go to [https://my.telegram.org/](https://my.telegram.org/)
   - Log in with your phone number
   - Go to 'API development tools'
   - Create a new application to get your API ID and hash  
3. **Install required packages**:
   ```bash
   pip install telethon
