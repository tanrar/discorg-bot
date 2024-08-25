import anthropic
import json
import discord
from datetime import datetime, timedelta
import logging
from anthropic import APIError

# Add this at the top of the file, after imports
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeBot:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)


    def call_claude(self, messages, system="", max_tokens=4000):
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=max_tokens,
                system=system,
                messages=messages
            )
            return response.content[0].text
        except APIError as e:
            if "insufficient_quota" in str(e) or "billing" in str(e).lower():
                logger.error("Anthropic API call failed due to insufficient funds or quota limit.")
                raise Exception("Unable to process request due to API quota or billing issues. Please check your Anthropic account.")
            else:
                logger.error(f"Anthropic API call failed: {str(e)}")
                raise


        
    async def monitor_channel(self, messages, time_frame="1 hour"):
        content = "\n".join([f"{m.author.name}: {m.content}" for m in messages])
        prompt = f"Analyze the following Discord conversation from the past {time_frame}: {content}"
        
        messages = [
            {"role": "user", "content": prompt},
        ]
        
        analysis = self.call_claude(messages, max_tokens=4000)
        return analysis
        
    async def generate_response(self, prompt):
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except APIError as e:
            if "insufficient_quota" in str(e) or "billing" in str(e).lower():
                logger.error("Anthropic API call failed due to insufficient funds or quota limit.")
                return "I'm sorry, but I'm currently unable to process requests due to API quota or billing issues. Please contact the bot administrator."
            else:
                logger.error(f"Anthropic API call failed: {str(e)}")
                return "I encountered an error while processing your request. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error generating response from Claude: {str(e)}")
            return "An unexpected error occurred. Please try again later or contact the bot administrator if the problem persists."