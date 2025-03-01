import discord
from discord.ext import commands
import re
from config import DISCORD_TOKEN, DEFAULT_TEMPERATURE, API_KEYS
from db_handler import DatabaseHandler
from ai_handler import AIHandler
import os
from datetime import datetime

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=['!', '/'], intents=intents)
db = DatabaseHandler()
ai = AIHandler()

# Bot Information Text
BOT_INFO = f"""
🌟 **Anime Persona Bot** 🌟

This bot is designed to roleplay as an anime character using Google's Gemini AI.

🤖 **Features**:
• AI-Powered Conversations with Multiple API Keys
• Persistent Memory via Database
• Custom Channel Support
• Temperature Control
• Blacklist System
• Name Mention Detection

📝 **Commands**:
• !setchannel - Set bot's primary channel
• !settemp <0.0-1.0> - Adjust AI creativity
• !info - Show this message
• !blacklist @user - Block user from using bot
• !whitelist @user - Allow user to use bot
• !keystatus - Check API keys status

Created by: {os.getenv('USER', 'aptdnfapt')}
Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

def load_persona_prompt():
    """Load the persona prompt from prompt.txt file"""
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Warning: prompt.txt not found! Creating with default prompt...")
        default_prompt = """You are a friendly anime character. Your responses should be:
1. In character and consistent
2. Family-friendly and appropriate
3. Engaging and interactive
4. Written in a natural conversational style"""
        with open('prompt.txt', 'w', encoding='utf-8') as file:
            file.write(default_prompt)
        return default_prompt

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    print(f'Bot connected as: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Connected to {len(bot.guilds)} servers')
    print(f'Started at: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print('------')
    
    # Initialize settings if not exist
    settings = db.get_settings()
    if not settings.temperature:
        db.update_temperature(DEFAULT_TEMPERATURE)

@bot.command(name='info')
async def show_info(ctx):
    """Display bot information"""
    await ctx.send(BOT_INFO)

@bot.command(name='setchannel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx):
    """Set the current channel as the bot's primary chat channel"""
    db.set_channel(str(ctx.guild.id), str(ctx.channel.id))
    await ctx.send(f'✅ Set {ctx.channel.mention} as the primary chat channel!')

@bot.command(name='settemp')
@commands.has_permissions(administrator=True)
async def set_temperature(ctx, temp: float):
    """Set the AI temperature (0.0 to 1.0)"""
    try:
        temp = float(temp)
        if 0.0 <= temp <= 1.0:
            db.update_temperature(temp)
            await ctx.send(f'✅ Temperature set to {temp}')
        else:
            await ctx.send('❌ Temperature must be between 0.0 and 1.0')
    except ValueError:
        await ctx.send('❌ Please provide a valid number between 0.0 and 1.0')

@bot.command(name='blacklist')
@commands.has_permissions(administrator=True)
async def blacklist_user(ctx, user: discord.Member):
    """Blacklist a user from using the bot"""
    if user.guild_permissions.administrator:
        await ctx.send("❌ Cannot blacklist an administrator!")
        return
    
    if user.id == ctx.author.id:
        await ctx.send("❌ You cannot blacklist yourself!")
        return
    
    db.set_user_access(str(user.id), True, str(ctx.author.id))
    await ctx.send(f"✅ User {user.mention} has been blacklisted from using the bot.")

@bot.command(name='whitelist')
@commands.has_permissions(administrator=True)
async def whitelist_user(ctx, user: discord.Member):
    """Remove a user from the blacklist"""
    db.set_user_access(str(user.id), False, str(ctx.author.id))
    await ctx.send(f"✅ User {user.mention} has been whitelisted and can now use the bot.")

@bot.command(name='keystatus')
@commands.has_permissions(administrator=True)
async def show_key_status(ctx):
    """Show the status of all API keys"""
    status_message = "**API Keys Status**\n\n"
    for i, key in enumerate(API_KEYS, 1):
        masked_key = f"{key[:6]}...{key[-4:]}"
        errors = ai.key_status[key]["errors"]
        last_error = ai.key_status[key]["last_error"]
        last_error_str = last_error.strftime("%Y-%m-%d %H:%M:%S") if last_error else "Never"
        
        status_message += f"Key {i}:\n"
        status_message += f"- Masked Key: {masked_key}\n"
        status_message += f"- Errors: {errors}\n"
        status_message += f"- Last Error: {last_error_str}\n\n"
    
    await ctx.send(status_message)

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)
    
    # Check if user is blacklisted
    if db.is_user_blacklisted(str(message.author.id)):
        return
    
    settings = db.get_settings()
    channel_id = db.get_channel(str(message.guild.id))
    
    # Check if message is in the designated channel or mentions the bot
    bot_name = bot.user.name.lower()
    if (channel_id and str(message.channel.id) == channel_id) or \
       (bot_name in message.content.lower()):
        try:
            # Get chat history
            history = db.get_chat_history(str(message.author.id))
            history_formatted = [
                {"role": "user" if i % 2 == 0 else "assistant",
                 "content": h.message if i % 2 == 0 else h.response}
                for i, h in enumerate(reversed(history))
            ]
            
            # Load persona prompt from file
            persona_prompt = load_persona_prompt()
            
            # Create chat instance with current settings
            chat = ai.create_chat(
                persona_prompt,
                settings.temperature or DEFAULT_TEMPERATURE
            )
            
            # Generate response
            response = ai.generate_response(chat, message.content, history_formatted)
            
            # Store in database
            db.add_chat_history(str(message.author.id), message.content, response)
            
            # Send response
            await message.channel.send(response)
            
        except Exception as e:
            error_message = f"❌ An error occurred: {str(e)}"
            print(error_message)
            await message.channel.send(error_message)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument! Please check the command usage.")
    else:
        print(f"Error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Run the bot
if __name__ == "__main__":
    try:
        print("Starting bot...")
        print(f"Current time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Running as: {os.getenv('USER', 'aptdnfapt')}")
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")
