"""
Demo: sends a couple of sample posts to your Telegram channel, run from
the agent/ folder. Works with `python3 agent/demo.py` from the project
root, or `python3 demo.py` from inside agent/.
"""

import os
import sys
import dotenv

print(__file__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

dotenv.load_dotenv()

from telegram_client.telegram_publisher import TelegramPublisher

# Load .env from the project root (no extra dependency needed)
env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

bot = TelegramPublisher()

msg_id = bot.post_text("👋 Hello from agent/demo.py!")
print(f"Sent text post, message id {msg_id}")

msg_id = bot.post_news_item(
    title="Demo News Item",
    summary="This is a demo showing how automated news posts will look.",
    url="https://example.com",
    source="Demo Source",
)
print(f"Sent news item, message id {msg_id}")
