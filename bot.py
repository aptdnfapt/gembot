import discord
from discord.ext import commands
import re
from config import DISCORD_TOKEN, DEFAULT_TEMPERATURE, API_KEYS
from db_handler import DatabaseHandler
from ai_handler import AIHandler
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=['!', '/'], intents=intents)
db = DatabaseHandler()
ai = AIHandler()

# Bot Information Text
BOT_INFO = """
🌟 **Anime Persona Bot** 🌟

This bot is designed to roleplay as an anime character using Google's Gemini AI.

🤖 **Features**:
• AI-Powered Conversations
• Persistent Memory
• Custom Channel Support
• Temperature Control
• Blacklist System

📝 **Commands**:
• !setchannel - Set bot's primary channel
• !settemp <0.0-1.0> - Adjust AI creativity
• !info - Show this message
• !blacklist @user - Block user from using bot
• !whitelist @user - Allow user to use bot
• !keystatus - Check API keys status

Created by: idc.btw(dc)
Last Updated: 2025-03-01
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
    print(f'{bot.user} has connected to Discord!')
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
    await ctx.send(f'Set {ctx.channel.mention} as the primary chat channel!')

@bot.command(name='settemp')
@commands.has_permissions(administrator=True)
async def set_temperature(ctx, temp: float):
    """Set the AI temperature (0.0 to 1.0)"""
    if 0.0 <= temp <= 1.0:
        db.update_temperature(temp)
        await ctx.send(f'Temperature set to {temp}')
    else:
        await ctx.send('Temperature must be between 0.0 and 1.0')

@bot.command(name='blacklist')
@commands.has_permissions(administrator=True)
async def blacklist_user(ctx, user: discord.Member):
    """Blacklist a user from using the bot"""
    if user.guild_permissions.administrator:
        await ctx.send("❌ Cannot blacklist an administrator!")
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
        last_error_str = last_error.strftime("%Y-%m-%d %H:%M:%S") if last_error else
