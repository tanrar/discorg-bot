import anthropic
import json
import discord
from datetime import datetime, timedelta

class ClaudeBot:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.personality_file = "claude_personality.json"
        self.load_personality()

    def load_personality(self):
        try:
            with open(self.personality_file, 'r') as f:
                self.personality = json.load(f)
        except FileNotFoundError:
            self.personality = {
                "identity": {
                    "name": "ClaudeBot",
                    "role": "Discord Bot",
                    "context": "I am a Discord Bot serving the Discorg server, which is a spinoff of the neoliberal subreddit. My purpose is to assist users, provide summaries, and engage in discussions related to politics, economics, and policy."
                },
                "traits": {
                    "humor": 0.5,
                    "formality": 0.5,
                    "empathy": 0.5,
                    "policy_knowledge": 0.8
                },
                "daily_history": [],
                "hourly_history": []
            }
            self.save_personality()

    def save_personality(self):
        with open(self.personality_file, 'w') as f:
            json.dump(self.personality, f, indent=2)

    def call_claude(self, messages, system="", max_tokens=1000):
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            system=system,
            messages=messages
        )
        return response.content[0].text

    async def process_message(self, message, channel):
        identity_context = f"I am {self.personality['identity']['name']}, {self.personality['identity']['role']}. {self.personality['identity']['context']}"
        trait_context = f"My personality traits are: {self.personality['traits']}."
        history_context = f"Recent daily history: {self.personality['daily_history'][-1] if self.personality['daily_history'] else 'No recent history'}. "
        history_context += f"Recent hourly history: {self.personality['hourly_history'][-1] if self.personality['hourly_history'] else 'No recent history'}."

        channel_messages = []
        async for msg in channel.history(limit=50):
            channel_messages.append(f"{msg.author.name}: {msg.content}")
        channel_messages.reverse()  # Oldest first
        channel_context = "Last 50 messages in the channel:\n" + "\n".join(channel_messages)

        system_content = f"{identity_context}\n{trait_context}\n{history_context}"

        messages = [
            {"role": "user", "content": f"Here's the recent context of the conversation:\n\n{channel_context}\n\nNow, please respond to the following message: {message.content}"},
        ]

        response = self.call_claude(messages, system=system_content)
        return response

    async def summarize_conversation(self, messages, time_frame="24 hours"):
        content = "\n".join([f"{m.author.name}: {m.content}" for m in messages])
        prompt = f"Summarize the following Discord conversation from the past {time_frame}: {content}"
        
        messages = [
            {"role": "user", "content": prompt},
        ]
        
        return self.call_claude(messages, max_tokens=2000)

    async def summarize_past_24h(self, channel):
        yesterday = datetime.now() - timedelta(days=1)
        messages = []
        last_message_id = None

        while True:
            chunk = []
            async for message in channel.history(limit=100, after=yesterday, before=last_message_id and discord.Object(id=last_message_id)):
                chunk.append(message)
            
            if not chunk:
                break
            
            messages.extend(chunk)
            last_message_id = chunk[-1].id

        if not messages:
            return "No messages in the past 24 hours."

        messages.reverse()  # Oldest first
        summary = await self.summarize_conversation(messages)
        self.personality["daily_history"].append(summary)
        self.save_personality()
        return summary
        
    async def monitor_channel(self, messages, time_frame="1 hour"):
        content = "\n".join([f"{m.author.name}: {m.content}" for m in messages])
        prompt = f"Analyze the following Discord conversation from the past {time_frame}: {content}"
        
        messages = [
            {"role": "user", "content": prompt},
        ]
        
        analysis = self.call_claude(messages, max_tokens=1500)
        self.personality["hourly_history"].append(analysis)
        self.save_personality()
        return analysis