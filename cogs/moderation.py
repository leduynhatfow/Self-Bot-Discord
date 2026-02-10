"""
Moderation & Server Management Cog
Commands for server moderation and management
"""

import discord
from discord.ext import commands
import asyncio

class moderation(commands.Cog):
    """Moderation and server management commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ==================== MODERATION COMMANDS ====================
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = None):
        """Usage: {prefix}kick <member> [reason]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            await member.kick(reason=reason)
            await ctx.send(f"✅ Đã kick {member.mention} | Lý do: {reason or 'Không có'}")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền kick.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str = None):
        """Usage: {prefix}ban <member> [reason]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            await member.ban(reason=reason)
            await ctx.send(f"✅ Đã ban {member.mention} | Lý do: {reason or 'Không có'}")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền ban.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='banid')
    @commands.has_permissions(ban_members=True)
    async def ban_by_id(self, ctx, user_id: int, *, reason: str = None):
        """Usage: {prefix}banid <user_id> [reason]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(f"✅ Đã ban {user.name} (ID: {user_id}) | Lý do: {reason or 'Không có'}")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền ban.")
        except discord.NotFound:
            await ctx.send("❌ Không tìm thấy user với ID này.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban_user(self, ctx, user_id: int):
        """Usage: {prefix}unban <user_id>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Đã unban {user.name} (ID: {user_id})")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền unban.")
        except discord.NotFound:
            await ctx.send("❌ User này không bị ban.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='hide')
    @commands.has_permissions(manage_channels=True)
    async def hide_channel(self, ctx):
        """Usage: {prefix}hide"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.send(f"✅ Đã ẩn {ctx.channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền manage channels.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='unhide')
    @commands.has_permissions(manage_channels=True)
    async def unhide_channel(self, ctx):
        """Usage: {prefix}unhide"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
            await ctx.send(f"✅ Đã hiện {ctx.channel.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền manage channels.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='nuke')
    @commands.has_permissions(manage_channels=True)
    async def nuke_channel(self, ctx):
        """Usage: {prefix}nuke"""
        try:
            channel = ctx.channel
            position = channel.position
            category = channel.category
            
            new_channel = await channel.clone()
            await new_channel.edit(position=position, category=category)
            await channel.delete()
            
            await new_channel.send("💥 **Channel đã được nuke!**")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền manage channels.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='nukesrv')
    @commands.has_permissions(administrator=True)
    async def nuke_server(self, ctx):
        """Usage: {prefix}nukesrv"""
        await ctx.send("⚠️ **Bạn có chắc muốn nuke server? Gõ `confirm` trong 10s để tiếp tục.**")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "confirm"
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10.0)
        except asyncio.TimeoutError:
            await ctx.send("✅ Đã hủy nuke.")
            return
        
        try:
            for channel in ctx.guild.channels:
                try:
                    await channel.delete()
                except:
                    pass
            
            for i in range(18):
                try:
                    await ctx.guild.create_text_channel('😈nuked-by-bot😈')
                except:
                    pass
            
            await ctx.send("💥 **Server đã được nuke!**")
        except Exception as e:
            print(f"Nuke error: {e}")
    
    # ==================== SERVER MANAGEMENT ====================
    
    @commands.command(name='create_channel')
    @commands.has_permissions(manage_channels=True)
    async def create_channel(self, ctx, channel_name: str, category: str = None):
        """Usage: {prefix}create_channel <channel_name> [category]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            cat = None
            if category:
                cat = discord.utils.get(ctx.guild.categories, name=category)
                if not cat:
                    cat = await ctx.guild.create_category(category)
            
            await ctx.guild.create_text_channel(name=channel_name, category=cat)
            await ctx.send(f"✅ Đã tạo channel **{channel_name}**")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền manage channels.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='create_role')
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, role_name: str, color: str = None):
        """Usage: {prefix}create_role <role_name> [hex_color]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            role_color = discord.Color(int(color, 16)) if color else discord.Color.default()
            role = await ctx.guild.create_role(name=role_name, color=role_color)
            await ctx.send(f"✅ Đã tạo role **{role.name}**")
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền manage roles.")
        except ValueError:
            await ctx.send("❌ Màu không hợp lệ. Dùng hex code (vd: FF5733)")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.command(name='massdmfrnds')
    async def mass_dm_friends(self, ctx, *, message: str):
        """Usage: {prefix}massdmfrnds <message>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        success = 0
        failed = 0
        
        status_msg = await ctx.send("📤 **Đang gửi DM đến bạn bè...**")
        
        for user in self.bot.user.friends:
            try:
                await user.send(message)
                success += 1
                await asyncio.sleep(2)
            except:
                failed += 1
        
        await status_msg.edit(content=f"✅ **Hoàn tất!** Thành công: {success} | Thất bại: {failed}")
    
    @commands.command(name='leaveallgroups')
    async def leave_all_groups(self, ctx):
        """Usage: {prefix}leaveallgroups"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        count = 0
        for channel in self.bot.private_channels:
            if isinstance(channel, discord.GroupChannel):
                try:
                    await channel.leave()
                    count += 1
                except:
                    pass
        
        await ctx.send(f"✅ **Đã rời {count} group channels**")
    
    @commands.command(name='delallfriends')
    async def delete_all_friends(self, ctx):
        """Usage: {prefix}delallfriends"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("⚠️ **Bạn có chắc muốn xóa tất cả bạn bè? Gõ `yes` trong 10s.**")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10.0)
        except asyncio.TimeoutError:
            await ctx.send("✅ Đã hủy.")
            return
        
        count = 0
        for friend in self.bot.user.friends:
            try:
                await friend.remove_friend()
                count += 1
                await asyncio.sleep(1)
            except:
                pass
        
        await ctx.send(f"✅ **Đã xóa {count} bạn bè**")
    
    @commands.command(name='closealldms')
    async def close_all_dms(self, ctx):
        """Usage: {prefix}closealldms"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        count = 0
        for channel in self.bot.private_channels:
            if isinstance(channel, discord.DMChannel):
                try:
                    await channel.close()
                    count += 1
                except:
                    pass
        
        await ctx.send(f"✅ **Đã đóng {count} DM channels**")

def setup(bot):
    """Setup function for cog."""
    bot.add_cog(moderation(bot))
