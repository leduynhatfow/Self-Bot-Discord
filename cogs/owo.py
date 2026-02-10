"""
OwO Bot Automation Cog
Farm and bet automation via Discord commands
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
import sys
import os
import json
import aiohttp

# Import modules từ src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.owofarm import OwOFarm
from src.owobet import OwOBet

logger = logging.getLogger(__name__)

# =============== STATUS MANAGER ===============
class StatusManager:
    @staticmethod
    def update_status(function_name, identifier, active, **kwargs):
        """Cập nhật trạng thái function cho channel/token"""
        try:
            status_file = "data/bot_status.json"
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            
            try:
                with open(status_file, "r") as f:
                    status_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                status_data = {
                    "owo_farm": {},
                    "owo_bet": {},
                    "snipe_nitro": {},
                    "rotator": {"active": False}
                }
            
            if function_name not in status_data:
                status_data[function_name] = {}
            
            templates = {
                "owo_farm": {
                    "active": False,
                    "gems_used": 0,
                    "commands_sent": 0,
                    "banned": False
                },
                "owo_bet": {
                    "active": False,
                    "bets_placed": 0,
                    "profit": 0,
                    "banned": False
                }
            }
            
            if function_name in templates:
                if identifier not in status_data[function_name]:
                    status_data[function_name][identifier] = templates[function_name].copy()
                status_data[function_name][identifier].update({"active": active, **kwargs})
            
            # Save
            with open(status_file, "w") as f:
                json.dump(status_data, f, indent=4)
            
            logger.debug(f"Cập nhật status {function_name} ({identifier}): active={active}")
        except Exception as e:
            logger.error(f"Lỗi update status: {e}")

# =============== DISCORD MESSENGER ===============
class DiscordMessenger:
    @staticmethod
    async def send_message(channel_id, message, token):
        """Gửi message đến Discord channel"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers={
                        "Authorization": token,
                        "User-Agent": "Mozilla/5.0",
                        "Content-Type": "application/json"
                    },
                    json={"content": message}
                ) as response:
                    if response.status not in [200, 201, 204]:
                        text = await response.text()
                        logger.error(f"Gửi message thất bại: {response.status} - {text}")
        except Exception as e:
            logger.error(f"Lỗi gửi message: {e}")

# =============== WEBHOOK SENDER ===============
async def send_webhook(webhook_type, embed_data):
    """Gửi webhook với embed"""
    try:
        # Load webhooks từ config
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        webhooks = config.get("webhooks", {})
        url = webhooks.get(webhook_type)
        
        if not url:
            logger.debug(f"Không có webhook URL cho '{webhook_type}'")
            return False
        
        async with aiohttp.ClientSession() as session:
            payload = {"embeds": [embed_data]}
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status not in [200, 204]:
                    logger.error(f"Webhook {webhook_type} failed: {response.status}")
                    return False
                else:
                    logger.info(f"✅ Đã gửi webhook {webhook_type}")
                    return True
    except Exception as e:
        logger.error(f"Lỗi gửi webhook {webhook_type}: {e}")
        return False

