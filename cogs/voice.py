"""
Voice Channel Management - SIMPLE VERSION
"""

import discord
from discord.ext import commands
import asyncio
import json
from typing import Dict, Optional
from datetime import datetime

class VoiceClient:    
    def __init__(self, token: str, token_index: int):
        self.token = token.strip()
        self.token_index = token_index
        self.client = None
        self.username = "Unknown"
        self.channel_name = "Unknown"
        self.guild_name = "Unknown"
        self.connected_at = None
    
    async def initialize(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        
        self.client = discord.Client(intents=intents)
        
        @self.client.event
        async def on_ready():
            self.username = str(self.client.user)
            print(f"✅ Token #{self.token_index} ready: {self.username}")
        
        try:
            asyncio.create_task(self.client.start(self.token, bot=False))
            
            for _ in range(30):
                await asyncio.sleep(0.5)
                if self.client.user:
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Init failed: {e}")
            return False
    
    async def connect(self, channel_id: int, max_retries: int = 3):
        for attempt in range(1, max_retries + 1):
            try:
                channel = self.client.get_channel(channel_id)
                if not channel:
                    return False
                
                self.channel_name = channel.name
                self.guild_name = channel.guild.name
                
                if channel.guild.voice_client:
                    await channel.guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(1)
                
                vc = await channel.connect(timeout=15.0, reconnect=False)
                
                # Self-deafen
                try:
                    await channel.guild.change_voice_state(
                        channel=channel,
                        self_mute=False,
                        self_deaf=True
                    )
                except:
                    pass
                
                if vc and vc.is_connected():
                    self.connected_at = datetime.now()
                    print(f"✅ Token #{self.token_index} connected (attempt {attempt})")
                    return True
                
            except Exception as e:
                if "already connected" in str(e).lower():
                    print(f"✅ Token #{self.token_index} already in voice")
                    self.connected_at = datetime.now()
                    return True
                
                print(f"❌ Attempt {attempt}/{max_retries} failed: {e}")
                
                if attempt < max_retries:
                    await asyncio.sleep(2)
        
        return False
    
    async def disconnect(self, max_retries: int = 3):
        for attempt in range(1, max_retries + 1):
            try:
                if not self.client:
                    return
                
                disconnected = False
                
                for guild in self.client.guilds:
                    if guild.voice_client and guild.voice_client.is_connected():
                        await guild.voice_client.disconnect(force=True)
                        print(f"✅ Disconnected from {guild.name} (attempt {attempt})")
                        disconnected = True
                
                await asyncio.sleep(1)
                
                still_connected = False
                for guild in self.client.guilds:
                    if guild.voice_client and guild.voice_client.is_connected():
                        still_connected = True
                        break
                
                if not still_connected:
                    print(f"✅ All connections closed")
                    return
                
                if attempt < max_retries:
                    print(f"⚠️ Still connected, retrying...")
                    await asyncio.sleep(2)
            
            except Exception as e:
                print(f"❌ Disconnect attempt {attempt}/{max_retries} error: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2)
    
    async def cleanup(self):
        await self.disconnect()
        if self.client:
            try:
                await self.client.close()
            except:
                pass
    
    def is_connected(self):
        if not self.client:
            return False
        
        for guild in self.client.guilds:
            if guild.voice_client and guild.voice_client.is_connected():
                return True
        
        return False


class voice(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.clients: Dict[int, VoiceClient] = {}
        self._load_config()
    
    def _load_config(self):
        """Load tokens."""
        try:
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.tokens = [t.strip() for t in config.get('voice_token', [])]
        except Exception as e:
            print(f"❌ Load config failed: {e}")
            self.tokens = []
    
    @commands.command(name='joinvoice')
    async def join_voice(self, ctx, channel_id: int, token_index: int = 0):
        """
        Usage: !joinvoice <channel_id> [token_index]
        """
        try:
            await ctx.message.delete()
        except:
            pass
        
        if not self.tokens:
            await ctx.send("❌ No tokens in config!")
            return
        
        if token_index >= len(self.tokens):
            await ctx.send(f"❌ Invalid index! Max: {len(self.tokens)-1}")
            return
        
        if token_index in self.clients:
            await ctx.send(f"⚠️ Token #{token_index} already in use!")
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ Channel not found!")
            return
        
        msg = await ctx.send(f"🔄 Connecting token #{token_index}...")
        
        vc = VoiceClient(self.tokens[token_index], token_index)
        
        if not await vc.initialize():
            await msg.edit(content="❌ Failed to initialize")
            return

        vc.channel_name = channel.name
        vc.guild_name = channel.guild.name
        vc.connected_at = datetime.now()
        self.clients[token_index] = vc
        
        await asyncio.sleep(1)
        
        if await vc.connect(channel_id):
            await msg.edit(content=f"✅ Token #{token_index} (`{vc.username}`) joined `{channel.name}`")
        else:
            await msg.edit(content=f"⚠️ Token #{token_index} (`{vc.username}`) added to status (connection may have failed)")
    
    @commands.command(name='leavevoice')
    async def leave_voice(self, ctx, token_index: int):
        """
        Usage: !leavevoice <token_index>
        """
        try:
            await ctx.message.delete()
        except:
            pass
        
        if token_index >= len(self.tokens):
            await ctx.send(f"❌ Invalid index! Max: {len(self.tokens)-1}")
            return
        
        msg = await ctx.send(f"🔄 Disconnecting token #{token_index}...")
        
        if token_index in self.clients:
            vc = self.clients[token_index]
            username = vc.username
            
            await vc.disconnect()
            await vc.cleanup()
            
            del self.clients[token_index]
            
            await msg.edit(content=f"✅ Token #{token_index} (`{username}`) disconnected and removed")
            return
        
        print(f"[INFO] Token #{token_index} not in tracking, attempting direct disconnect...")
        
        temp_vc = VoiceClient(self.tokens[token_index], token_index)
        
        if await temp_vc.initialize():
            await asyncio.sleep(1)
            await temp_vc.disconnect()
            await temp_vc.cleanup()
            await msg.edit(content=f"✅ Token #{token_index} disconnect attempted (was not in tracking)")
        else:
            await msg.edit(content=f"⚠️ Token #{token_index} could not initialize for disconnect")
    
    @commands.command(name='statusvoice')
    async def status_voice(self, ctx):
        """
        Usage: !statusvoice
        """
        try:
            await ctx.message.delete()
        except:
            pass
        
        if not self.clients:
            await ctx.send(
                f"🎙️ **Voice Status**\n"
                f"❌ No connections\n"
                f"📋 {len(self.tokens)} tokens available"
            )
            return
        
        status = f"🎙️ **Voice Status** ({len(self.clients)} active)\n\n"
        
        for idx in sorted(self.clients.keys()):
            vc = self.clients[idx]
            
            is_conn = vc.is_connected()
            emoji = "🟢" if is_conn else "🔴"
            
            uptime = ""
            if vc.connected_at:
                elapsed = datetime.now() - vc.connected_at
                mins = int(elapsed.total_seconds() // 60)
                uptime = f" ({mins}m)"
            
            status += (
                f"{emoji} **Token #{idx}** - `{vc.username}`\n"
                f"   └ {vc.channel_name} • {vc.guild_name}{uptime}\n"
            )
        
        await ctx.send(status)
    
    @commands.command(name='reloadvoicetokens')
    async def reload_tokens(self, ctx):
        """
        Usage: !reloadvoicetokens
        """
        try:
            await ctx.message.delete()
        except:
            pass
        
        old = len(self.tokens)
        self._load_config()
        await ctx.send(f"✅ Reloaded: {old} → {len(self.tokens)}")
    
    def cog_unload(self):
        for vc in self.clients.values():
            asyncio.create_task(vc.cleanup())


def setup(bot):
    bot.add_cog(voice(bot))
