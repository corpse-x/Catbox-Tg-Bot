import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "7632335902:AABBCCDD")

# Upload APIs
CATBOX_API = "https://catbox.moe/user/api.php"
LITTERBOX_API = "https://litterbox.catbox.moe/resources/internals/api.php"
# 0x0.st - no login, permanent, supports most file types
ZEROX0_API = "https://0x0.st"
# file.io - no login needed (short-lived, fallback only)
# tmpfiles.org - no login, permanent
TMPFILES_API = "https://tmpfiles.org/api/v1/upload"

MAX_FILE_SIZE_MB = 50  # Telegram bot API limit
