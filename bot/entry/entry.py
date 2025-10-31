from pyrogram.client import Client
from pathlib import Path
import dotenv as dt
import os

# dt.load_dotenv(dotenv_path=Path.cwd() / Path("bot") / Path("core") / ".env")

bot: Client = Client(os.getenv("NAME"), api_hash=os.getenv("TELEGRAM_API_HASH"), api_id=os.getenv("TELEGRAM_API_ID"), bot_token=os.getenv("TELEGRAM_BOT_TOKEN"))
