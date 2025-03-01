import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_CHANNEL_ID = None

# API Keys Configuration
API_KEYS = [
    key.strip() 
    for key in os.getenv('GEMINI_API_KEYS', '').split(',') 
    if key.strip()
]

# Database Configuration
DATABASE_URL = "sqlite:///bot_data.db"

# Bot Configuration
DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
MAX_HISTORY_LENGTH = 10

# Validate configuration
if not API_KEYS:
    raise ValueError("No API keys found in .env file. Please add GEMINI_API_KEYS.")
