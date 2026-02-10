import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import random
from datetime import datetime, timezone
from typing import List

class presence(commands.Cog):
    """Custom status, Spotify, and Rich Presence manager."""
    
    def __init__(self, bot, token: str):
        self.bot = bot
        self.token = token
        self.songs_file = "data/songs.json"
        self.rpc_config = "rich_presence.json"
        
        # State
        self.is_rotating = False
        self.is_rotating_listen = False
        self.is_custom_rpc = False
        self.statuses = []
        self.tracks = []
        self.rpc_data = None
        
    
    def _load_songs(self):
        """Loads Spotify tracks from JSON file."""
        try:
            with open(self.songs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _load_rpc_config(self):
        """Loads custom RPC configuration from JSON file."""
        try:
            with open(self.rpc_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    # ==================== CUSTOM STATUS ====================
    
    @commands.command(name='rotate')
    async def rotate(self, ctx, *, statuses: str):
        """Usage: {prefix}rotate <emoji1>,<text1> / <emoji2>,<text2>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if self.is_rotating:
            temp = await ctx.send("**❌ Status rotation is already running**")
            await asyncio.sleep(3)
            await temp.delete()
            return
        
        self.statuses = [s.strip() for s in statuses.split('/') if s.strip()]
        if not self.statuses:
            temp = await ctx.send(
                "**❌ Invalid format**\n\n"
                "**Usage:**\n"
                "`.rotate 😎,Text1 / 🔥,Text2`\n"
                "`.rotate <:pepe:123>,Dank / <a:dance:456>,Vibe`"
            )
            await asyncio.sleep(5)
            await temp.delete()
            return
        
        self.is_rotating = True
        temp = await ctx.send(
            f"**✅ Status Rotation Enabled**\n"
            f"📊 Total statuses: `{len(self.statuses)}`\n"
            f"🔄 Switching every 5 seconds"
        )
        await asyncio.sleep(3)
        await temp.delete()
        
        asyncio.create_task(self._rotate_loop())
    
    @commands.command(name='stop_rotate')
    async def stop_rotate(self, ctx):
        """Usage: {prefix}stop_rotate"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        self.is_rotating = False
        await self._clear_status()
        temp = await ctx.send("**✅ Status rotation disabled**")
        await asyncio.sleep(3)
        await temp.delete()
    
    async def _rotate_loop(self):
        """Main loop for rotating custom statuses."""
        while self.is_rotating:
            try:
                for status in self.statuses:
                    if not self.is_rotating:
                        break
                    
                    parts = status.split(',', 1)
                    emoji = parts[0].strip()
                    text = parts[1].strip() if len(parts) > 1 else ""
                    
                    emoji_id = None
                    emoji_name = None
                    
                    if emoji.startswith("<") and emoji.endswith(">"):
                        try:
                            emoji_parts = emoji.strip("<>").split(":")
                            if len(emoji_parts) >= 3:
                                emoji_name = emoji_parts[1]
                                emoji_id = emoji_parts[2]
                            elif len(emoji_parts) == 2:
                                emoji_name = emoji_parts[0]
                                emoji_id = emoji_parts[1]
                        except:
                            emoji_name = emoji  # Fallback
                    else:
                        if emoji.isdigit():
                            emoji_id = emoji
                        else:
                            emoji_name = emoji
                    
                    async with aiohttp.ClientSession() as s:
                        await s.patch(
                            "https://discord.com/api/v9/users/@me/settings",
                            headers={
                                "Authorization": self.token, 
                                "Content-Type": "application/json"
                            },
                            json={
                                "status": "dnd", 
                                "custom_status": {
                                    "text": text, 
                                    "emoji_name": emoji_name, 
                                    "emoji_id": emoji_id
                                }
                            }
                        )
                    
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ [ROTATE] Error: {e}")
                await asyncio.sleep(5)
        
        await self._clear_status()
    
    async def _clear_status(self):
        """Clears the custom status."""
        try:
            async with aiohttp.ClientSession() as s:
                await s.patch(
                    "https://discord.com/api/v9/users/@me/settings",
                    headers={"Authorization": self.token, "Content-Type": "application/json"},
                    json={"custom_status": None}
                )
        except:
            pass
    
    # ==================== SPOTIFY - FULL SONG DURATION ====================
    
    @commands.command(name='rotate_listen')
    async def rotate_listen(self, ctx):
        """Usage: {prefix}rotate_listen"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if self.is_rotating_listen:
            temp = await ctx.send("**❌ Spotify mode is already running**")
            await asyncio.sleep(3)
            await temp.delete()
            return
        
        if self.is_custom_rpc:
            self.is_custom_rpc = False
            await asyncio.sleep(0.5)
        
        tracks = self._load_songs()
        if not tracks:
            temp = await ctx.send(
                f"**❌ No tracks found**\n\n"
                f"File: `{self.songs_file}`\n"
                f"Please export your Spotify playlist to this file"
            )
            await asyncio.sleep(5)
            await temp.delete()
            return
        
        self.tracks = tracks.copy()
        random.shuffle(self.tracks)
        self.is_rotating_listen = True
        
        temp = await ctx.send(
            f"**✅ Spotify Mode Enabled**\n"
            f"🎵 Total tracks: `{len(tracks)}`\n"
            f"🔀 Shuffled playlist"
        )
        await asyncio.sleep(3)
        await temp.delete()
        
        asyncio.create_task(self._spotify_loop())
    
    @commands.command(name='stop_rotate_listen')
    async def stop_rotate_listen(self, ctx):
        """Usage: {prefix}stop_rotate_listen"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        self.is_rotating_listen = False
        await self.bot.change_presence(activity=None, status=discord.Status.online)
        temp = await ctx.send("**✅ Spotify mode disabled**")
        await asyncio.sleep(3)
        await temp.delete()
    
    async def _spotify_loop(self):
        """Main loop for Spotify listening mode - plays full song duration."""
        while self.is_rotating_listen:
            try:
                if not self.tracks:
                    self.tracks = self._load_songs()
                    random.shuffle(self.tracks)
                
                if not self.tracks:
                    await asyncio.sleep(30)
                    continue
                
                track = self.tracks.pop(0)
                t = track["track"]
                
                name = t["name"]
                artist = t["artists"][0]["name"]
                album = t["album"]["name"]
                
                img_url = t["album"]["images"][0]["url"]
                if "https://i.scdn.co/image/" in img_url:
                    img = img_url.split("https://i.scdn.co/image/")[1]
                else:
                    img = "ab67616d00001e02c4d671473910340ec095a9cc"
                
                duration_ms = t["duration_ms"]
                start = int(datetime.now(timezone.utc).timestamp() * 1000)
                end = start + duration_ms
                
                spotify_url = t.get("external_urls", {}).get("spotify", "https://open.spotify.com")
                
                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name="Spotify",
                    details=name,
                    state=f"by {artist}",
                    timestamps={"start": start, "end": end},
                    assets={
                        "large_image": f"spotify:{img}",
                        "large_text": album
                    },
                    application_id=145093540785766400,
                    party={"id": f"spotify:{random.randint(100000000000, 999999999999)}"},
                    sync_id=t.get("id", str(random.randint(100000, 999999))),
                    buttons=["Play on Spotify"],
                    metadata={
                        "button_urls": [spotify_url]
                    }
                )
                
                await self.bot.change_presence(activity=activity, status=discord.Status.online)
                
                wait_time = duration_ms / 1000
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                print(f"❌ [SPOTIFY] Error: {e}")
                await asyncio.sleep(30)
        
        await self.bot.change_presence(activity=None, status=discord.Status.online)
    
    # ==================== CUSTOM RPC - ALWAYS WITH PROGRESS BAR ====================
    
    @commands.command(name='custom_rpc')
    async def custom_rpc(self, ctx):
        """Usage: {prefix}custom_rpc"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if self.is_custom_rpc:
            temp = await ctx.send("**❌ Custom RPC is already running**")
            await asyncio.sleep(3)
            await temp.delete()
            return
        
        if self.is_rotating_listen:
            self.is_rotating_listen = False
            await asyncio.sleep(0.5)
        
        cfg = self._load_rpc_config()
        if not cfg:
            temp = await ctx.send(
                f"**❌ Config file not found**\n\n"
                f"File: `{self.rpc_config}`\n"
                f"Please create your custom RPC config"
            )
            await asyncio.sleep(5)
            await temp.delete()
            return
        
        self.rpc_data = cfg
        self.is_custom_rpc = True
        
        temp = await ctx.send(
            f"**✅ Custom RPC Enabled**\n"
            f"🎨 Progress bar: `Active`\n"
            f"🔄 Auto-reload: `Enabled`"
        )
        await asyncio.sleep(3)
        await temp.delete()
        
        asyncio.create_task(self._custom_rpc_loop())
    
    @commands.command(name='stop_custom_rpc')
    async def stop_custom_rpc(self, ctx):
        """Usage: {prefix}stop_custom_rpc"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        self.is_custom_rpc = False
        await self.bot.change_presence(activity=None, status=discord.Status.online)
        temp = await ctx.send("**✅ Custom RPC disabled**")
        await asyncio.sleep(3)
        await temp.delete()
    
    async def _custom_rpc_loop(self):
        """Main loop for custom RPC - always with progress bar."""
        
        while self.is_custom_rpc:
            try:
                cfg = self._load_rpc_config()
                if not cfg:
                    await asyncio.sleep(10)
                    continue
                
                large_text_list = cfg.get("large_text", ["Listening to Music"])
                large_text_random = random.choice(large_text_list) if isinstance(large_text_list, list) else large_text_list
                
                duration_seconds = cfg.get("duration", 180)
                duration_ms = duration_seconds * 1000
                start = int(datetime.now(timezone.utc).timestamp() * 1000)
                end = start + duration_ms
                
                assets = {}
                if cfg.get("large_image"):
                    assets["large_image"] = cfg["large_image"]
                    assets["large_text"] = large_text_random
                
                button_url = cfg.get("details", "")
                if button_url and not button_url.startswith("http"):
                    button_url = f"https://{button_url}"
                
                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name="Spotify",
                    details=large_text_random,  # Line 1 - LARGE TEXT
                    state=cfg.get("details", ""),  # Line 2 - URL
                    timestamps={"start": start, "end": end},
                    assets=assets if assets else None,
                    application_id=145093540785766400,
                    party={"id": f"spotify:{random.randint(100000000000, 999999999999)}"},
                    sync_id=str(random.randint(100000, 999999)),
                    buttons=[large_text_random] if button_url else None,
                    metadata={"button_urls": [button_url]} if button_url else None
                )
                
                await self.bot.change_presence(activity=activity, status=discord.Status.online)
                
                await asyncio.sleep(duration_seconds)
                
            except Exception as e:
                print(f"❌ [CUSTOM RPC] Error: {e}")
                await asyncio.sleep(10)
        
        await self.bot.change_presence(activity=None, status=discord.Status.online)


def setup(bot):
    """Cog setup function."""
    try:
        token = bot.http.token
    except:
        with open("config.json", 'r') as f:
            token = json.load(f).get('token')
    
    bot.add_cog(presence(bot, token))
