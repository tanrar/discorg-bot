# Discord Summarization Bot

This bot summarizes conversations in a Discord channel using the Anthropic API. It's designed to run on AWS Lambda but can also be run locally for testing purposes.

## Features

- Monitors a specified Discord channel for the `!summarize` command
- Retrieves recent messages (up to 1 hour old)
- Uses Anthropic's Claude model to generate a summary
- Stores the last summarized message ID in DynamoDB
- Can be run locally or deployed to AWS Lambda

## How It Works

1. The bot checks for a `!summarize` command in the specified channel
2. If found, it fetches messages since the last summarization (or up to 1 hour old)
3. Messages are sent to Anthropic's API for summarization
4. The summary is posted back to the Discord channel
5. The last summarized message ID is updated in DynamoDB

## Prerequisites

- Python 3.8+
- A Discord bot token
- An Anthropic API key
- AWS credentials configured (for DynamoDB access and Lambda deployment)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/discord-summarization-bot.git
   cd discord-summarization-bot
   ```

2. Install dependencies using pipenv:
   ```
   pipenv install
   ```

3. Create a `.env` file in the project root with the following content:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DYNAMODB_TABLE_NAME=your_dynamodb_table_name
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id
   ```

## Running Locally

To run the bot locally for testing:

1. Activate the pipenv shell:
   ```
   pipenv shell
   ```

2. Run the script:
   ```
   python main.py
   ```

The bot will now monitor the specified Discord channel for the `!summarize` command.

## Development

This project uses `pipenv` for dependency management. To add new dependencies:

```
pipenv install package_name
```

To update dependencies:

```
pipenv update
```

## AWS Lambda Deployment

A deployment script is provided to easily upload the bot to AWS Lambda. To use it:

1. Ensure you have the AWS CLI configured with your credentials.

2. Install the required packages:
   ```
   pipenv install boto3
   ```

3. Set the environment variable for your Lambda function name:
   ```
   export AWS_LAMBDA_FUNCTION_NAME=your-lambda-function-name
   ```

4. Run the deployment script:
   ```
   pipenv run python deploy_lambda.py
   ```

This script will create a deployment package with all dependencies and upload it to your specified Lambda function. Make sure the IAM role associated with your AWS credentials has permissions to update Lambda functions.

Note: This script assumes that your Lambda function already exists. If you need to create a new function, you'll need to modify the script or create the function manually in the AWS Console first.

Remember to configure your Lambda function with the necessary environment variables (ANTHROPIC_API_KEY, DYNAMODB_TABLE_NAME, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID) in the AWS Console or via the AWS CLI.