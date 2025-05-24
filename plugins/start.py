import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import START_MSG, ADMINS

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('start'))
async def start_command(client: Client, message: Message):
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😊 About Me", callback_data="about"),
                InlineKeyboardButton("🔒 Close", callback_data="close")
            ]
        ]
    )
    
    await message.reply_text(
        text=START_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        quote=True
    )

@Bot.on_message(filters.command("startfile"))
async def start_script(client, message):
    try:
        result = subprocess.check_output(["/bin/sh", "start.sh"], stderr=subprocess.STDOUT)
        await message.reply(f"`{result.decode()}`")
    except subprocess.CalledProcessError as e:
        await message.reply(f"Error:\n`{e.output.decode()}`")