class owo(commands.Cog):
    """OwO bot automation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.state = {
            "owo_mode": {},
            "owobet_mode": {},
            "commands_sent": {},
            "bets_placed": {},
            "gems_used": {},
            "banned": {},
            "stopped_by_command": {},
            "farming_session": {},
            "owo_tasks": {},
            "owobet_tasks": {}
        }
        self.status_manager = StatusManager()
        self.messenger = DiscordMessenger()
        
        self.captcha_solver = None
        try:
            import importlib.util
            
            captcha_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'solvecaptcha.py')
            
            if os.path.exists(captcha_path):
                spec = importlib.util.spec_from_file_location("solvecaptcha", captcha_path)
                solver_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(solver_module)
                
                self.captcha_solver = type('CaptchaSolver', (), {})()
                self.captcha_solver.GhoStySolveNormalCap = getattr(solver_module, 'GhoStySolveNormalCap', None)
                self.captcha_solver.GhoStySyncedCaptchaSolve = getattr(solver_module, 'GhoStySyncedCaptchaSolve', None)
                
                if self.captcha_solver.GhoStySolveNormalCap or self.captcha_solver.GhoStySyncedCaptchaSolve:
                    logger.info("✅ Captcha solver đã sẵn sàng")
                else:
                    logger.warning("⚠️ Không tìm thấy captcha solver functions")
                    self.captcha_solver = None
            else:
                logger.warning(f"⚠️ Không tìm thấy solvecaptcha.py tại {captcha_path}")
                self.captcha_solver = None
        except Exception as e:
            logger.error(f"❌ Lỗi load captcha solver: {e}")
            self.captcha_solver = None
    
    # ==================== OWO FARM ====================
    
    @commands.command(name='owo')
    async def owo_farm(self, ctx, index: int, mode: str, huntbot: str = "false", 
                       farming: str = "true", money: str = "10000"):
        """Usage: {prefix}owo <index> <on/off> [huntbot] [farming] [money]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        config = self.bot.config
        token_owo = config.get("token_owo", [])
        
        if index < 0 or index >= len(token_owo):
            await ctx.send(f"❌ Index {index} không hợp lệ. Có {len(token_owo)} token.", delete_after=10)
            return
        
        channel_token_pair = token_owo[index]
        channel_id, token = list(channel_token_pair.items())[0]
        channel = self.bot.get_channel(int(channel_id))
        
        if not channel:
            await ctx.send(f"❌ Không tìm thấy channel ID {channel_id}", delete_after=10)
            return
        
        mode = mode.lower() in ['on', 'true', '1', 'start']
        
        if mode:
            if str(channel_id) in self.state["owo_mode"] and self.state["owo_mode"][str(channel_id)]:
                await ctx.send(f"❌ Farm đang chạy cho channel {channel.mention}", delete_after=10)
                return
            
            self.state["banned"][str(channel_id)] = False
            self.state["stopped_by_command"][str(channel_id)] = False
            self.state["owo_mode"][str(channel_id)] = True
            
            farm = OwOFarm(
                channel_id=channel_id,
                token=token,
                config=config,
                state=self.state,
                messenger=self.messenger,
                status_manager=self.status_manager,
                webhook_sender=send_webhook,
                captcha_solver=self.captcha_solver  # ← TRUYỀN CAPTCHA SOLVER
            )
            
            task = asyncio.create_task(farm.farm_loop())
            self.state.setdefault("owo_tasks", {})[str(channel_id)] = [task]
            
            await ctx.send(
                f"✅ **OwO Farm ON** (index {index})\n"
                f"📍 Channel: {channel.mention}\n"
                f"🎯 Sử dụng schedule động 2 batch",
                delete_after=15
            )
            
            logger.info(f"🟢 Started farm for channel {channel_id}")
        
        else:
            if str(channel_id) not in self.state["owo_mode"] or not self.state["owo_mode"][str(channel_id)]:
                await ctx.send(f"❌ Farm không chạy cho channel {channel.mention}", delete_after=10)
                return
            
            self.state["owo_mode"][str(channel_id)] = False
            self.state["stopped_by_command"][str(channel_id)] = True
            
            tasks = self.state.get("owo_tasks", {}).get(str(channel_id), [])
            for task in tasks:
                try:
                    task.cancel()
                except:
                    pass
            
            self.state["owo_tasks"][str(channel_id)] = []
            
            await ctx.send(f"✅ **OwO Farm OFF** (index {index})", delete_after=10)
            logger.info(f"🔴 Stopped farm for channel {channel_id}")
    
    # ==================== OWO BET ====================
    
    @commands.command(name='owobet')
    async def owo_bet(self, ctx, index: int, enable: str = "true"):
        """Usage: {prefix}owobet <index> <on/off>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        config = self.bot.config
        token_owo = config.get("token_owo", [])
        
        if index < 0 or index >= len(token_owo):
            await ctx.send(f"❌ Index {index} không hợp lệ. Có {len(token_owo)} token.", delete_after=10)
            return
        
        channel_token_pair = token_owo[index]
        channel_id, token = list(channel_token_pair.items())[0]
        channel = self.bot.get_channel(int(channel_id))
        
        if not channel:
            await ctx.send(f"❌ Không tìm thấy channel ID {channel_id}", delete_after=10)
            return
        
        enable = enable.lower() in ['on', 'true', '1', 'start']
        
        if enable:
            if str(channel_id) in self.state["owobet_mode"] and self.state["owobet_mode"][str(channel_id)]:
                await ctx.send(f"❌ Bet đang chạy cho channel {channel.mention}", delete_after=10)
                return
            
            if str(channel_id) in self.state["owo_mode"] and self.state["owo_mode"][str(channel_id)]:
                await ctx.send(f"❌ Farm đang chạy cho channel này. Vui lòng dừng farm trước.", delete_after=10)
                return
            
            self.state["banned"][str(channel_id)] = False
            self.state["stopped_by_command"][str(channel_id)] = False
            self.state["owobet_mode"][str(channel_id)] = True
            
            bet = OwOBet(
                channel_id=channel_id,
                token=token,
                config=config,
                state=self.state,
                messenger=self.messenger,
                status_manager=self.status_manager,
                webhook_sender=send_webhook,
                captcha_solver=self.captcha_solver  # ← TRUYỀN CAPTCHA SOLVER
            )
            
            task = asyncio.create_task(bet.bet_loop())
            self.state.setdefault("owobet_tasks", {})[str(channel_id)] = [task]
            
            await ctx.send(
                f"✅ **OwO Bet ON** (index {index})\n"
                f"📍 Channel: {channel.mention}\n"
                f"🎰 Sử dụng Martingale strategy",
                delete_after=15
            )
            
            logger.info(f"🟢 Started bet for channel {channel_id}")
        
        else:
            if str(channel_id) not in self.state["owobet_mode"] or not self.state["owobet_mode"][str(channel_id)]:
                await ctx.send(f"❌ Bet không chạy cho channel {channel.mention}", delete_after=10)
                return
            
            self.state["owobet_mode"][str(channel_id)] = False
            self.state["stopped_by_command"][str(channel_id)] = True
            
            tasks = self.state.get("owobet_tasks", {}).get(str(channel_id), [])
            for task in tasks:
                try:
                    task.cancel()
                except:
                    pass
            
            self.state["owobet_tasks"][str(channel_id)] = []
            
            await ctx.send(f"✅ **OwO Bet OFF** (index {index})", delete_after=10)
            logger.info(f"🔴 Stopped bet for channel {channel_id}")
    
    # ==================== START ALL ====================
    
    @commands.command(name='owoall')
    async def owo_all(self, ctx, mode: str):
        """Usage: {prefix}owoall <on/off>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        config = self.bot.config
        token_owo = config.get("token_owo", [])
        
        if not token_owo:
            await ctx.send("❌ Không có token nào trong config!", delete_after=10)
            return
        
        mode = mode.lower() in ['on', 'true', '1', 'start']
        
        success_count = 0
        fail_count = 0
        
        if mode:
            for index, channel_token_pair in enumerate(token_owo):
                channel_id, token = list(channel_token_pair.items())[0]
                channel = self.bot.get_channel(int(channel_id))
                
                if not channel:
                    logger.warning(f"⚠️ Không tìm thấy channel {channel_id}")
                    fail_count += 1
                    continue
                
                if str(channel_id) in self.state["owo_mode"] and self.state["owo_mode"][str(channel_id)]:
                    logger.info(f"⏭️ Channel {channel_id} đã đang chạy")
                    continue
                
                try:
                    self.state["banned"][str(channel_id)] = False
                    self.state["stopped_by_command"][str(channel_id)] = False
                    self.state["owo_mode"][str(channel_id)] = True
                    
                    farm = OwOFarm(
                        channel_id=channel_id,
                        token=token,
                        config=config,
                        state=self.state,
                        messenger=self.messenger,
                        status_manager=self.status_manager,
                        webhook_sender=send_webhook,
                        captcha_solver=self.captcha_solver
                    )
                    
                    task = asyncio.create_task(farm.farm_loop())
                    self.state.setdefault("owo_tasks", {})[str(channel_id)] = [task]
                    
                    success_count += 1
                    logger.info(f"🟢 Started farm for {channel.name}")
                    
                    await asyncio.sleep(2)
                
                except Exception as e:
                    logger.error(f"❌ Lỗi start farm {channel_id}: {e}")
                    fail_count += 1
            
            await ctx.send(
                f"✅ **Đã bật farm cho {success_count}/{len(token_owo)} channel(s)**\n"
                f"❌ Thất bại: {fail_count}",
                delete_after=15
            )
        
        else:
            for index, channel_token_pair in enumerate(token_owo):
                channel_id, token = list(channel_token_pair.items())[0]
                
                if str(channel_id) not in self.state["owo_mode"] or not self.state["owo_mode"][str(channel_id)]:
                    continue
                
                try:
                    # Stop tasks
                    self.state["owo_mode"][str(channel_id)] = False
                    self.state["stopped_by_command"][str(channel_id)] = True
                    
                    tasks = self.state.get("owo_tasks", {}).get(str(channel_id), [])
                    for task in tasks:
                        try:
                            task.cancel()
                        except:
                            pass
                    
                    self.state["owo_tasks"][str(channel_id)] = []
                    success_count += 1
                    logger.info(f"🔴 Stopped farm for {channel_id}")
                
                except Exception as e:
                    logger.error(f"❌ Lỗi stop farm {channel_id}: {e}")
                    fail_count += 1
            
            await ctx.send(
                f"✅ **Đã tắt farm cho {success_count} channel(s)**\n"
                f"❌ Thất bại: {fail_count}",
                delete_after=15
            )
    
    # ==================== SEND ALL ====================
    
    @commands.command(name='owoallsend')
    async def owo_all_send(self, ctx, *, text: str):
        """Usage: {prefix}owoallsend <text>"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        config = self.bot.config
        token_owo = config.get("token_owo", [])
        
        if not token_owo:
            await ctx.send("❌ Không có token nào trong config!", delete_after=10)
            return
        
        success_count = 0
        fail_count = 0
        
        for index, channel_token_pair in enumerate(token_owo):
            channel_id, token = list(channel_token_pair.items())[0]
            channel = self.bot.get_channel(int(channel_id))
            
            try:
                await self.messenger.send_message(channel_id, text, token)
                success_count += 1
                
                channel_name = channel.name if channel else channel_id
                logger.info(f"📤 Sent to {channel_name}: {text[:50]}")
                
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"❌ Lỗi gửi message đến {channel_id}: {e}")
                fail_count += 1
        
        await ctx.send(
            f"✅ **Đã gửi message đến {success_count}/{len(token_owo)} channel(s)**\n"
            f"❌ Thất bại: {fail_count}\n"
            f"📝 Message: `{text[:50]}...`" if len(text) > 50 else f"📝 Message: `{text}`",
            delete_after=15
        )
    
    # ==================== STATUS ====================
    
    @commands.command(name='status_owo')
    async def status_owo(self, ctx, option: str = None):
        """Usage: {prefix}status_owo [farm|bet]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if option and option.lower() not in ["farm", "bet"]:
            await ctx.send("❌ Option không hợp lệ! Dùng: farm, bet, hoặc không gì", delete_after=10)
            return
        
        option = option.lower() if option else None
        
        lines = []
        now = datetime.now()
        lines.append("**🎮 TRẠNG THÁI OWO BOT**")
        lines.append(f"⏰ {now.strftime('%H:%M:%S %d/%m/%Y')}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if option is None or option == "farm":
            farm_channels = [ch for ch, active in self.state.get("owo_mode", {}).items() if active]
            
            lines.append("")
            lines.append("**🌾 OWO FARM**")
            
            if farm_channels:
                lines.append(f"📊 Active: **{len(farm_channels)}** channel(s)")
                lines.append("```")
                
                for channel_id in farm_channels:
                    channel = self.bot.get_channel(int(channel_id))
                    username = channel.name if channel else f"{channel_id}"
                    
                    commands = self.state.get("commands_sent", {}).get(channel_id, 0)
                    gems = self.state.get("gems_used", {}).get(channel_id, 0)
                    banned = self.state.get("banned", {}).get(channel_id, False)
                    
                    status_icon = "🚫" if banned else "✅"
                    
                    lines.append(f"{status_icon} {username}: 📝 {commands:,} | 💎 {gems}")
                
                lines.append("```")
            else:
                lines.append("```")
                lines.append("❌ Không có channel nào đang farm")
                lines.append("```")
        
        if option is None:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if option is None or option == "bet":
            bet_channels = [ch for ch, active in self.state.get("owobet_mode", {}).items() if active]
            
            lines.append("")
            lines.append("**🎰 OWO BET**")
            
            if bet_channels:
                lines.append(f"📊 Active: **{len(bet_channels)}** channel(s)")
                lines.append("```")
                
                for channel_id in bet_channels:
                    channel = self.bot.get_channel(int(channel_id))
                    username = channel.name if channel else f"{channel_id}"
                    
                    bets = self.state.get("bets_placed", {}).get(channel_id, 0)
                    profit = self.state.get("bet_profit", {}).get(channel_id, 0)
                    banned = self.state.get("banned", {}).get(channel_id, False)
                    
                    status_icon = "🚫" if banned else "✅"
                    profit_icon = "📈" if profit >= 0 else "📉"
                    profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
                    
                    lines.append(f"{status_icon} {username}: 🎲 {bets} | {profit_icon} {profit_str}")
                
                lines.append("```")
            else:
                lines.append("```")
                lines.append("❌ Không có channel nào đang bet")
                lines.append("```")
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("**⚙️ LỆNH**")
        lines.append("```")
        lines.append(".owo <index> on/off        - Farm 1 channel")
        lines.append(".owobet <index> on/off     - Bet 1 channel")
        lines.append(".owoall on/off             - Farm tất cả")
        lines.append(".owoallsend <text>         - Gửi tin nhắn tất cả")
        lines.append(".status_owo [farm|bet]     - Xem status")
        lines.append("```")
        
        await ctx.send("\n".join(lines), delete_after=60)

def setup(bot):
    """Setup function for cog"""
    bot.add_cog(owo(bot))
