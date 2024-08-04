import discord
import anthropic
import asyncio
import boto3
import logging
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

import os
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "discorg-bot")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "test")
# Set up logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Set up Anthropic client
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Set up DynamoDB client
dynamodb = boto3.resource("dynamodb", "us-east-1")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


async def get_last_summarized_message_id(channel_id):
    logger.info(f"Fetching last summarized message ID for channel {channel_id}")
    response = table.get_item(Key={"channel_id": str(channel_id)})
    item = response.get("Item")
    result = int(item["last_message_id"]) if item else None
    logger.info(f"Last summarized message ID: {result}")
    return result


async def update_last_summarized_message_id(channel_id, message_id):
    logger.info(
        f"Updating last summarized message ID for channel {channel_id} to {message_id}"
    )
    table.put_item(
        Item={"channel_id": str(channel_id), "last_message_id": str(message_id)}
    )


async def check_for_summarize_command(channel_id):
    logger.info(f"Checking for summarize command in channel {channel_id}")
    channel = await client.fetch_channel(channel_id)
    async for message in channel.history(limit=10):
        if message.content.strip().lower() == "!summarize":
            logger.info(f"Summarize command found: {message.id}")
            return message
    logger.info("No summarize command found")
    return None


async def fetch_messages_with_pagination(
    channel, last_message_id, max_messages=1000, time_limit=None
):
    logger.info(
        f"Fetching messages for channel {channel.id}, starting from message {last_message_id}"
    )
    messages = []
    now = datetime.utcnow()

    kwargs = {"limit": 100, "oldest_first": False}

    if last_message_id is not None:
        kwargs["after"] = discord.Object(id=last_message_id)

    while len(messages) < max_messages:
        new_messages = []
        async for message in channel.history(**kwargs):
            new_messages.append(message)
            if len(new_messages) >= 100:
                break

        if not new_messages:
            break

        for msg in new_messages:
            if time_limit and (now - msg.created_at) > time_limit:
                logger.info(f"Time limit reached, stopping at {len(messages)} messages")
                return messages
            messages.append(msg)
            if len(messages) >= max_messages:
                logger.info(f"Max messages reached: {max_messages}")
                return messages

        kwargs["before"] = new_messages[-1].id

    logger.info(f"Fetched {len(messages)} messages")
    return messages


async def summarize_conversation(channel_id, command_message):
    logger.info(f"Summarizing conversation for channel {channel_id}")
    channel = await client.fetch_channel(channel_id)
    last_summarized_id = await get_last_summarized_message_id(channel_id)

    time_limit = timedelta(hours=1)
    messages = await fetch_messages_with_pagination(
        channel, last_summarized_id, max_messages=1000, time_limit=time_limit
    )

    if not messages:
        logger.info("No new messages to summarize")
        await channel.send("No new messages to summarize from the last hour.")
        return

    conversation = "\n".join(
        f"{msg.author.name}: {msg.content}"
        for msg in reversed(messages)
        if msg.id != command_message.id
    )

    max_chunk_size = 12000
    chunks = [
        conversation[i : i + max_chunk_size]
        for i in range(0, len(conversation), max_chunk_size)
    ]

    summaries = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Summarizing chunk {i+1} of {len(chunks)}")
        prompt = f"Please summarize the following Discord conversation:\n\n{chunk}\n\nSummary:"
        response = anthropic_client.completions.create(
            model="claude-2.1",
            prompt=prompt,
            max_tokens_to_sample=500,
        )
        summaries.append(response.completion)

    final_summary = "\n\n".join(summaries)
    logger.info("Sending summary to channel")
    await channel.send(
        f"Here's a summary of the conversation since the last summary:\n\n{final_summary}"
    )

    await update_last_summarized_message_id(channel_id, command_message.id)


async def main(channel_id):
    logger.info(f"Starting main function for channel {channel_id}")
    await client.login(DISCORD_BOT_TOKEN)

    command_message = await check_for_summarize_command(channel_id)
    if command_message:
        await summarize_conversation(channel_id, command_message)
    else:
        logger.info("No summarize command found, ending execution")


def lambda_handler(event, context):
    logger.info("Lambda function invoked")
    channel_id = int(DISCORD_CHANNEL_ID)
    asyncio.get_event_loop().run_until_complete(main(channel_id))
    logger.info("Lambda function execution completed")
    return {"statusCode": 200, "body": "Execution completed"}
