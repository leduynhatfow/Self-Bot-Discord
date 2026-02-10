"""
Auto Reactions Cog - Auto react with emojis
- Auto react for specific user or @everyone
- Bomb reactions (20 emojis)
- Custom reactions
"""

from typing import Optional, Union
import discord
from discord.ext import commands
import asyncio


class reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_react_user: Optional[Union[discord.User, str]] = None
        self.auto_react_emojis: Optional[str] = None
        self.auto_react_channel: Optional[discord.TextChannel] = None

    async def convert_to_emoji(self, emoji_str: str) -> Union[discord.Emoji, str]:
        """Converts a string to a discord.Emoji object if it's a custom emoji, else returns the string."""
        if emoji_str.startswith("<:") and emoji_str.endswith(">"):
            emoji_id = int(emoji_str.split(":")[-1][:-1])
            emoji = self.bot.get_emoji(emoji_id)
            return emoji or emoji_str
        return emoji_str

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listens for messages and reacts with the auto react emojis if set."""
        if message.author.id == self.bot.user.id:
            return
            
        if self.auto_react_emojis and self.auto_react_user:
            if (
                self.auto_react_user == "@everyone"
                or message.author == self.auto_react_user
            ):
                if self.auto_react_channel:
                    if message.channel != self.auto_react_channel:
                        return
                    
                for emoji in self.auto_react_emojis.split():
                    try:
                        emoji_obj = await self.convert_to_emoji(emoji)
                        await message.add_reaction(emoji_obj)
                        await asyncio.sleep(0.3)
                    except discord.HTTPException as e:
                        print(f"❌ [AUTO REACT] Failed to add: {emoji} - {e}")
                    except Exception as e:
                        print(f"❌ [AUTO REACT] Error: {e}")

    @commands.command(name='auto_react')
    async def auto_react(self, ctx, user: str, *, emojis: str) -> None:
        """Usage: {prefix}auto_react <@user/all> <emojis>"""
        try:
            await ctx.message.delete()
        except:
            pass

        if user.lower() == "all":
            self.auto_react_user = "@everyone"
            self.auto_react_channel = ctx.channel
            user_display = "@everyone"
        else:
            try:
                self.auto_react_channel = None
                user_obj = await commands.UserConverter().convert(ctx, user)
                self.auto_react_user = user_obj
                user_display = str(user_obj)
            except commands.UserNotFound:
                temp_message = await ctx.send(
                    f"**❌ User `{user}` not found**\n\n"
                    f"**Usage:**\n"
                    f"`.auto_react @user 🔥 💀`\n"
                    f"`.auto_react all 🔥 💀`"
                )
                await asyncio.sleep(5)
                await temp_message.delete()
                return
            except Exception as e:
                temp_message = await ctx.send(f"**❌ Error:** `{e}`")
                await asyncio.sleep(3)
                await temp_message.delete()
                return

        self.auto_react_emojis = emojis
        
        if user.lower() == "all":
            temp_message = await ctx.send(
                f"**✅ Auto React Enabled**\n"
                f"📝 Channel: `#{ctx.channel.name}`\n"
                f"👤 Target: `Everyone in this channel`\n"
                f"😀 Emojis: {emojis}"
            )
        else:
            temp_message = await ctx.send(
                f"**✅ Auto React Enabled**\n"
                f"👤 User: `{user_display}`\n"
                f"😀 Emojis: {emojis}"
            )
        
        await asyncio.sleep(3)
        await temp_message.delete()

    @commands.command(name='stop_react')
    async def stop_react(self, ctx) -> None:
        """Usage: {prefix}stop_react"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        self.auto_react_emojis = None
        self.auto_react_user = None
        self.auto_react_channel = None
        temp_message = await ctx.send("**✅ Auto react disabled**")
        await asyncio.sleep(3)
        await temp_message.delete()
    
    @commands.command(name='react_status')
    async def react_status(self, ctx) -> None:
        """Usage: {prefix}react_status"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if self.auto_react_user:
            user_str = str(self.auto_react_user) if self.auto_react_user != "@everyone" else "@everyone"
            channel_str = f"#{self.auto_react_channel.name}" if self.auto_react_channel else "All channels"
            
            temp_message = await ctx.send(
                f"**🎯 Auto React Status**\n\n"
                f"✅ **Enabled**\n"
                f"👤 User: `{user_str}`\n"
                f"📝 Channel: `{channel_str}`\n"
                f"😀 Emojis: {self.auto_react_emojis or 'None'}"
            )
            await asyncio.sleep(10)
            await temp_message.delete()
        else:
            temp_message = await ctx.send(
                f"**🎯 Auto React Status**\n\n"
                f"❌ **Disabled**\n\n"
                f"Use `.auto_react @user <emojis>` to enable"
            )
            await asyncio.sleep(5)
            await temp_message.delete()


def setup(bot):
    bot.add_cog(reactions(bot))
