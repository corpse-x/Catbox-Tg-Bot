from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="[ How to Use ]", callback_data="help"),
        InlineKeyboardButton(text="[ Commands ]", callback_data="cmds"),
    )
    builder.row(
        InlineKeyboardButton(text="[ Supported Hosts ]", callback_data="hosts"),
    )
    return builder.as_markup()


def upload_result_keyboard(urls: dict) -> InlineKeyboardMarkup:
    """Keyboard shown after successful upload with copy/share buttons."""
    builder = InlineKeyboardBuilder()

    # Primary URL buttons (open link)
    for host, url in urls.items():
        builder.row(
            InlineKeyboardButton(
                text=f"[ {host} - Open ]",
                url=url
            )
        )

    # Share buttons for each URL
    for host, url in urls.items():
        share_text = f"[ Share via {host} ]"
        share_url = f"https://t.me/share/url?url={url}&text=Uploaded+via+FileBot"
        builder.row(
            InlineKeyboardButton(text=share_text, url=share_url)
        )

    return builder.as_markup()


def help_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="[ Back ]", callback_data="start")
    )
    return builder.as_markup()
