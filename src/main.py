import discord
import anthropic
import asyncio
import boto3
from boto3.dynamodb.conditions import Key

import settings
# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Set up Anthropic client
anthropic_client = anthropic.Client(settings.ANTHROPIC_API_KEY)

# Set up DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

async def get_last_summarized_message_id(channel_id):
    response = table.get_item(Key={'channel_id': str(channel_id)})
    item = response.get('Item')
    return int(item['last_message_id']) if item else None

async def update_last_summarized_message_id(channel_id, message_id):
    table.put_item(Item={
        'channel_id': str(channel_id),
        'last_message_id': str(message_id)
    })

async def check_for_summarize_command(channel_id):
    channel = await client.fetch_channel(channel_id)
    async for message in channel.history(limit=10):
        if message.content.strip().lower() == '!summarize':
            return message
    return None

async def fetch_messages_with_pagination(channel, last_message_id, max_messages=1000):
    messages = []
    last_id = last_message_id
    while len(messages) < max_messages:
        new_messages = await channel.history(limit=100, after=discord.Object(id=last_id)).flatten()
        if not new_messages:
            break
        messages.extend(new_messages)
        last_id = new_messages[-1].id
    return messages

async def summarize_conversation(channel_id, command_message):
    channel = await client.fetch_channel(channel_id)
    last_summarized_id = await get_last_summarized_message_id(channel_id)
    
    messages = await fetch_messages_with_pagination(channel, last_summarized_id)
    
    if not messages:
        await channel.send("No new messages to summarize since the last summary.")
        return

    conversation = "\n".join(f"{msg.author.name}: {msg.content}" for msg in reversed(messages) if msg.id != command_message.id)
    
    # Split conversation into chunks if it's too long
    max_chunk_size = 12000  # Adjust based on Claude's token limit
    chunks = [conversation[i:i+max_chunk_size] for i in range(0, len(conversation), max_chunk_size)]
    
    summaries = []
    for chunk in chunks:
        prompt = f"Please summarize the following Discord conversation:\n\n{chunk}\n\nSummary:"
        response = anthropic_client.completion(
            model="claude-2.1",
            prompt=prompt,
            max_tokens_to_sample=500,
        )
        summaries.append(response.completion.strip())
    
    final_summary = "\n\n".join(summaries)
    await channel.send(f"Here's a summary of the conversation since the last summary:\n\n{final_summary}")
    
    # Update the last summarized message ID
    await update_last_summarized_message_id(channel_id, command_message.id)

async def main(channel_id):
    await client.login(settings.DISCORD_BOT_TOKEN)
    
    command_message = await check_for_summarize_command(channel_id)
    if command_message:
        await summarize_conversation(channel_id, command_message)

def lambda_handler(event, context):
    channel_id = int(settings.DISCORD_CHANNEL_ID)  # Channel to monitor
    asyncio.get_event_loop().run_until_complete(main(channel_id))
    return {'statusCode': 200, 'body': 'Execution completed'}

