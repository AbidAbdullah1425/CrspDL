from bot import Bot
import os
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID

# Constants
SCRIPT_PATH = "./animepahe-dl.sh"
DOWNLOADS_PATH = "./downloads"
TEMP_DATA = {}  # Store user selection data temporarily

class AnimeDL:
    def __init__(self):
        self.active_downloads = {}
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        
    async def execute_cmd(self, cmd: list) -> tuple:
        """Execute shell command and return output"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode(), stderr.decode(), process.returncode

    async def search_anime(self, query: str) -> list:
        """Search for anime using the script"""
        cmd = [SCRIPT_PATH, "-a", query]
        stdout, stderr, code = await self.execute_cmd(cmd)
        results = []
        if code == 0 and stdout:
            for line in stdout.splitlines():
                if "]" in line and line.strip():
                    try:
                        session = line.split("]")[0].strip("[")
                        title = line.split("]")[1].strip()
                        results.append({
                            "session": session,
                            "title": title
                        })
                    except:
                        continue
        return results

    async def get_episodes(self, session: str) -> list:
        """Get episode list for anime"""
        cmd = [SCRIPT_PATH, "-s", session, "-l"]
        stdout, stderr, code = await self.execute_cmd(cmd)
        episodes = []
        if code == 0 and stdout:
            # Parse episode list from output
            for line in stdout.splitlines():
                if line.startswith("E") and "]" in line:
                    ep_num = line.split("]")[0].replace("E", "").strip()
                    episodes.append(ep_num)
        return sorted(episodes, key=lambda x: int(x))

    async def get_resolutions(self, session: str, episode: str) -> list:
        """Get available resolutions for episode"""
        cmd = [SCRIPT_PATH, "-s", session, "-e", episode, "-l"]
        stdout, stderr, code = await self.execute_cmd(cmd)
        resolutions = []
        if stdout:
            # Parse resolutions from output
            for line in stdout.splitlines():
                if "resolution" in line:
                    res = line.split('"')[1]
                    if res not in resolutions:
                        resolutions.append(res)
        return sorted(resolutions, key=lambda x: int(x))

    async def download_episode(self, session: str, episode: str, resolution: str = None) -> str:
        """Download episode and return file path"""
        cmd = [SCRIPT_PATH, "-s", session, "-e", episode]
        if resolution:
            cmd.extend(["-r", resolution])
        
        output_file = f"{DOWNLOADS_PATH}/{session}_EP{episode}.mp4"
        cmd.extend(["-o", output_file])
        
        stdout, stderr, code = await self.execute_cmd(cmd)
        if code == 0 and os.path.exists(output_file):
            return output_file
        return None

dl = AnimeDL()

@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_cmd(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide anime name!\nUsage: /dl <anime name>")
        return

    query = " ".join(message.command[1:])
    status_msg = await message.reply_text("🔍 Searching anime...")

    results = await dl.search_anime(query)
    if not results:
        await status_msg.edit_text("❌ No results found!")
        return

    # Create keyboard with results
    buttons = []
    for result in results[:8]:  # Limit to 8 results
        buttons.append([
            InlineKeyboardButton(
                text=result["title"][:60],
                callback_data=f"anime_{result['session']}"
            )
        ])

    await status_msg.edit_text(
        "🎯 Select anime:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex("^anime_"))
async def handle_anime_selection(client, callback: CallbackQuery):
    session = callback.data.split("_")[1]
    TEMP_DATA[callback.from_user.id] = {"session": session}

    await callback.message.edit_text("📃 Getting episode list...")
    episodes = await dl.get_episodes(session)
    
    if not episodes:
        await callback.message.edit_text("❌ No episodes found!")
        return

    # Create episode selection buttons
    buttons = []
    for i in range(0, len(episodes), 2):
        row = []
        for ep in episodes[i:i+2]:
            row.append(
                InlineKeyboardButton(
                    f"EP {ep}",
                    callback_data=f"ep_{ep}"
                )
            )
        buttons.append(row)

    if len(buttons) > 5:  # Add navigation if many episodes
        buttons.append([
            InlineKeyboardButton("⬅️", callback_data="nav_prev"),
            InlineKeyboardButton("➡️", callback_data="nav_next")
        ])

    await callback.message.edit_text(
        "📺 Select episode:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex("^ep_"))
async def handle_episode_selection(client, callback: CallbackQuery):
    episode = callback.data.split("_")[1]
    user_data = TEMP_DATA.get(callback.from_user.id, {})
    user_data["episode"] = episode
    TEMP_DATA[callback.from_user.id] = user_data

    await callback.message.edit_text("🎬 Getting available resolutions...")
    resolutions = await dl.get_resolutions(user_data["session"], episode)

    if not resolutions:
        await callback.message.edit_text("❌ No resolutions found!")
        return

    buttons = []
    for res in resolutions:
        buttons.append([
            InlineKeyboardButton(
                f"{res}p",
                callback_data=f"res_{res}"
            )
        ])

    await callback.message.edit_text(
        "📊 Select resolution:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex("^res_"))
async def handle_resolution_selection(client, callback: CallbackQuery):
    resolution = callback.data.split("_")[1]
    user_data = TEMP_DATA.get(callback.from_user.id, {})
    
    await callback.message.edit_text(
        f"⏬ Starting download...\n"
        f"Anime: {user_data['session']}\n"
        f"Episode: {user_data['episode']}\n"
        f"Resolution: {resolution}p"
    )

    # Start download
    file_path = await dl.download_episode(
        user_data["session"],
        user_data["episode"],
        resolution
    )

    if not file_path or not os.path.exists(file_path):
        await callback.message.edit_text("❌ Download failed!")
        return

    # Upload to Telegram
    await callback.message.edit_text("📤 Uploading to Telegram...")
    await client.send_video(
        callback.message.chat.id,
        video=file_path,
        caption=(
            f"🎯 {user_data['session']}\n"
            f"📺 Episode {user_data['episode']}\n"
            f"📊 {resolution}p"
        )
    )

    # Cleanup
    os.remove(file_path)
    del TEMP_DATA[callback.from_user.id]
    await callback.message.edit_text("✅ Download completed!")
