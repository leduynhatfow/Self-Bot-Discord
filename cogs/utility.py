"""
Utility Commands Cog
Miscellaneous utility tools with built-in English instructions.
"""

import discord
from discord.ext import commands
import aiohttp
import asyncio
from urllib.parse import quote
from googletrans import Translator, LANGUAGES
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from src.clone import CloneHandler
    CLONE_AVAILABLE = True
except ImportError:
    CLONE_AVAILABLE = False
    print("⚠️ Clone module not available")

class utility(commands.Cog):
    """Utility and miscellaneous commands for daily use."""
    
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        self.weather_api_key = 'a9f8e695f7a349ae896144208250701'

    # ==================== WEATHER ====================
    
    @commands.command(name='weather', aliases=['wth'])
    async def get_weather(self, ctx, *, location: str):
        """Usage: {prefix}weather <city_name>"""
        try: await ctx.message.delete()
        except: pass
        
        try:
            url = f'http://api.weatherapi.com/v1/current.json?key={self.weather_api_key}&q={quote(location)}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return await ctx.send(f"❌ Location `{location}` not found.")
                    
                    data = await response.json()
                    temp = data["current"]["temp_c"]
                    cond = data["current"]["condition"]["text"]
                    
                    await ctx.send(f"**🌤️ WEATHER: {location.upper()}**\nTemp: {temp}°C | Condition: {cond}")
        except Exception as e:
            await ctx.send(f"❌ Weather error: {e}")

    # ==================== IMAGE GENERATION ====================
    
    @commands.command(name='genimg1')
    async def gen_image_1(self, ctx, *, prompt: str):
        """Usage: {prefix}genimg1 <description>"""
        try: await ctx.message.delete()
        except: pass
        url = f'https://image.pollinations.ai/prompt/{quote(prompt)}'
        await ctx.send(f"🎨 **AI Generated:** `{prompt}`\n{url}")

    @commands.command(name='genimg2')
    async def gen_image_2(self, ctx, *, query: str):
        """Usage: {prefix}genimg2 <keyword>"""
        try: await ctx.message.delete()
        except: pass
        headers = {'Authorization': 'Client-ID F1kSmh4MALfMKjHRxk38dZmPEV0OxsHdzuruBS_Y7to'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.unsplash.com/search/photos?query={quote(query)}&per_page=1", headers=headers) as resp:
                data = await resp.json()
                if not data['results']: return await ctx.send("❌ No image found.")
                await ctx.send(f"📸 **Photo for:** `{query}`\n{data['results'][0]['urls']['regular']}")

    # ==================== CHECKERS ====================
    
    @commands.command(name='checktoken')
    async def check_token(self, ctx, token: str):
        """Usage: {prefix}checktoken <token>"""
        try: await ctx.message.delete()
        except: pass
        r = requests.get("https://discord.com/api/v10/users/@me", headers={'Authorization': token})
        if r.status_code == 200:
            u = r.json()
            await ctx.send(f"✅ **Valid Token:** `{u['username']}#{u.get('discriminator', '0')}`")
        else:
            await ctx.send("❌ Invalid Token.")

    @commands.command(name='checkpromo')
    async def check_promo(self, ctx, *, promo: str):
        """Usage: {prefix}checkpromo <link_or_code>"""
        try: await ctx.message.delete()
        except: pass
        code = promo.split('/')[-1].strip()
        url = f'https://ptb.discord.com/api/v10/entitlements/gift-codes/{code}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                status = "VALID/AVAILABLE" if r.status in [200, 201, 204] else "INVALID/CLAIMED"
                await ctx.send(f"**Code:** `{code}` | **Status:** {status}")

    # ==================== EMOJI MANAGEMENT ====================
    
    @commands.command(name='emoji_copy')
    @commands.has_permissions(manage_emojis=True)
    async def copy_emojis(self, ctx, source_id: int, target_id: int):
        """Usage: {prefix}emoji_copy <source_server_id> <target_server_id>"""
        try: await ctx.message.delete()
        except: pass
        source = self.bot.get_guild(source_id)
        target = self.bot.get_guild(target_id)
        if not source or not target: return await ctx.send("❌ Server not found.")
        
        await ctx.send(f"📤 **Copying {len(source.emojis)} emojis...**")
        count = 0
        async with aiohttp.ClientSession() as session:
            for e in source.emojis:
                try:
                    async with session.get(str(e.url)) as r:
                        await target.create_custom_emoji(name=e.name, image=await r.read())
                        count += 1
                        await asyncio.sleep(1.5)
                except: continue
        await ctx.send(f"✅ **Done!** Copied {count} emojis to {target.name}.")

    @commands.command(name='emoji_add')
    @commands.has_permissions(manage_emojis=True)
    async def add_emoji(self, ctx, source_id: int, target_id: int, emoji_id: int):
        """Usage: {prefix}emoji_add <source_server_id> <target_server_id> <emoji_id>"""
        try: await ctx.message.delete()
        except: pass
        source = self.bot.get_guild(source_id)
        target = self.bot.get_guild(target_id)
        if not source or not target: return await ctx.send("❌ Server not found.")
        
        emoji = discord.utils.get(source.emojis, id=emoji_id)
        if not emoji: return await ctx.send(f"❌ Emoji ID `{emoji_id}` not found in {source.name}.")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(emoji.url)) as r:
                    new = await target.create_custom_emoji(name=emoji.name, image=await r.read())
            await ctx.send(f"✅ **Added:** {new} (`{emoji.name}`) to {target.name}")
        except Exception as e:
            await ctx.send(f"❌ Error adding emoji: {e}")

    # ==================== SERVER CLONE ====================
    
    @commands.command(name='server_clone', aliases=['csrv', 'cloneserver'])
    async def clone_server(self, ctx, source_id: int, target_id: int):
        """Usage: {prefix}server_clone <source_id> <target_id>"""
        if not CLONE_AVAILABLE:
            return await ctx.send("❌ Clone module không khả dụng!")
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        source_guild = self.bot.get_guild(source_id)
        target_guild = self.bot.get_guild(target_id)
        
        if not source_guild:
            return await ctx.send(f"❌ Không tìm thấy source server (ID: {source_id})")
        
        if not target_guild:
            return await ctx.send(f"❌ Không tìm thấy target server (ID: {target_id})")
        
        required_perms = ['manage_roles', 'manage_channels', 'manage_guild']
        missing_perms = [p for p in required_perms if not getattr(target_guild.me.guild_permissions, p, False)]
        
        if missing_perms:
            return await ctx.send(f"❌ **Bot thiếu quyền trong target server:**\n• {', '.join(missing_perms)}")
        
        confirm_msg = await ctx.send(
            f"⚠️ **XÁC NHẬN CLONE SERVER**\n"
            f"📤 **Source:** {source_guild.name} ({source_id})\n"
            f"📥 **Target:** {target_guild.name} ({target_id})\n\n"
            f"❗ **Cảnh báo:** Toàn bộ nội dung trong target server sẽ bị **XÓA**\n\n"
            f"Gõ `confirm` trong 15 giây để tiếp tục..."
        )
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "confirm"
        
        try:
            await self.bot.wait_for('message', check=check, timeout=15.0)
        except asyncio.TimeoutError:
            return await confirm_msg.edit(content="⏱️ **Đã hết thời gian - Hủy clone**")
        
        status_msg = await ctx.send("🔄 **Đang khởi tạo clone server...**")
        handler = CloneHandler()
        
        try:
            await status_msg.edit(content="🔄 **[1/6]** Đang clone thông tin server...")
            await handler.guild_edit(target_guild, source_guild)
            await asyncio.sleep(2)
            
            await status_msg.edit(content="🔄 **[2/6]** Đang xóa roles cũ...")
            await handler.roles_delete(target_guild)
            await asyncio.sleep(2)
            
            await status_msg.edit(content="🔄 **[3/6]** Đang xóa channels cũ...")
            await handler.channels_delete(target_guild)
            await asyncio.sleep(2)
            
            await status_msg.edit(content="🔄 **[4/6]** Đang tạo roles...")
            await handler.roles_create(target_guild, source_guild)
            await asyncio.sleep(2)
            
            await status_msg.edit(content="🔄 **[5/6]** Đang tạo categories...")
            await handler.categories_create(target_guild, source_guild)
            await asyncio.sleep(2)
            
            await status_msg.edit(content="🔄 **[6/6]** Đang tạo channels...")
            await handler.channels_create(target_guild, source_guild)
            
            roles_count = len([r for r in target_guild.roles if r.name != "@everyone"])
            channels_count = len(target_guild.channels)
            categories_count = len(target_guild.categories)
            
            await status_msg.edit(content=
                f"✅ **CLONE SERVER HOÀN TẤT!**\n"
                f"📤 **Source:** {source_guild.name}\n"
                f"📥 **Target:** {target_guild.name}\n\n"
                f"**📊 Kết quả:**\n"
                f"• Roles: {roles_count}\n"
                f"• Categories: {categories_count}\n"
                f"• Channels: {channels_count}\n\n"
                f"**⚠️ Lưu ý:**\n"
                f"• Emojis không được clone (dùng `{ctx.prefix}emoji_copy`)\n"
                f"• Webhooks phải tạo lại"
            )
            
        except Exception as e:
            await status_msg.edit(content=f"❌ **Lỗi clone server:** {e}")
            print(f"[CLONE] ❌ Error: {e}")

    @commands.command(name='quick_clone', aliases=['qclone'])
    async def quick_clone(self, ctx, source_id: int, target_id: int):
        """Usage: {prefix}quick_clone <source_id> <target_id>"""
        if not CLONE_AVAILABLE:
            return await ctx.send("❌ Clone module không khả dụng!")
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        source_guild = self.bot.get_guild(source_id)
        target_guild = self.bot.get_guild(target_id)
        
        if not source_guild or not target_guild:
            return await ctx.send("❌ Không tìm thấy server!")
        
        status_msg = await ctx.send("⚡ **Đang quick clone...**")
        handler = CloneHandler()
        
        try:
            await status_msg.edit(content="⚡ **[1/3]** Đang tạo roles...")
            await handler.roles_create(target_guild, source_guild)
            
            await status_msg.edit(content="⚡ **[2/3]** Đang tạo categories...")
            await handler.categories_create(target_guild, source_guild)
            
            await status_msg.edit(content="⚡ **[3/3]** Đang tạo channels...")
            await handler.channels_create(target_guild, source_guild)
            
            await status_msg.edit(content="✅ **Quick clone hoàn tất!**")
            
        except Exception as e:
            await status_msg.edit(content=f"❌ **Lỗi:** {e}")
            print(f"[CLONE] ❌ Error: {e}")

def setup(bot):
    bot.add_cog(utility(bot))
