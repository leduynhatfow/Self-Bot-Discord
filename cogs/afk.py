"""
AFK Status Cog
Manages Away-From-Keyboard (AFK) status and automated responses.
"""

import discord
from discord.ext import commands
import asyncio
import json
import os

DATA_FOLDER = "data"
AFK_DATA_FILE = os.path.join(DATA_FOLDER, "afk_status.json")

class afk(commands.Cog):
    """Commands to set and manage AFK status."""
    
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        self.afk_data = self._load_data()
        self.user_cooldowns = {}
    
    def _load_data(self):
        """Loads AFK statuses from the persistent JSON file."""
        try:
            if os.path.exists(AFK_DATA_FILE):
                with open(AFK_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _save_data(self):
        """Saves current AFK statuses to the JSON file."""
        with open(AFK_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.afk_data, f, ensure_ascii=False, indent=4)

    @commands.command(name='afk')
    async def set_afk(self, ctx, *, reason: str = "I am currently busy, will get back to you later."):
        """Usage: {prefix}afk [reason]"""
        self.afk_data[str(ctx.author.id)] = reason
        self._save_data()
        
        try:
            await ctx.message.edit(content=f"✅ **AFK Mode Enabled:** {reason}")
        except discord.HTTPException:
            await ctx.send(f"✅ **AFK Mode Enabled:** {reason}")

    @commands.command(name='unafk')
    async def remove_afk(self, ctx):
        """Usage: {prefix}unafk"""
        if str(ctx.author.id) in self.afk_data:
            del self.afk_data[str(ctx.author.id)]
            self._save_data()
            
            try:
                await ctx.message.edit(content="✅ **AFK Mode Disabled.** Welcome back!")
            except discord.HTTPException:
                await ctx.send("✅ **AFK Mode Disabled.** Welcome back!")
        else:
            try:
                await ctx.message.edit(content="❌ **You are not currently AFK.**")
            except discord.HTTPException:
                await ctx.send("❌ **You are not currently AFK.**")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for mentions and handles AFK responses."""
        if message.author.bot:
            return

        bot_id = str(self.bot.user.id)
        if bot_id in self.afk_data:
            is_mentioned = self.bot.user in message.mentions
            is_dm = isinstance(message.channel, discord.DMChannel)
            
            if (is_mentioned or is_dm) and message.author.id != self.bot.user.id:
                if message.author.id not in self.user_cooldowns:
                    reason = self.afk_data[bot_id]
                    await message.channel.send(f"⚠️ **I am currently AFK:** {reason}")
                    
                    self.user_cooldowns[message.author.id] = True
                    await asyncio.sleep(10)
                    if message.author.id in self.user_cooldowns:
                        del self.user_cooldowns[message.author.id]

def setup(bot):
    """Cog setup function."""
    bot.add_cog(afk(bot))
