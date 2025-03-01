# Discord Anime Persona Bot

A Discord bot that role-plays as an anime character using Google's Gemini AI with multiple API key support and persistent chat history.

## Features

- 🤖 Multi-API key support with automatic fallback
- 💭 Persistent chat history via SQLite database
- 🎭 Customizable character persona via prompt.txt
- 🎮 Dedicated channel support
- 🌡️ Adjustable AI temperature
- 🛡️ User blacklist system
- 📝 Name mention detection

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```plaintext
DISCORD_TOKEN=your_discord_token_here
GEMINI_API_KEYS=key1,key2,key3,key4
DEFAULT_TEMPERATURE=0.7
```

4. Customize the persona in `prompt.txt`

5. Run the bot:
```bash
python bot.py
```

## Commands

- `!setchannel` - Set the current channel as bot's primary chat channel
- `!settemp <0.0-1.0>` - Adjust AI temperature
- `!info` - Display bot information
- `!blacklist @user` - Block user from using bot
- `!whitelist @user` - Allow user to use bot
- `!keystatus` - Check API keys status

## File Structure

```
discord-anime-persona-bot/
├── .env                # Environment variables
├── config.py          # Configuration settings
├── models.py          # Database models
├── db_handler.py      # Database operations
├── ai_handler.py      # AI and API handling
├── bot.py            # Main bot file
├── prompt.txt        # Persona configuration
├── requirements.txt  # Dependencies
└── README.md         # Documentation
```

## Configuration

### API Keys
Add multiple API keys in `.env` file as comma-separated values:
```plaintext
GEMINI_API_KEYS=key1,key2,key3,key4
```

### Persona
Edit `prompt.txt` to customize the bot's personality and behavior.

### Database
Uses SQLite by default. Database file will be created automatically as `bot_data.db`.

## Error Handling

- Automatic API key rotation on errors
- Cool-down period for failed keys (1 hour)
- Load balancing across multiple keys
- Persistent error tracking

## Security

- API keys stored in .env file
- Admin-only commands for sensitive operations
- User blacklist system
- Content filtering via Gemini API

## Support

Created by: aptdnfapt
Last Updated: 2025-03-01

## License

MIT License
