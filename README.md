# Discord Summarization and Chat Bot

This bot summarizes conversations in a Discord channel and can engage in chat interactions using the Anthropic API. It's designed to run as a standalone Python application.

## Features

- Monitors a specified Discord channel
- Generates hourly, 8-hour, and daily summaries of conversations
- Creates user-specific daily summaries
- Engages in chat interactions with customizable personalities, including:
  - Default chat
- Uses Anthropic's Claude model for summarization and chat responses
- Maintains context memory for more coherent conversations

## Available Commands

- `/hourly_summary`: Generate and post an hourly summary
- `/daily_summary`: Generate and post a daily summary
- `/eight_hour_summary`: Generate and post an 8-hour summary
- `/user_daily_summary`: Generate a daily summary focused on a specific user
- `/enable_chat`: Enable bot chatting in the monitored channel
- `/disable_chat`: Disable bot chatting in the monitored channel
- `/set_personality`: Set the bot's personality (e.g., Harry from Disco Elysium)
- `/clear_memory`: Clear the bot's memory of recent messages
- `/help`: Display a list of available commands and their descriptions

## How It Works

1. The bot connects to Discord and monitors the specified channel
2. It responds to various slash commands for generating summaries and managing its behavior
3. When chatting is enabled, it can respond to messages using the selected personality
4. Summaries and chat responses are generated using Anthropic's API
5. Summaries are posted in a designated output channel

## Prerequisites

- Python 3.8+
- A Discord bot token
- An Anthropic API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/discord-summarization-chat-bot.git
   cd discord-summarization-chat-bot
   ```

2. Install dependencies using pipenv:
   ```
   pipenv install
   ```

3. Set up your environment variables (Discord token, Anthropic API key, etc.)

4. Run the bot:
   ```
   pipenv run python src/main.py
   ```

For more detailed setup instructions, please refer to the documentation.

## Development

This project uses `pipenv` for dependency management. To add new dependencies:

```
pipenv install package_name
```

To update dependencies:

```
pipenv update
```

## Deployment

While this bot is designed to run as a standalone application, you can modify it to run on cloud platforms like AWS Lambda. A deployment script (`deployment.ps1`) is provided for creating a deployment package, which can be useful if you decide to deploy to a cloud environment in the future.

## Logging

The bot uses Python's built-in logging module to log important events and errors. Logs are printed to the console and can be redirected to a file if needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.