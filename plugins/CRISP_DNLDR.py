from bot import Bot
import os
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID

# Constants
SCRIPT_PATH = "/app/animepahe-dl.sh"  # Script in the app directory
DOWNLOADS_PATH = "/tmp/downloads"  # Use /tmp for downloads
TEMP_DATA = {}  # Store user selection data temporarily

class AnimeDL:
    def __init__(self):
        self.active_downloads = {}
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        # Make script executable if needed
        if os.path.exists(SCRIPT_PATH):
            os.chmod(SCRIPT_PATH, 0o755)
        
    async def execute_cmd(self, cmd: list) -> tuple:
        """Execute shell command and return output"""
        try:
            # Add environment variables
            env = os.environ.copy()
            env['ANIMEPAHE_DL_NODE'] = '/usr/bin/node'
            env['ANIMEPAHE_DL_NONINTERACTIVE'] = '1'
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd="/tmp"  # Set working directory to /tmp
            )
            stdout, stderr = await process.communicate()
            return stdout.decode(), stderr.decode(), process.returncode
        except Exception as e:
            return "", str(e), 1

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

dl = AnimeDL()

@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_cmd(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide anime name!\nUsage: /dl <anime name>")
        return

    query = " ".join(message.command[1:])
    status_msg = await message.reply_text("🔍 Searching anime...")

    try:
        # Execute search command with error checking
        cmd = [SCRIPT_PATH, "-a", query]
        stdout, stderr, code = await dl.execute_cmd(cmd)
        
        # Debug output
        print(f"Search command: {' '.join(cmd)}")
        print(f"Exit code: {code}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

        if code != 0:
            await status_msg.edit_text(f"❌ Search failed: {stderr}")
            return

        stdout_text = stdout
        if not stdout_text.strip():
            await status_msg.edit_text("❌ No results found!")
            return

        # Create keyboard with results
        buttons = []
        for line in stdout_text.splitlines():
            if "]" in line and line.strip():
                try:
                    session = line.split("]")[0].strip("[")
                    title = line.split("]")[1].strip()
                    buttons.append([
                        InlineKeyboardButton(
                            text=title[:60],
                            callback_data=f"anime_{session}"
                        )
                    ])
                except:
                    continue

        if not buttons:
            await status_msg.edit_text("❌ No results found!")
            return

        await status_msg.edit_text(
            "🎯 Select anime:",
            reply_markup=InlineKeyboardMarkup(buttons[:8])
        )

    except Exception as e:
        print(f"Error in handle_dl_cmd: {str(e)}")
        await status_msg.edit_text(f"❌ An error occurred: {str(e)}")

@Bot.on_callback_query(filters.regex("^anime_"))
async def handle_anime_selection(client, callback: CallbackQuery):
    session = callback.data.split("_")[1]
    TEMP_DATA[callback.from_user.id] = {"session": session}
    
    # Use -s and -l flags to get episodes
    cmd = [SCRIPT_PATH, "-s", session, "-l"]
    stdout, stderr, code = await dl.execute_cmd(cmd)
    
    if code != 0:
        await callback.message.edit_text("❌ Failed to get episodes!")
        return
        
    # Parse episodes from output
    episodes = []
    for line in stdout.splitlines():
        if line.startswith("[") and "]" in line:
            try:
                ep_num = line.split("]")[0].strip("[")
                episodes.append(ep_num)
            except:
                continue
    
    if not episodes:
        await callback.message.edit_text("❌ No episodes found!")
        return
    
    # Create episode selection buttons
    buttons = []
    for i in range(0, len(episodes), 2):  # 2 episodes per row
        row = []
        for ep in episodes[i:i+2]:
            if len(row) < 2:  # Maximum 2 buttons per row
                row.append(
                    InlineKeyboardButton(
                        f"EP {ep}",
                        callback_data=f"ep_{ep}"
                    )
                )
        buttons.append(row)
    
    await callback.message.edit_text(
        "📺 Select episode:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex("^ep_"))
async def handle_episode_selection(client, callback: CallbackQuery):
    episode = callback.data.split("_")[1]
    user_data = TEMP_DATA.get(callback.from_user.id, {})
    
    if not user_data.get("session"):
        await callback.message.edit_text("❌ Session expired. Please search again.")
        return
    
    await callback.message.edit_text("⏬ Starting download...")
    
    # Download episode
    cmd = [SCRIPT_PATH, "-s", user_data["session"], "-e", episode]
    stdout, stderr, code = await dl.execute_cmd(cmd)
    
    if code != 0:
        await callback.message.edit_text(f"❌ Download failed: {stderr}")
        return
    
    # Find downloaded file
    output_file = f"{DOWNLOADS_PATH}/{user_data['session']}_EP{episode}.mp4"
    if not os.path.exists(output_file):
        await callback.message.edit_text("❌ Video file not found!")
        return
    
    # Upload to Telegram
    await callback.message.edit_text("📤 Uploading to Telegram...")
    try:
        await client.send_video(
            callback.message.chat.id,
            video=output_file,
            caption=f"🎯 {user_data['session']}\n📺 Episode {episode}"
        )
        os.remove(output_file)  # Clean up
        del TEMP_DATA[callback.from_user.id]  # Clear temp data
        await callback.message.edit_text("✅ Download completed!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Upload failed: {str(e)}")