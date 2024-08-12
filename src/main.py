import os
import discord
from discord.ext import commands, tasks
from claude_bot import ClaudeBot
from datetime import datetime, time, timedelta

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

claude_bot = ClaudeBot(os.getenv('ANTHROPIC_API_KEY'))

MONITOR_CHANNEL_ID = int(os.getenv('MONITOR_CHANNEL_ID'))
OUTPUT_CHANNEL_ID = int(os.getenv('OUTPUT_CHANNEL_ID'))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    update_hourly_summary.start()
    daily_summary.start()

@bot.command()
async def summarize(ctx):
    """Summarize the last 24 hours of conversation in the monitored channel."""
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    summary = await claude_bot.summarize_past_24h(monitor_channel)
    await ctx.send(f"Here's a summary of the last 24 hours in the monitored channel:\n\n{summary}")

@bot.command()
async def hourly_summary(ctx):
    """Get the last hourly summary."""
    if claude_bot.personality["hourly_history"]:
        await ctx.send(f"Here's the last hourly summary:\n\n{claude_bot.personality['hourly_history'][-1]}")
    else:
        await ctx.send("No hourly summary available yet.")

@tasks.loop(hours=1)
async def update_hourly_summary():
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    
    if monitor_channel:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        messages = []
        async for message in monitor_channel.history(after=one_hour_ago):
            messages.append(message)
        
        if messages:
            await claude_bot.monitor_channel(messages)

@tasks.loop(time=time(hour=0))  # Run daily at midnight
async def daily_summary():
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)
    
    if monitor_channel and output_channel:
        summary = await claude_bot.summarize_past_24h(monitor_channel)
        await output_channel.send(f"Daily Summary of Monitored Channel:\n\n{summary}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if bot.user in message.mentions:
        response = await claude_bot.process_message(message, message.channel)
        await message.channel.send(response)

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))