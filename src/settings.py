# Todo, fix the installation. For now, this'll go in main.py. We just want a MVP, not a finished product

import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "discorg-bot")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "test")
