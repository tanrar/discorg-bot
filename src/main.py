import os
import discord
import logging
from discord import app_commands
from discord.ext import commands, tasks
from claude_bot import ClaudeBot
from datetime import datetime, time, timedelta, timezone
import random
from collections import deque
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()

intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

claude_bot = ClaudeBot(os.getenv('ANTHROPIC_API_KEY'))
logger.info("Initialized ClaudeBot with API key")

MONITOR_CHANNEL_ID = int(os.getenv('MONITOR_CHANNEL_ID'))
OUTPUT_CHANNEL_ID = int(os.getenv('OUTPUT_CHANNEL_ID'))
CHAT_BOT_CHANNEL = int(os.getenv('CHAT_BOT_CHANNEL'))
logger.info(f"Monitor Channel ID: {MONITOR_CHANNEL_ID}, Output Channel ID: {OUTPUT_CHANNEL_ID}")

# Add this near the top of the file, after other global variables
MAX_CONTEXT_MESSAGES = 100
context_messages = deque(maxlen=MAX_CONTEXT_MESSAGES)
chatting_enabled = True
current_personality = "obama_discord"

PROMPTS_FILE = 'src/base_prompt.json'

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            return json.load(f)
    logger.warning(f"Prompts file {PROMPTS_FILE} not found. Using empty prompts dictionary.")
    return {}

prompts = load_prompts()

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@bot.tree.command(name="hourly_summary", description="Generate and post an hourly summary")
async def hourly_summary(interaction: discord.Interaction):
    logger.info(f"Hourly summary command invoked by {interaction.user}")
    await interaction.response.defer()
    
    await generate_summary(interaction, timedelta(hours=1), "Hourly")

@bot.tree.command(name="daily_summary", description="Generate and post a daily summary")
async def daily_summary(interaction: discord.Interaction):
    logger.info(f"Daily summary command invoked by {interaction.user}")
    await interaction.response.defer()
    
    await generate_summary(interaction, timedelta(days=1), "Daily")

@bot.tree.command(name="eight_hour_summary", description="Generate and post an 8-hour summary")
async def eight_hour_summary(interaction: discord.Interaction):
    logger.info(f"8-hour summary command invoked by {interaction.user}")
    await interaction.response.defer()
    
    await generate_summary(interaction, timedelta(hours=8), "8-Hour")

@bot.tree.command(name="user_daily_summary", description="Generate a daily summary focused on a specific user")
async def user_daily_summary(interaction: discord.Interaction, user: discord.Member):
    logger.info(f"User daily summary command invoked by {interaction.user} for user {user}")
    await interaction.response.defer()
    
    await generate_user_summary(interaction, user, timedelta(days=1), "Daily")

@bot.tree.command(name="enable_chat", description="Enable bot chatting in the monitored channel")
async def enable_chat(interaction: discord.Interaction):
    global chatting_enabled
    chatting_enabled = True
    logger.info(f"Chatting enabled by {interaction.user}")
    await interaction.response.send_message("Chatting has been enabled. I'll now respond to messages in the monitored channel.")

@bot.tree.command(name="disable_chat", description="Disable bot chatting in the monitored channel")
async def disable_chat(interaction: discord.Interaction):
    global chatting_enabled
    chatting_enabled = False
    logger.info(f"Chatting disabled by {interaction.user}")
    await interaction.response.send_message("Chatting has been disabled. I'll stop responding to messages in the monitored channel.")

@bot.tree.command(name="set_personality", description="Set the bot's personality")
async def set_personality(interaction: discord.Interaction, personality: str):
    global current_personality
    valid_personalities = ["chat", "howard_dean_catgirl", "bane", "botanical_artifice", "darrow_red_rising", "uwu_insult", "darrow_uwu", "obama_discord", "envy_adams"]
    
    if personality.lower() not in valid_personalities:
        await interaction.response.send_message(f"Invalid personality. Choose from: {', '.join(valid_personalities)}")
        return
    
    current_personality = personality.lower()
    logger.info(f"Personality set to {current_personality} by {interaction.user}")
    await interaction.response.send_message(f"Bot personality has been set to: {current_personality}")

