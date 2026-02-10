"""
Auto Automation Cog
Handles automatic keyword responses and smart message broadcasting.
"""

import discord
from discord.ext import commands
import asyncio
import json
import os
import random
from datetime import datetime

DATA_FOLDER = "data"
TRIGGER_DATA_FILE = os.path.join(DATA_FOLDER, "triggers.json")
MESSAGE_FILE = os.path.join(DATA_FOLDER, "message_sent.txt")

class auto_mess(commands.Cog):
    """Automatic response and smart messaging commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.data = self._load_data()
        self.auto_mess_task = None
        
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        if not os.path.exists(MESSAGE_FILE):
            with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
                f.write("Hello from auto message!\nThank you for messaging.\nHave a great day.")

        for chan_id, info in self.data.get("auto_messages", {}).items():
            asyncio.create_task(self._auto_message_fixed_task(int(chan_id), info['time'], info['content']))
            
        if self.data.get("auto_mess_config", {}).get("active"):
            self.auto_mess_task = asyncio.create_task(self._auto_mess_loop())

    def _load_data(self):
        """Loads automation data from the JSON file."""
        try:
            if os.path.exists(TRIGGER_DATA_FILE):
                with open(TRIGGER_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "auto_responses": {}, 
                "auto_messages": {}, 
                "auto_mess_config": {"active": False, "mode": "time", "value": 60}
            }
        except:
            return {"auto_responses": {}, "auto_messages": {}, "auto_mess_config": {"active": False, "mode": "time", "value": 60}}

    def _save_data(self):
        """Saves current data to the JSON file."""
        with open(TRIGGER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def _get_random_message(self):
        """Retrieves a random line from message_sent.txt."""
        try:
            with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            return random.choice(lines) if lines else None
        except:
            return None

    # ==================== 1. AUTO RESPONSE (.ar) ====================

    @commands.command(name='ar')
    async def add_ar(self, ctx, *, trigger_response: str):
        """Usage: {prefix}ar <keyword>, <response>"""
        try:
            await ctx.message.delete()
            trigger_word, response = map(str.strip, trigger_response.split(',', 1))
            self.data["auto_responses"][trigger_word.lower()] = response
            self._save_data()
            await ctx.send(f"✅ Added trigger: `{trigger_word}`", delete_after=5)
        except:
            await ctx.send(f"❌ Invalid format. Use: `{ctx.prefix}ar keyword, response`", delete_after=5)

    @commands.command(name='ar_list')
    async def list_ar(self, ctx):
        """Usage: {prefix}ar_list"""
        ars = self.data.get("auto_responses", {})
        if not ars: 
            return await ctx.send("❌ The auto-response list is empty.")
        
        msg = "\n".join([f"• {k}: {v}" for k, v in ars.items()])
        await ctx.send(f"**📝 ACTIVE AUTO RESPONSES:**\n```\n{msg}\n```")

    # ==================== 2. AUTO MESSAGE FIXED (.am) ====================

    @commands.command(name='am')
    async def add_am(self, ctx, interval: int, channel_id: int, *, content: str):
        """Usage: {prefix}am <seconds> <channel_id> <content>"""
        self.data["auto_messages"][str(channel_id)] = {"time": interval, "content": content}
        self._save_data()
        asyncio.create_task(self._auto_message_fixed_task(channel_id, interval, content))
        await ctx.send(f"✅ Auto-posting enabled every {interval}s in <#{channel_id}>")

    async def _auto_message_fixed_task(self, channel_id, interval, content):
        """Loop for fixed message intervals."""
        while str(channel_id) in self.data.get("auto_messages", {}):
            channel = self.bot.get_channel(channel_id)
            if channel:
                try: await channel.send(content)
                except: pass
            await asyncio.sleep(interval)

    # ==================== 3. AUTO MESS RANDOM (.auto_mess) ====================

    @commands.command(name='auto_mess')
    async def auto_mess_cmd(self, ctx, status: str, channel_id: int = None, mode: str = "time", value: int = 60):
        """Usage: {prefix}auto_mess <on/off> [channel_id] [mode] [value]"""
        try: await ctx.message.delete()
        except: pass

        if status.lower() == "on":
            target_channel_id = channel_id if channel_id else ctx.channel.id
            
            self.data["auto_mess_config"] = {
                "active": True,
                "mode": mode.lower(),
                "value": value,
                "channel_id": target_channel_id
            }
            self._save_data()
            
            if self.auto_mess_task:
                self.auto_mess_task.cancel()
            self.auto_mess_task = asyncio.create_task(self._auto_mess_loop())
            
            await ctx.send(f"✅ **Auto Mess Random:** ON\n- Channel: <#{target_channel_id}>\n- Mode: `{mode}`\n- Value: `{value}`")
        else:
            self.data["auto_mess_config"]["active"] = False
            self._save_data()
            if self.auto_mess_task:
                self.auto_mess_task.cancel()
            await ctx.send("❌ **Auto Mess Random:** OFF")

    async def _auto_mess_loop(self):
        """Loop for smart random messaging."""
        while self.data.get("auto_mess_config", {}).get("active"):
            config = self.data["auto_mess_config"]
            channel = self.bot.get_channel(config["channel_id"])
            if not channel:
                await asyncio.sleep(10)
                continue

            if config["mode"] == "time":
                await asyncio.sleep(config["value"])
                msg = self._get_random_message()
                if msg:
                    try: await channel.send(msg)
                    except: pass
            
            elif config["mode"] == "message":
                wait_count = config["value"]
                other_msgs_count = 0
                
                async for message in channel.history(limit=50):
                    if message.author.id == self.bot.user.id:
                        break
                    other_msgs_count += 1
                
                if other_msgs_count >= wait_count:
                    msg = self._get_random_message()
                    if msg:
                        try: await channel.send(msg)
                        except: pass
                
                await asyncio.sleep(5)

    # ==================== LISTENER ====================

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for keywords and triggers auto-responses."""
        if message.author.bot: return
        
        # Auto Response Trigger Logic
        content = message.content.lower()
        if content in self.data.get("auto_responses", {}):
            try:
                await message.channel.send(self.data["auto_responses"][content])
            except:
                pass

def setup(bot):
    """Cog setup function."""
    bot.add_cog(auto_mess(bot))
