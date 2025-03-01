import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Current time and user for logging
CURRENT_TIME = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
CURRENT_USER = os.getenv('USER', 'aptdnfapt')

print(f"Loading configuration at {CURRENT_TIME} UTC")
print(f"Configuration loaded by user: {CURRENT_USER}")

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

# API Keys Configuration
API_KEYS = [
    key.strip() 
    for key in os.getenv('GEMINI_API_KEYS', '').split(',') 
    if key.strip()
]
if not API_KEYS:
    raise ValueError("No API keys found in .env file. Please add GEMINI_API_KEYS.")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', "sqlite:///bot_data.db")

# Bot Configuration
DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
MAX_HISTORY_LENGTH = int(os.getenv('MAX_HISTORY_LENGTH', '10'))
DEFAULT_CHANNEL_ID = None

# Advanced Configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
def validate_config():
    """Validate the configuration values"""
    errors = []
    
    # Validate Discord Token
    if not DISCORD_TOKEN or len(DISCORD_TOKEN) < 50:
        errors.append("Invalid DISCORD_TOKEN")
    
    # Validate API Keys
    if not API_KEYS:
        errors.append("No API keys provided")
    for key in API_KEYS:
        if len(key) < 20:  # Basic length check for API keys
            errors.append(f"Invalid API key format: {key[:6]}...")
    
    # Validate temperature
    if not (0.0 <= DEFAULT_TEMPERATURE <= 1.0):
        errors.append(f"Invalid DEFAULT_TEMPERATURE: {DEFAULT_TEMPERATURE}")
    
    # Validate history length
    if MAX_HISTORY_LENGTH < 1:
        errors.append(f"Invalid MAX_HISTORY_LENGTH: {MAX_HISTORY_LENGTH}")
    
    if errors:
        raise ValueError("\n".join(errors))

# Configuration summary
def print_config_summary():
    """Print a summary of the configuration (without sensitive data)"""
    print("\n=== Configuration Summary ===")
    print(f"Timestamp: {CURRENT_TIME} UTC")
    print(f"User: {CURRENT_USER}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Number of API Keys: {len(API_KEYS)}")
    print(f"Default Temperature: {DEFAULT_TEMPERATURE}")
    print(f"Max History Length: {MAX_HISTORY_LENGTH}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print(f"Log Level: {LOG_LEVEL}")
    print("=== End Configuration ===\n")

# Validate and print summary when module is loaded
try:
    validate_config()
    if DEBUG_MODE:
        print_config_summary()
except Exception as e:
    print(f"Configuration Error: {str(e)}")
    raise

if __name__ == "__main__":
    print_config_summary()
