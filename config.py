import os

# Укажи свой Telegram ID
ROOT_ID: int = int(os.getenv("ROOT_ID", "123456789"))

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

DB_PATH: str = "data/bot.db"

# Часовой пояс для рассылок
TIMEZONE: str = "Europe/Moscow"
