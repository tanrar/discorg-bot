import os
import asyncio
import discord
from discord.ext import commands
from claude_bot import ClaudeBot
import logging
import sys
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize ClaudeBot
claude_bot = ClaudeBot(os.getenv('ANTHROPIC_API_KEY'))

# Channel ID
MONITOR_CHANNEL_ID = int(os.getenv('MONITOR_CHANNEL_ID'))

async def count_messages(channel, after):
    count = 0
    last_message_id = None
    while True:
        messages = []
        async for message in channel.history(limit=100, after=after, before=last_message_id and discord.Object(id=last_message_id)):
            messages.append(message)
        count += len(messages)
        if len(messages) < 100:
            break
        last_message_id = messages[-1].id
        logging.info(f"Counted {count} messages so far...")
    return count

async def generate_daily_summary():
    await bot.wait_until_ready()
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    
    if monitor_channel:
        yesterday = datetime.now() - timedelta(days=1)
        logging.info("Counting messages from the past 24 hours...")
        message_count = await count_messages(monitor_channel, yesterday)
        logging.info(f"Total messages in the past 24 hours: {message_count}")

        logging.info("Generating summary...")
        try:
            summary = await asyncio.wait_for(claude_bot.summarize_past_24h(monitor_channel), timeout=300)  # 5 minute timeout
            print("\nDaily Summary of Monitored Channel:")
            print("====================================")
            print(f"Total messages summarized: {message_count}")
            print("------------------------------------")
            print(summary)
            print("====================================")
        except asyncio.TimeoutError:
            logging.error("Summary generation timed out after 5 minutes.")
        except Exception as e:
            logging.error(f"An error occurred while generating the summary: {str(e)}")
    else:
        logging.error("Could not find monitor channel.")
    
    await bot.close()

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    await generate_daily_summary()

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"An error occurred in event {event}: {sys.exc_info()[1]}")

async def main():
    try:
        await bot.start(os.getenv('DISCORD_BOT_TOKEN'))
    except discord.errors.LoginFailure:
        logging.error("Failed to log in. Please check your Discord token.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())