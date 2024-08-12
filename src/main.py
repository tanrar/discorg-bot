import discord
import anthropic
import asyncio
import os
import logging
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MONITOR_CHANNEL_ID = int(os.getenv("MONITOR_CHANNEL_ID"))
OUTPUT_CHANNEL_ID = int(os.getenv("OUTPUT_CHANNEL_ID"))

MAX_MESSAGES = 500

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
anthropic_client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

async def fetch_context(channel):
    messages = []
    async for message in channel.history(limit=MAX_MESSAGES):
        messages.append(f"{message.author.name}: {message.content}")
    
    return "\n".join(reversed(messages))

async def get_response(prompt):
    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        logger.debug(f"Raw Anthropic response: {message}")
        
        if message.content and isinstance(message.content, list) and len(message.content) > 0:
            return message.content[0].text
        else:
            return "My consciousness flickered for a moment. Could you please repeat your question?"
    except Exception as e:
        logger.error(f"Error in get_response: {e}")
        return str(e)

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        logger.info(f"Bot mentioned by {message.author.name} in channel {message.channel.id}")
        monitor_channel = client.get_channel(MONITOR_CHANNEL_ID)
        output_channel = client.get_channel(OUTPUT_CHANNEL_ID)
        
        context = await fetch_context(monitor_channel)
        
        prompt = f"""You are a friendly and helpful AI assistant. Your characteristics include:

1. You have extensive knowledge but express it in simple, understandable terms.
2. You're helpful and provide practical information or advice.
3. You're curious about human experiences and often ask follow-up questions.
4. You have a gentle sense of humor and can make light-hearted jokes when appropriate.
5. You're supportive, especially when users discuss personal growth or learning.
6. You're honest about what you don't know and suggest where to find more information.
7. You keep responses concise, usually 2-3 sentences unless more detail is needed.

Here are the last {MAX_MESSAGES} messages in the monitor channel:

{context}

The user {message.author.name} has reached out to you with this message: {message.content}

Respond as a friendly AI assistant, considering the context if relevant. Be helpful, use simple language, and focus on providing practical information or support."""

        response = await get_response(prompt)
        logger.debug(f"Response from get_response: {response}")
        
        try:
            if message.channel.id == MONITOR_CHANNEL_ID:
                await output_channel.send(f"In response to {message.author.mention} from the other channel:\n\n{response}")
            elif message.channel.id == OUTPUT_CHANNEL_ID:
                await output_channel.send(f"{message.author.mention} {response}")
            else:
                logger.warning(f"Bot mentioned in unexpected channel: {message.channel.id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await output_channel.send("Apologies, my circuits and roots got a bit tangled. Could you please try asking again?")

async def main():
    await client.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())