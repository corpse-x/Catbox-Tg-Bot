import os
import logging
import tempfile
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, Document, PhotoSize,
    Video, Audio, Voice, VideoNote, Animation, Sticker
)
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType

from keyboards import start_keyboard, upload_result_keyboard, help_back_keyboard
from uploader import upload_file

logger = logging.getLogger(__name__)
router = Router()

START_TEXT = """<b>FileBot</b> — Upload anything, get permanent links.

Send a file, photo, video, or document with one of the commands below — or just send a file directly and use the inline buttons.

<b>Commands</b>
<code>/tgm</code>  — Upload to all hosts
<code>/cat</code>  — Upload to catbox.moe only
<code>/upload</code> — Same as /tgm
<code>/start</code> — This message
<code>/help</code>  — Help & info

<b>Works in</b>  DM and Groups
<b>Supports</b>  Images, Videos, Docs, ZIP, PDF, any file

<i>No login. No API key. Links never expire.</i>"""

HELP_TEXT = """<b>How to use</b>

1. Reply to a file with <code>/tgm</code> or <code>/cat</code>
2. Or send the command, then attach the file in the same message
3. Bot uploads to hosts and returns permanent URLs

<b>Link preview</b>
Images will show as preview in the returned URL message.

<b>Hosts</b>
- catbox.moe — permanent, up to 200MB
- 0x0.st — permanent (retention by file size)
- tmpfiles.org — permanent, no limit

<b>Limits</b>
Telegram Bot API: 50MB max per file."""

HOSTS_TEXT = """<b>Upload Hosts</b>

<b>catbox.moe</b>
  Permanent links, no account needed
  Max: 200MB, all file types

<b>0x0.st</b>
  Permanent (retention = 365 - (size_mb / 1024) * 365 days minimum)
  No login, direct links, all types

<b>tmpfiles.org</b>
  Permanent, no account
  Direct download links"""


async def process_file_upload(message: Message, bot: Bot, catbox_only: bool = False):
    """Core upload logic — works for all file types."""
    # Determine file object
    file_obj = None
    filename = "file"

    if message.document:
        file_obj = message.document
        filename = file_obj.file_name or "document"
    elif message.photo:
        file_obj = message.photo[-1]  # highest resolution
        filename = f"photo_{file_obj.file_unique_id}.jpg"
    elif message.video:
        file_obj = message.video
        filename = file_obj.file_name or f"video_{file_obj.file_unique_id}.mp4"
    elif message.audio:
        file_obj = message.audio
        filename = file_obj.file_name or f"audio_{file_obj.file_unique_id}.mp3"
    elif message.voice:
        file_obj = message.voice
        filename = f"voice_{file_obj.file_unique_id}.ogg"
    elif message.video_note:
        file_obj = message.video_note
        filename = f"videonote_{file_obj.file_unique_id}.mp4"
    elif message.animation:
        file_obj = message.animation
        filename = file_obj.file_name or f"animation_{file_obj.file_unique_id}.gif"
    elif message.sticker:
        file_obj = message.sticker
        filename = f"sticker_{file_obj.file_unique_id}.webp"

    if not file_obj:
        await message.reply(
            "<b>No file found.</b>\n\nReply to a file with this command, or send the file with the command in caption."
        )
        return

    # File size check
    file_size = getattr(file_obj, "file_size", 0) or 0
    if file_size > 50 * 1024 * 1024:
        await message.reply(
            f"<b>File too large.</b>\nTelegram Bot API limit is 50MB.\nYour file: <code>{file_size // (1024*1024)}MB</code>"
        )
        return

    status_msg = await message.reply("<code>Downloading file...</code>")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, filename)

            # Download
            file_info = await bot.get_file(file_obj.file_id)
            await bot.download_file(file_info.file_path, destination=local_path)

            await status_msg.edit_text("<code>Uploading to hosts...</code>")

            # Upload
            if catbox_only:
                from uploader import upload_catbox_only
                urls = await upload_catbox_only(local_path, filename)
            else:
                urls = await upload_file(local_path, filename)

    except Exception as e:
        logger.error(f"Upload error: {e}")
        await status_msg.edit_text(f"<b>Upload failed.</b>\n<code>{e}</code>")
        return

    if not urls:
        await status_msg.edit_text(
            "<b>All upload hosts failed.</b>\nTry again later."
        )
        return

    # Build result message
    lines = [f"<b>Upload complete</b> — <code>{filename}</code>\n"]

    for host, url in urls.items():
        lines.append(f"<b>{host}</b>")
        lines.append(f"<code>{url}</code>")
        lines.append("")

    # Primary URL for link preview (first URL)
    primary_url = list(urls.values())[0]
    lines.append(primary_url)  # raw URL at end triggers Telegram link preview

    result_text = "\n".join(lines)
    kb = upload_result_keyboard(urls)

    await status_msg.delete()
    await message.reply(
        result_text,
        reply_markup=kb,
        disable_web_page_preview=False  # enable link preview for image
    )


# ── Commands ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(START_TEXT, reply_markup=start_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=help_back_keyboard())


@router.message(Command(commands=["tgm", "upload"]))
async def cmd_tgm(message: Message, bot: Bot):
    # Check if command is in caption of a media message or it's a reply
    target = message.reply_to_message if message.reply_to_message else message
    await process_file_upload(target, bot, catbox_only=False)


@router.message(Command("cat"))
async def cmd_cat(message: Message, bot: Bot):
    target = message.reply_to_message if message.reply_to_message else message
    await process_file_upload(target, bot, catbox_only=True)


# ── Auto-upload when file is sent with caption command ────────────────────────

@router.message(
    F.caption.regexp(r"^/(tgm|upload|cat)\b"),
    F.document | F.photo | F.video | F.audio | F.voice | F.animation
)
async def auto_upload_with_caption(message: Message, bot: Bot):
    catbox_only = message.caption and message.caption.strip().startswith("/cat")
    await process_file_upload(message, bot, catbox_only=catbox_only)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(HELP_TEXT, reply_markup=help_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cmds")
async def cb_cmds(callback: CallbackQuery):
    text = (
        "<b>Commands</b>\n\n"
        "<code>/tgm</code>  — Upload to all hosts\n"
        "<code>/cat</code>  — Upload to catbox.moe only\n"
        "<code>/upload</code> — Same as /tgm\n"
        "<code>/help</code>  — Help & info\n"
        "<code>/start</code> — Start message\n\n"
        "<i>Reply to a file with any command to upload it.</i>"
    )
    await callback.message.edit_text(text, reply_markup=help_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "hosts")
async def cb_hosts(callback: CallbackQuery):
    await callback.message.edit_text(HOSTS_TEXT, reply_markup=help_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "start")
async def cb_start(callback: CallbackQuery):
    await callback.message.edit_text(START_TEXT, reply_markup=start_keyboard())
    await callback.answer()