async def generate_summary(interaction: discord.Interaction, time_period: timedelta, summary_type: str):
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)
    
    if not monitor_channel or not output_channel:
        logger.error("Couldn't find monitor or output channel.")
        await interaction.followup.send("Error: Couldn't find monitor or output channel.")
        return

    # Get messages from the specified time period
    current_time = datetime.now(timezone.utc)
    start_time = current_time - time_period
    messages = []
    try:
        async for message in monitor_channel.history(after=start_time, limit=None):
            messages.append(message)
    except discord.errors.Forbidden:
        logger.error(f"Bot doesn't have permission to read message history in channel {monitor_channel.name}")
        await interaction.followup.send("Error: Bot doesn't have permission to read message history.")
        return

    logger.info(f"Retrieved {len(messages)} messages from the last {summary_type.lower()} in channel {monitor_channel.name}")
    logger.info(f"Start time: {start_time.isoformat()}, Current time: {current_time.isoformat()}")
    
    if not messages:
        logger.warning(f"No messages found in channel {monitor_channel.name} (ID: {MONITOR_CHANNEL_ID}) after {start_time.isoformat()}")
        await interaction.followup.send(f"No messages were found in the monitored channel (ID: {MONITOR_CHANNEL_ID}) during the last {summary_type.lower()}. Please check the channel ID, bot permissions, and time range.")
        return

    # Generate summary using Claude
    messages_text = "\n".join([f"{m.author.name}: {m.content}" for m in messages])

    if 'summary' not in prompts:
        logger.error("Summary prompt not found in prompts file.")
        await interaction.followup.send("Error: Summary prompt not configured.")
        return

    prompt = prompts['summary'].format(summary_type=summary_type.lower(), messages_text=messages_text)
    logger.debug(f"Sending prompt to Claude: {prompt[:100]}...")
    
    try:
        summary = await claude_bot.generate_response(prompt)
        logger.info(f"Generated {summary_type.lower()} summary using Claude.")
    except AttributeError:
        logger.error("ClaudeBot object does not have generate_response method")
        await interaction.followup.send("Error: Unable to generate summary due to a configuration issue.")
        return
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        await interaction.followup.send("Error: Unable to generate summary. Please try again later.")
        return

    # Post summary to output channel
    await output_channel.send(f"**{summary_type} Summary**\n\n{summary}")
    logger.info(f"Posted {summary_type.lower()} summary to output channel {output_channel.name}")
    await interaction.followup.send(f"{summary_type} summary has been generated and posted.")
    logger.info(f"Notified user {interaction.user} about {summary_type.lower()} summary completion")

async def generate_user_summary(interaction: discord.Interaction, target_user: discord.Member, time_period: timedelta, summary_type: str):
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)
    
    if not monitor_channel or not output_channel:
        logger.error("Couldn't find monitor or output channel.")
        await interaction.followup.send("Error: Couldn't find monitor or output channel.")
        return

    current_time = datetime.now(timezone.utc)
    start_time = current_time - time_period
    all_messages = []
    user_messages = []

    try:
        async for message in monitor_channel.history(after=start_time, limit=None):
            all_messages.append(message)
            if message.author == target_user:
                user_messages.append(message)
    except discord.errors.Forbidden:
        logger.error(f"Bot doesn't have permission to read message history in channel {monitor_channel.name}")
        await interaction.followup.send("Error: Bot doesn't have permission to read message history.")
        return

    logger.info(f"Retrieved {len(all_messages)} total messages and {len(user_messages)} messages from {target_user.name} in the last {summary_type.lower()} in channel {monitor_channel.name}")

    if not user_messages:
        await interaction.followup.send(f"No messages from {target_user.name} were found in the monitored channel during the last {summary_type.lower()}.")
        return

    all_messages_text = "\n".join([f"{m.author.name}: {m.content}" for m in all_messages])
    user_messages_text = "\n".join([f"{m.content}" for m in user_messages])

    if 'user_summary' not in prompts:
        logger.error("User summary prompt not found in prompts file.")
        await interaction.followup.send("Error: User summary prompt not configured.")
        return

    prompt = prompts['user_summary'].format(target_user=target_user.name, summary_type=summary_type.lower(), all_messages_text=all_messages_text, user_messages_text=user_messages_text)

    try:
        summary = await claude_bot.generate_response(prompt)
        logger.info(f"Generated {summary_type.lower()} summary for user {target_user.name} using Claude.")
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        await interaction.followup.send("Error: Unable to generate summary. Please try again later.")
        return

    await output_channel.send(f"**{summary_type} Summary for {target_user.name}**\n\n{summary}")
    logger.info(f"Posted {summary_type.lower()} summary for user {target_user.name} to output channel {output_channel.name}")
    await interaction.followup.send(f"{summary_type} summary for {target_user.name} has been generated and posted.")
    logger.info(f"Notified user {interaction.user} about {summary_type.lower()} summary completion for {target_user.name}")

async def generate_bot_response(message_content, context):
    global current_personality
    
    with open('src/base_prompt.json', 'r') as f:
        prompts = json.load(f)
    
    if current_personality not in prompts:
        logger.error(f"{current_personality} prompt not found in prompts file.")
        return f"Error: {current_personality} prompt not configured."

    prompt = prompts[current_personality].format(context=context, message_content=message_content)

    try:
        response = await claude_bot.generate_response(prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating bot response: {str(e)}")
        return "Oops, my circuits are a bit frazzled. Can you try again?"

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    logger.debug(f"Received message from {message.author} in channel {message.channel.name}")
    await bot.process_commands(message)

    if message.channel.id == CHAT_BOT_CHANNEL:
        context_messages.append(f"{message.author.name}: {message.content}")
        context = "\n".join(list(context_messages))

        if chatting_enabled:
            async with message.channel.typing():
                response = await generate_bot_response(message.content, context)
            await message.channel.send(response)
            logger.info(f"Bot responded to message in chatbot channel from {message.author}")

if __name__ == "__main__":
    logger.info("Starting the bot...")
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))