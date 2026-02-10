"""
General Commands Cog
Basic utility and information commands for general use.
"""

import discord
from discord.ext import commands
import asyncio
from datetime import datetime


class general(commands.Cog):
    """General utility commands for bot and user information."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='selfbot', aliases=['info', 'about'])
    async def selfbot_info(self, ctx):
        """Usage: {prefix}selfbot"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m" if uptime else "N/A"
        
        info = f"""**🤖 BOT INFORMATION**
━━━━━━━━━━━━━━━━━━━━━━━━
**Name:** {self.bot.user.name}
**ID:** {self.bot.user.id}
**Prefix:** {self.bot.command_prefix}
**Servers:** {len(self.bot.guilds)}
**Commands:** {len(self.bot.commands)}
**Cogs Active:** {len(self.bot.cogs)}
**Uptime:** {uptime_str}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        await ctx.send(info)
    
    @commands.command(name='clear', aliases=['purge'])
    async def clear_messages(self, ctx, amount: int = 10):
        """Usage: {prefix}clear [amount]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if amount <= 0:
            await ctx.send("❌ Amount must be greater than 0.")
            return
        
        try:
            deleted = 0
            async for message in ctx.channel.history(limit=amount * 2):
                if message.author.id == self.bot.user.id:
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.5) # Sleep to avoid rate limits
                    
                    if deleted >= amount:
                        break
            
            status_msg = await ctx.send(f"✅ Successfully deleted {deleted} messages.")
            await asyncio.sleep(3)
            await status_msg.delete()
            
        except discord.Forbidden:
            await ctx.send("❌ Missing permissions to delete messages.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='spam')
    async def spam_message(self, ctx, times: int, *, message: str):
        """Usage: {prefix}spam <times> <message>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if times <= 0 or times > 20:
            await ctx.send("❌ Please provide a count between 1 and 20.")
            return
        
        try:
            for _ in range(times):
                await ctx.send(message)
                await asyncio.sleep(0.5)
        except discord.Forbidden:
            await ctx.send("❌ Cannot send messages: Missing permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='dm')
    async def send_dm(self, ctx, user: discord.User, *, message: str):
        """Usage: {prefix}dm <user> <message>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            await user.send(message)
            await ctx.send(f"✅ DM sent to {user.name}")
        except discord.Forbidden:
            await ctx.send(f"❌ Could not DM {user.name} (DMs might be closed).")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='srvinfo', aliases=['serverinfo'])
    async def server_info(self, ctx):
        """Usage: {prefix}srvinfo"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ This command can only be used within a server.")
            return
        
        info = f"""**📊 SERVER INFORMATION**
━━━━━━━━━━━━━━━━━━━━━━━━
**Name:** {guild.name}
**ID:** {guild.id}
**Owner:** {guild.owner.mention if guild.owner else 'N/A'}
**Members:** {guild.member_count}
**Channels:** {len(guild.channels)}
**Roles:** {len(guild.roles)}
**Created on:** {guild.created_at.strftime('%B %d, %Y')}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        await ctx.send(info)
    
    @commands.command(name='userinfo', aliases=['user_info', 'whois'])
    async def user_info(self, ctx, member: discord.Member = None):
        """Usage: {prefix}userinfo [member]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        member = member or ctx.author
        
        info = f"""**👤 USER INFORMATION**
━━━━━━━━━━━━━━━━━━━━━━━━
**Username:** {member.name}
**Discriminator:** #{member.discriminator}
**ID:** {member.id}
**Nickname:** {member.nick or 'None'}
**Top Role:** {member.top_role.name}
**Account Created:** {member.created_at.strftime('%B %d, %Y')}
**Joined Server:** {member.joined_at.strftime('%B %d, %Y') if member.joined_at else 'N/A'}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        await ctx.send(info)
    
def setup(bot):
    bot.add_cog(general(bot))
