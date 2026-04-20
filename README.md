# FileBot

Aiogram 3.x Telegram bot — upload files to permanent free hosts.

## Setup

```bash
cp .env.example .env
# edit .env, set BOT_TOKEN

pip install -r requirements.txt
python bot.py
```

## Commands

| Command | Action |
|---------|--------|
| `/start` | Start message + buttons |
| `/tgm` | Upload to all hosts |
| `/upload` | Same as /tgm |
| `/cat` | Upload to catbox only |
| `/help` | Help info |

**Usage:** Reply to any file with `/tgm` or `/cat`, OR send the command as caption with the file.

## Hosts

- **catbox.moe** — permanent, no account, up to 200MB
- **0x0.st** — permanent (retention formula), no login
- **tmpfiles.org** — permanent, no login

## Supported file types

Images, Videos, Documents, ZIP, PDF, Audio, Voice, GIF, Stickers, any document type.

## Requirements

- Python 3.10+
- aiogram 3.13+
