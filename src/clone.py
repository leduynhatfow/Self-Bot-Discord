"""
Clone Module
Xử lý clone server Discord
"""

import discord
import asyncio
from typing import Optional

class CloneHandler:
    """Class xử lý clone server."""
    
    @staticmethod
    async def guild_edit(guild_to: discord.Guild, guild_from: discord.Guild):
        """Clone thông tin server (name, icon)."""
        if not guild_to.me.guild_permissions.manage_guild:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Guild' trong {guild_to.name}")
            return False
        
        try:
            await guild_to.edit(name=guild_from.name)
            print(f"[CLONE] ✅ Đã đổi tên server thành: {guild_from.name}")
            
            if guild_from.icon_url:
                try:
                    icon_bytes = await guild_from.icon_url.read()
                    await guild_to.edit(icon=icon_bytes)
                    print(f"[CLONE] ✅ Đã clone icon server")
                except Exception as e:
                    print(f"[CLONE] ⚠️ Không thể clone icon: {e}")
            
            return True
            
        except discord.Forbidden:
            print(f"[CLONE] ❌ Thiếu quyền edit server {guild_to.name}")
            return False
        except Exception as e:
            print(f"[CLONE] ❌ Lỗi edit server: {e}")
            return False

    @staticmethod
    async def roles_delete(guild_to: discord.Guild):
        """Xóa tất cả roles trong server."""
        if not guild_to.me.guild_permissions.manage_roles:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Roles' trong {guild_to.name}")
            return False
        
        deleted_count = 0
        for role in guild_to.roles:
            if role.name == "@everyone":
                continue
            
            try:
                await role.delete()
                deleted_count += 1
                print(f"[CLONE] 🗑️ Đã xóa role: {role.name}")
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể xóa role: {role.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi xóa role {role.name}: {e}")
        
        print(f"[CLONE] ✅ Đã xóa {deleted_count} roles")
        return True

    @staticmethod
    async def channels_delete(guild_to: discord.Guild):
        """Xóa tất cả channels trong server."""
        if not guild_to.me.guild_permissions.manage_channels:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Channels' trong {guild_to.name}")
            return False
        
        deleted_count = 0
        for channel in guild_to.channels:
            try:
                await channel.delete()
                deleted_count += 1
                print(f"[CLONE] 🗑️ Đã xóa channel: {channel.name}")
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể xóa channel: {channel.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi xóa channel {channel.name}: {e}")
        
        print(f"[CLONE] ✅ Đã xóa {deleted_count} channels")
        return True

    @staticmethod
    async def roles_create(guild_to: discord.Guild, guild_from: discord.Guild):
        """Tạo roles từ server nguồn."""
        if not guild_to.me.guild_permissions.manage_roles:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Roles' trong {guild_to.name}")
            return False
        
        roles = [role for role in guild_from.roles if role.name != "@everyone"]
        roles.reverse()
        
        created_count = 0
        for role in roles:
            try:
                await guild_to.create_role(
                    name=role.name,
                    permissions=role.permissions,
                    colour=role.colour,
                    hoist=role.hoist,
                    mentionable=role.mentionable
                )
                created_count += 1
                print(f"[CLONE] ➕ Đã tạo role: {role.name}")
                await asyncio.sleep(0.8)
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể tạo role: {role.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi tạo role {role.name}: {e}")
        
        print(f"[CLONE] ✅ Đã tạo {created_count}/{len(roles)} roles")
        return True

    @staticmethod
    async def categories_create(guild_to: discord.Guild, guild_from: discord.Guild):
        """Tạo categories từ server nguồn."""
        if not guild_to.me.guild_permissions.manage_channels:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Channels' trong {guild_to.name}")
            return False
        
        created_count = 0
        for category in guild_from.categories:
            try:
                overwrites_to = {}
                for key, value in category.overwrites.items():
                    if isinstance(key, discord.Role):
                        role = discord.utils.get(guild_to.roles, name=key.name)
                        if role:
                            overwrites_to[role] = value
                
                new_category = await guild_to.create_category(
                    name=category.name,
                    overwrites=overwrites_to
                )
                
                try:
                    await new_category.edit(position=category.position)
                except:
                    pass
                
                created_count += 1
                print(f"[CLONE] 📁 Đã tạo category: {category.name}")
                await asyncio.sleep(0.8)
                
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể tạo category: {category.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi tạo category {category.name}: {e}")
        
        print(f"[CLONE] ✅ Đã tạo {created_count}/{len(guild_from.categories)} categories")
        return True

    @staticmethod
    async def channels_create(guild_to: discord.Guild, guild_from: discord.Guild):
        """Tạo text và voice channels từ server nguồn."""
        if not guild_to.me.guild_permissions.manage_channels:
            print(f"[CLONE] ❌ Bot thiếu quyền 'Manage Channels' trong {guild_to.name}")
            return False
        
        text_created = 0
        voice_created = 0
        
        # ========== TEXT CHANNELS ==========
        for channel_text in guild_from.text_channels:
            try:
                category = None
                if channel_text.category:
                    category = discord.utils.get(guild_to.categories, name=channel_text.category.name)
                
                overwrites_to = {}
                for key, value in channel_text.overwrites.items():
                    if isinstance(key, discord.Role):
                        role = discord.utils.get(guild_to.roles, name=key.name)
                        if role:
                            overwrites_to[role] = value
                
                new_channel = await guild_to.create_text_channel(
                    name=channel_text.name,
                    overwrites=overwrites_to,
                    position=channel_text.position,
                    topic=channel_text.topic,
                    slowmode_delay=channel_text.slowmode_delay,
                    nsfw=channel_text.nsfw,
                    category=category
                )
                
                text_created += 1
                print(f"[CLONE] 💬 Đã tạo text channel: {channel_text.name}")
                await asyncio.sleep(0.8)
                
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể tạo text channel: {channel_text.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi tạo text channel {channel_text.name}: {e}")
        
        # ========== VOICE CHANNELS ==========
        for channel_voice in guild_from.voice_channels:
            try:
                category = None
                if channel_voice.category:
                    category = discord.utils.get(guild_to.categories, name=channel_voice.category.name)
                
                # Map overwrites
                overwrites_to = {}
                for key, value in channel_voice.overwrites.items():
                    if isinstance(key, discord.Role):
                        role = discord.utils.get(guild_to.roles, name=key.name)
                        if role:
                            overwrites_to[role] = value
                
                new_channel = await guild_to.create_voice_channel(
                    name=channel_voice.name,
                    overwrites=overwrites_to,
                    position=channel_voice.position,
                    bitrate=channel_voice.bitrate,
                    user_limit=channel_voice.user_limit,
                    category=category
                )
                
                voice_created += 1
                print(f"[CLONE] 🔊 Đã tạo voice channel: {channel_voice.name}")
                await asyncio.sleep(0.8)
                
            except discord.Forbidden:
                print(f"[CLONE] ⚠️ Không thể tạo voice channel: {channel_voice.name}")
            except Exception as e:
                print(f"[CLONE] ⚠️ Lỗi tạo voice channel {channel_voice.name}: {e}")
        
        print(f"[CLONE] ✅ Đã tạo {text_created} text channels và {voice_created} voice channels")
        return True
