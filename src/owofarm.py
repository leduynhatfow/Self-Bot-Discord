"""
OwO Farm Module
Xử lý logic farm OwO bot với schedule động + Captcha + Gems + Quest + HuntBot
"""

import asyncio
import random
import time
import os
import json
import logging
import re
import aiohttp
from datetime import datetime, timedelta
import unicodedata

logger = logging.getLogger(__name__)
class OwOFarm:
    def __init__(self, channel_id, token, config, state, messenger, status_manager, webhook_sender, captcha_solver=None):
        self.channel_id = str(channel_id)
        self.token = token
        self.config = config
        self.state = state
        self.messenger = messenger
        self.status_manager = status_manager
        self.webhook_sender = webhook_sender
        self.captcha_solver = captcha_solver 
        
        # Initialize state
        self._init_channel_state()
    def normalize_text(self, text):
        text = ''.join(
            ch for ch in unicodedata.normalize('NFKC', text)
            if not unicodedata.category(ch).startswith('C')
            and not unicodedata.category(ch).startswith('M')
        )
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    def _init_channel_state(self):
        """Khởi tạo state cho channel"""
        defaults = {
            "commands_sent": 0,
            "gems_used": 0,
            "last_gem_check": time.time(),
            "last_quest_check": time.time(),
            "huntbot_tries": 0,
            "huntbot_pause_until": 0,
            "huntbot_next_time": 0,
            "huntbot_stage": "normal",
            "huntbot_cowoncy": self.config.get("money", 20000)
        }
        
        for key, default_value in defaults.items():
            self.state.setdefault(key, {})
            if self.channel_id not in self.state[key]:
                self.state[key][self.channel_id] = default_value
    
    # =============== GEMS MANAGER ===============
    async def parse_gems(self, inventory_message):
        """Phân tích gems từ inventory"""
        rarity_order = ['f', 'm', 'e', 'r', 'l', 'u', 'c']
        gems_by_tier = {'1': [], '2': [], '3': [], '4': [], '5': [], 'star': []}
        box_count = 0
        
        lines = inventory_message.split('\n')
        for line in lines:
            for tier in ['1', '2', '3', '4', '5']:
                for rarity in rarity_order:
                    patterns = [
                        fr'`(\d+)`<:({rarity}gem{tier}):\d+>',
                        fr'`(\d+)`<a:({rarity}gem{tier}):\d+>'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            gems_by_tier[tier].append((rarity, match.group(1)))
            
            for rarity in rarity_order:
                patterns = [
                    fr'`(\d+)`<:({rarity}star):\d+>',
                    fr'`(\d+)`<a:({rarity}star):\d+>'
                ]
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        gems_by_tier['star'].append((rarity, match.group(1)))
            
            box_pattern = r'`(\d+)`<:box:427352600476647425>.*(\d{3})'
            box_match = re.search(box_pattern, line)
            if box_match:
                box_count = int(box_match.group(2))
        
        for tier in gems_by_tier:
            gems_by_tier[tier].sort(key=lambda x: rarity_order.index(x[0]))
        
        selected_gems = []
        for tier in ['1', '2', '3', '4', '5', 'star']:
            if gems_by_tier[tier]:
                selected_gems.append(gems_by_tier[tier][-1][1])
        
        return selected_gems, box_count
    
    async def check_and_use_gems(self):
        """Kiểm tra và sử dụng gems"""
        await self.messenger.send_message(self.channel_id, "owo inventory", self.token)
        await asyncio.sleep(3)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=2",
                    headers={"Authorization": self.token}
                ) as response:
                    if response.status == 200:
                        messages = await response.json()
                        for message in messages:
                            if message["author"]["id"] == "408785106942164992" and "inventory" in message["content"].lower():
                                selected_gems, box_count = await self.parse_gems(message["content"])
                                
                                if selected_gems:
                                    use_command = "owo use " + " ".join(selected_gems)
                                    await self.messenger.send_message(self.channel_id, use_command, self.token)
                                    self.state["gems_used"][self.channel_id] += len(selected_gems)
                                    logger.debug(f"💎 Đã dùng {len(selected_gems)} gems")
                                
                                if box_count > 5:
                                    await self.messenger.send_message(self.channel_id, "owolb all", self.token)
                                    logger.debug(f"📦 Mở {box_count} lootbox")
                                
                                await asyncio.sleep(3)
                                break
        except Exception as e:
            logger.error(f"Lỗi check gems: {e}")
    
    # =============== QUEST MANAGER ===============
    def parse_quests_from_embed(self, embed):
        """Phân tích quest từ embed"""
        try:
            description = embed.get("description", "")
            quests = []
            lines = description.split('\n')
            current_quest = ""
            quest_number = 0
            
            for line in lines:
                if line.startswith("**") and any(char.isdigit() for char in line[:5]):
                    if current_quest:
                        quests.append((quest_number, current_quest))
                    quest_number = int(line.split('.')[0].replace('*', '').strip())
                    current_quest = line
                elif current_quest:
                    current_quest += "\n" + line
            
            if current_quest:
                quests.append((quest_number, current_quest))
            
            return quests
        except Exception as e:
            logger.error(f"Lỗi phân tích quest: {e}")
            return []
    
    def find_friend_quest(self, quests):
        """Tìm quest friend"""
        keywords = ["friend", "friends"]
        for quest_num, quest_text in sorted(quests, key=lambda x: x[0]):
            if any(keyword in quest_text.lower() for keyword in keywords):
                return quest_num
        return None
    
    async def check_and_reroll_quests(self):
        """Kiểm tra và reroll quest"""
        await self.messenger.send_message(self.channel_id, "owo daily", self.token)
        await asyncio.sleep(15)
        await self.messenger.send_message(self.channel_id, "owoq", self.token)
        await asyncio.sleep(3)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=5",
                    headers={"Authorization": self.token}
                ) as response:
                    if response.status == 200:
                        messages = await response.json()
                        for message in messages:
                            if message["author"]["id"] != "408785106942164992":
                                continue
                            
                            if "embeds" in message and message["embeds"]:
                                embed = message["embeds"][0]
                                quests = self.parse_quests_from_embed(embed)
                                
                                if not quests:
                                    logger.warning(f"⚠️ Không tìm thấy quest")
                                    break
                                
                                friend_quest_num = self.find_friend_quest(quests)
                                
                                if friend_quest_num:
                                    logger.info(f"🔄 Reroll friend quest #{friend_quest_num}")
                                    await asyncio.sleep(1)
                                    await self.messenger.send_message(self.channel_id, f"owoq rr {friend_quest_num}", self.token)
                                    await asyncio.sleep(2)
                                
                                break
        except Exception as e:
            logger.error(f"Lỗi check quest: {e}")
    
    # =============== HUNTBOT MANAGER ===============
    def parse_huntbot_time(self, time_str):
        """Phân tích thời gian HuntBot"""
        time_str = time_str.upper().strip()
        h = int(re.search(r'(\d+)H', time_str).group(1)) if 'H' in time_str else 0
        m = int(re.search(r'(\d+)M', time_str).group(1)) if 'M' in time_str else 0
        return timedelta(hours=h, minutes=m)
    
    def parse_huntbot_cowoncy(self, msg_content):
        """Phân tích cowoncy tối ưu"""
        try:
            content = msg_content.lower().replace(",", "")
            match = re.search(r"current max autohunt:.*?for (\d+) cowoncy", content)
            return int(match.group(1)) if match else 20000
        except:
            return 20000
    
    async def handle_huntbot_messages(self, cowoncy_amount=None):
        """Xử lý tin nhắn HuntBot"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=5",
                    headers={"Authorization": self.token}
                ) as response:
                    if response.status == 200:
                        messages = await response.json()
                        for message in messages:
                            if message["author"]["id"] != "408785106942164992":
                                continue
                            
                            msg_content = message.get("content", "")
                            if "embeds" in message and message["embeds"]:
                                embed = message["embeds"][0]
                                msg_content = (
                                    (embed.get("description", "") or "") +
                                    "".join(f"{f.get('name', '')}\n{f.get('value', '')}" for f in embed.get("fields", []))
                                )
                            
                            msg_lower = msg_content.lower()
                            
                            if "please include your password! the command is" in msg_lower:
                                logger.warning(f"⚠️ Yêu cầu password, chờ 10 phút")
                                self.state["huntbot_next_time"][self.channel_id] = time.time() + 700
                                self.state["huntbot_stage"][self.channel_id] = "waiting_for_password_reset"
                                return True
                            
                            if "i am back with" in msg_lower and "animals" in msg_lower:
                                await asyncio.sleep(15)
                                await self.messenger.send_message(self.channel_id, "owohb", self.token)
                                await asyncio.sleep(4)
                                return await self.handle_huntbot_messages(cowoncy_amount)
                            
                            if "beep. boop. i am huntbot" in msg_lower:
                                optimal_cowoncy = self.parse_huntbot_cowoncy(msg_content)
                                self.state["huntbot_cowoncy"][self.channel_id] = optimal_cowoncy
                                await self.messenger.send_message(self.channel_id, f"owo hb {optimal_cowoncy}", self.token)
                                await asyncio.sleep(4)
                                return await self.handle_huntbot_messages(optimal_cowoncy)
                            
                            if "i will be back in" in msg_lower:
                                match = re.search(r"i will be back in\s*(\d+h?\s*\d*m?|\d+m?)", msg_lower, re.IGNORECASE)
                                if match:
                                    time_str = match.group(1).strip()
                                    delta = self.parse_huntbot_time(time_str)
                                    self.state["huntbot_next_time"][self.channel_id] = time.time() + delta.total_seconds()
                                    self.state["huntbot_stage"][self.channel_id] = "waiting_for_return"
                                    logger.info(f"⏰ HuntBot sẽ quay về sau {time_str}")
                                    return True
                            
                            if "here is your password!" in msg_lower and message.get("attachments"):
                                url = message["attachments"][0]["url"]
                                
                                if not self.captcha_solver:
                                    logger.error("❌ Captcha solver không khả dụng")
                                    return True
                                
                                logger.info(f"🔐 Đang giải captcha HuntBot...")
                                
                                # Try async solver first
                                result = None
                                try:
                                    if hasattr(self.captcha_solver, 'GhoStySolveNormalCap'):
                                        result = await self.captcha_solver.GhoStySolveNormalCap(url)
                                except Exception as e:
                                    logger.debug(f"Async solver failed: {e}")
                                
                                # Try sync solver as fallback
                                if not result:
                                    try:
                                        if hasattr(self.captcha_solver, 'GhoStySyncedCaptchaSolve'):
                                            result = self.captcha_solver.GhoStySyncedCaptchaSolve(url)
                                    except Exception as e:
                                        logger.debug(f"Sync solver failed: {e}")
                                
                                if result:
                                    use_cowoncy = cowoncy_amount if cowoncy_amount else self.state["huntbot_cowoncy"].get(self.channel_id, 20000)
                                    await self.messenger.send_message(self.channel_id, f"owo autohunt {use_cowoncy} {result}", self.token)
                                    logger.info(f"✅ Đã giải captcha HuntBot: {result}")
                                    await asyncio.sleep(4)
                                    return await self.handle_huntbot_messages(use_cowoncy)
                                else:
                                    logger.error(f"❌ Giải captcha HuntBot thất bại")
                                    return True
                            
                            if "you spent" in msg_lower and "cowoncy" in msg_lower:
                                match = re.search(r"i will be back in\s*(\d+h?\s*\d*m?|\d+m?)", msg_lower, re.IGNORECASE)
                                if match:
                                    time_str = match.group(1).strip()
                                    delta = self.parse_huntbot_time(time_str)
                                    self.state["huntbot_next_time"][self.channel_id] = time.time() + delta.total_seconds()
                                    self.state["huntbot_stage"][self.channel_id] = "waiting_for_return"
                                    logger.info(f"🤖 HuntBot đã kích hoạt, quay về sau {time_str}")
                                    return True
                        
                        return False
        except Exception as e:
            logger.error(f"Lỗi xử lý HuntBot: {e}")
            return False
    
    def create_daily_schedule(self):
        """
        Tạo lịch trình farm 2 batch:
        - Batch 1 (FARM): 7-8 giờ liên tục, delay min 30s → 500-800 lệnh
        - Batch 2 (REST): Nghỉ 17-18 giờ
        """
        history_file = "data/farm_history.json"
        history = {}
        
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except:
                history = {}
        
        if self.channel_id not in history:
            history[self.channel_id] = {
                "last_batch_counts": [],
                "total_days": 0
            }
        
        channel_history = history[self.channel_id]
        
        farm_hours = random.uniform(7.0, 8.0)
        farm_seconds = farm_hours * 3600
        
        avg_delay = random.uniform(35.0, 50.0)
        estimated_commands = int(farm_seconds / avg_delay)
        
        variation = random.uniform(0.90, 1.10)
        total_commands = int(estimated_commands * variation)
        
        total_commands = max(500, min(800, total_commands))
        
        extra_rest = random.uniform(1*3600, 2*3600)
        rest_seconds = (24*3600 - farm_seconds) + extra_rest
        
        schedule = {
            "pattern": "safe_continuous",
            "total_commands": total_commands,
            "num_batches": 1,
            "farm_times": [farm_seconds],
            "farm_commands": [total_commands],
            "rest_times": [rest_seconds],
            "total_farm_hours": farm_seconds / 3600,
            "total_rest_hours": rest_seconds / 3600,
            "avg_delay_target": avg_delay
        }
        
        channel_history["last_batch_counts"].append(1)
        if len(channel_history["last_batch_counts"]) > 5:
            channel_history["last_batch_counts"] = channel_history["last_batch_counts"][-5:]
        
        channel_history["total_days"] += 1
        history[self.channel_id] = channel_history
        
        try:
            with open(history_file, "w") as f:
                json.dump(history, f, indent=4)
        except:
            pass
        
        return schedule
    
    def calculate_delay(self, time_left, commands_left):
        """
        Tính delay động với min 30s, max 90s
        """
        if commands_left <= 0 or time_left <= 0:
            return 30.0
        
        target_delay = time_left / commands_left
        
        min_delay = 30.0
        max_delay = 90.0
        
        if target_delay < min_delay:
            actual_delay = random.uniform(min_delay, min_delay * 1.2)
        elif target_delay > max_delay:
            actual_delay = random.uniform(max_delay * 0.8, max_delay)
        else:
            actual_delay = random.uniform(
                max(min_delay, target_delay * 0.85),
                min(max_delay, target_delay * 1.15)
            )
        
        if random.random() < 0.015:
            long_delay = random.uniform(180, 480)
            actual_delay += long_delay
            logger.info(f"   💤 Long delay: +{long_delay/60:.1f} phút")
        
        elif random.random() < 0.03:
            micro_pause = random.uniform(30, 90)
            actual_delay += micro_pause
            logger.debug(f"   ⏸️ Micro-pause: +{micro_pause:.0f}s")
        
        return round(actual_delay, 2)
    
    async def check_ban(self):
        """Kiểm tra ban/captcha - CHỈ PHÁT HIỆN, KHÔNG GIẢI"""
        check_phrases = [
            "are you a real human",
            "please complete this within 10 minutes",
            "it may result in a ban",
            "please use the link below",
            "verify that you are human"
        ]
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=5",
                    headers={"Authorization": self.token}
                ) as response:
                    if response.status == 200:
                        messages = await response.json()
                        for message in messages:
                            if message["author"]["id"] == "408785106942164992":
                                msg_content = message.get("content", "")
                                
                                if "embeds" in message and message["embeds"]:
                                    embed = message["embeds"][0]
                                    msg_content = (
                                        (embed.get("description", "") or "") +
                                        (embed.get("title", "") or "") +
                                        "".join(f"{f.get('name', '')}\n{f.get('value', '')}" for f in embed.get("fields", []))
                                    )
                                
                                msg_norm = self.normalize_text(msg_content)
                                
                                if any(phrase in msg_norm for phrase in check_phrases):
                                    logger.warning(f"⚠️ Phát hiện ban/captcha: {msg_norm[:100]}...")
                                    return True
                        return False
        except Exception as e:
            logger.error(f"Lỗi check ban: {e}")
            return False
    
    async def handle_ban_detection(self, session):
        """Xử lý khi phát hiện ban"""
        logger.critical(f"🚨 BAN DETECTED cho {self.channel_id}!")
        
        try:
            embed = {
                "title": "🚨 BAN DETECTED - OWO FARM",
                "description": f"**Channel:** <#{self.channel_id}>\n⚠️ Đã phát hiện ban/captcha! Bot đã dừng hoàn toàn.",
                "fields": [
                    {"name": "💎 Gems đã dùng", "value": f"`{self.state['gems_used'].get(self.channel_id, 0)}`", "inline": True},
                    {"name": "📝 Lệnh đã gửi", "value": f"`{self.state['commands_sent'].get(self.channel_id, 0)}`", "inline": True}
                ],
                "color": 0xff0000,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "OwO Farm Bot - DỪNG"}
            }
            await self.webhook_sender("ban_alert", embed)
        except Exception as e:
            logger.error(f"Lỗi gửi webhook ban: {e}")
        
        self.state["owo_mode"][self.channel_id] = False
        self.state.setdefault("banned", {})[self.channel_id] = True
        self.state["stopped_by_command"][self.channel_id] = True
        
        # ========== CANCEL TASKS ==========
        tasks = self.state.get("owo_tasks", {}).get(self.channel_id, [])
        for task in tasks:
            try:
                task.cancel()
            except:
                pass
        self.state["owo_tasks"][self.channel_id] = []
        logger.debug(f"Cancelled {len(tasks)} tasks")
        
        # Update status
        self.status_manager.update_status(
            "owo_farm",
            self.channel_id,
            False,
            gems_used=self.state["gems_used"].get(self.channel_id, 0),
            commands_sent=self.state["commands_sent"].get(self.channel_id, 0),
            banned=True
        )
        
        # ========== GỬI DISCORD MESSAGE ==========
        try:
            await self.messenger.send_message(
                self.channel_id,
                "🚨 **BAN DETECTED!**\n\n"
                "Bot đã dừng hoàn toàn. Vui lòng:\n"
                "1. Giải quyết captcha/ban\n"
                "2. Sử dụng lệnh `.owo <index> on` để kích hoạt lại bot",
                self.token
            )
        except:
            pass
        
        return True
    
    async def send_farm_command(self, commands, last_command):
        """Gửi lệnh farm ngẫu nhiên"""
        cmd = random.choice(commands)
        while cmd == last_command and len(commands) > 1:
            cmd = random.choice(commands)
        
        await self.messenger.send_message(self.channel_id, cmd, self.token)
        
        return cmd
    
    async def farm_loop(self):
        """Main farm loop"""
        try:
            logger.info(f"🟢 Starting farm loop for {self.channel_id}")
            
            if self.channel_id not in self.state.get("farming_session", {}):
                self.state.setdefault("farming_session", {})[self.channel_id] = {}
            
            session = self.state["farming_session"][self.channel_id]
            
            if "daily_schedule" not in session or session["daily_schedule"] is None:
                schedule = self.create_daily_schedule()
                session["daily_schedule"] = schedule
                session["session_start_time"] = time.time()
                session["current_step"] = 0
                session["step_start_time"] = time.time()
                session["current_farm_commands_sent"] = 0
                session["daily_commands_sent"] = 0
                
                # Lưu schedule vào status
                self.status_manager.update_status(
                    "owo_farm",
                    self.channel_id,
                    True,
                    commands_sent=self.state["commands_sent"][self.channel_id],
                    gems_used=self.state["gems_used"][self.channel_id]
                )
                
                embed = {
                    "title": "📋 LỊCH TRÌNH NGÀY MỚI",
                    "description": f"**Channel:** <#{self.channel_id}>\n**Pattern:** `{schedule['pattern'].upper()}`\n**Tổng lệnh:** `{schedule['total_commands']} lệnh`",
                    "color": 0x00ff00,
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {"text": "OwO Farm Bot"}
                }
                await self.webhook_sender("farm_status", embed)
                
                logger.info(f"📋 Lịch trình ngày mới: {schedule['total_commands']} lệnh trong {schedule['total_farm_hours']:.1f}h")
            
            # ========== KHỞI TẠO HUNTBOT ĐẦU TIÊN ==========
            huntbot_mode = self.config.get("huntbot_mode", True)
            money = self.config.get("money", 20000)
            
            if huntbot_mode and self.state["huntbot_next_time"][self.channel_id] == 0:
                logger.info(f"🤖 Khởi động HuntBot lần đầu với {money} cowoncy...")
                await self.messenger.send_message(self.channel_id, f"owo hb {money}", self.token)
                self.state["huntbot_tries"][self.channel_id] = 1
                await asyncio.sleep(4)
                
                await self.handle_huntbot_messages(money)
            
            # Commands list
            base_commands = ["owoh", "owo pray", "owo h", "owo b", "owob"]
            random_commands = [
                random.choice(["owo cf 1", "owoz", "owo s 1", "owo owo"]),
                random.choice(["owo pup", "owo army", "owo piku", "owo run"]),
                random.choice(["owo punch <@408785106942164992>", "owo roll"])
            ]
            commands = base_commands + random_commands
            last_command = None
            
            # Main loop
            while self.state["owo_mode"].get(self.channel_id, False):
                try:
                    current_time = time.time()
                    
                    # Ban/Captcha check
                    ban_detected = await self.check_ban()
                    
                    if ban_detected:
                        if await self.handle_ban_detection(session):
                            break
                    
                    schedule = session.get("daily_schedule")
                    if not schedule:
                        logger.error("Schedule missing!")
                        break
                    
                    current_step = session.get("current_step", 0)
                    num_batches = schedule["num_batches"]
                    
                    if current_step >= num_batches * 2:
                        embed = {
                            "title": "🎉 HOÀN THÀNH 1 NGÀY FARM",
                            "description": f"**Channel:** <#{self.channel_id}>",
                            "fields": [
                                {"name": "✅ Tổng lệnh", "value": f"`{session['daily_commands_sent']}`", "inline": True},
                                {"name": "💎 Gems", "value": f"`{self.state['gems_used'][self.channel_id]}`", "inline": True}
                            ],
                            "color": 0xffff00,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await self.webhook_sender("daily_complete", embed)
                        
                        new_schedule = self.create_daily_schedule()
                        session["daily_schedule"] = new_schedule
                        session["current_step"] = 0
                        session["step_start_time"] = time.time()
                        session["current_farm_commands_sent"] = 0
                        session["daily_commands_sent"] = 0
                        
                        continue
                    
                    # FARM PHASE
                    if current_step % 2 == 0:
                        farm_index = current_step // 2
                        farm_time = schedule["farm_times"][farm_index]
                        farm_commands = schedule["farm_commands"][farm_index]
                        step_start_time = session.get("step_start_time", current_time)
                        
                        time_elapsed = current_time - step_start_time
                        time_left = farm_time - time_elapsed
                        commands_sent = session.get("current_farm_commands_sent", 0)
                        commands_left = farm_commands - commands_sent
                        
                        if time_elapsed >= farm_time or commands_sent >= farm_commands:
                            session["current_step"] += 1
                            session["step_start_time"] = time.time()
                            session["current_farm_commands_sent"] = 0
                            
                            rest_time = schedule["rest_times"][farm_index]
                            embed = {
                                "title": f"💤 BẮT ĐẦU NGHỈ BATCH {farm_index + 1}",
                                "description": f"**Channel:** <#{self.channel_id}>",
                                "fields": [
                                    {"name": "✅ Đã gửi", "value": f"`{commands_sent} lệnh`", "inline": True},
                                    {"name": "⏰ Nghỉ", "value": f"`{rest_time/3600:.1f}h`", "inline": True}
                                ],
                                "color": 0xffa500,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await self.webhook_sender("farm_status", embed)
                            
                            continue
                        
                        if commands_left > 0 and time_left > 0:
                            # ========== GEM CHECK ==========
                            if current_time - self.state["last_gem_check"][self.channel_id] > 4000:
                                await self.check_and_use_gems()
                                self.state["last_gem_check"][self.channel_id] = current_time
                                continue

                            # ========== QUEST CHECK ==========
                            if current_time - self.state["last_quest_check"][self.channel_id] > 86450:
                                await self.check_and_reroll_quests()
                                self.state["last_quest_check"][self.channel_id] = current_time
                                continue

                            # ========== HUNTBOT PAUSE ==========
                            if current_time < self.state["huntbot_pause_until"].get(self.channel_id, 0):
                                await asyncio.sleep(10)
                                continue

                            # ========== HUNTBOT TRIGGER ==========
                            if huntbot_mode and current_time >= self.state["huntbot_next_time"].get(self.channel_id, 0) + 15:
                                cmd = "owohb" if self.state["huntbot_stage"][self.channel_id] == "waiting_for_return" else f"owo hb {money}"
                                
                                logger.debug(f"🤖 HuntBot try {self.state['huntbot_tries'][self.channel_id] + 1}: {cmd}")
                                await self.messenger.send_message(self.channel_id, cmd, self.token)
                                self.state["huntbot_tries"][self.channel_id] += 1
                                await asyncio.sleep(4)
                                
                                handled = await self.handle_huntbot_messages(money)
                                if handled:
                                    self.state["huntbot_tries"][self.channel_id] = 0
                                elif self.state["huntbot_tries"][self.channel_id] >= 4:
                                    self.state["huntbot_pause_until"][self.channel_id] = current_time + 14*60
                                    self.state["huntbot_tries"][self.channel_id] = 0
                                    logger.warning(f"⏸️ HuntBot pause 14 phút")
                                continue
                            
                            # ========== GỬI LỆNH FARM ==========
                            delay = self.calculate_delay(time_left, commands_left)
                            
                            last_command = await self.send_farm_command(commands, last_command)
                            
                            self.state["commands_sent"][self.channel_id] += 1
                            session["current_farm_commands_sent"] += 1
                            session["daily_commands_sent"] += 1
                            
                            logger.info(f"🌱 Batch {farm_index+1}: {commands_sent+1}/{farm_commands} | "
                                      f"Ngày: {session['daily_commands_sent']}/{schedule['total_commands']} | "
                                      f"Delay: {delay:.1f}s")
                            
                            self.status_manager.update_status(
                                "owo_farm",
                                self.channel_id,
                                True,
                                gems_used=self.state["gems_used"][self.channel_id],
                                commands_sent=self.state["commands_sent"][self.channel_id]
                            )
                            
                            await asyncio.sleep(delay)
                        else:
                            await asyncio.sleep(10)
                    
                    else:
                        rest_index = (current_step - 1) // 2
                        rest_time = schedule["rest_times"][rest_index]
                        step_start_time = session.get("step_start_time", current_time)
                        
                        time_elapsed = current_time - step_start_time
                        time_left = rest_time - time_elapsed
                        
                        if time_elapsed >= rest_time:
                            session["current_step"] += 1
                            session["step_start_time"] = time.time()
                            
                            next_farm_index = (current_step + 1) // 2
                            if next_farm_index < len(schedule["farm_times"]):
                                embed = {
                                    "title": f"🌱 BẮT ĐẦU FARM BATCH {next_farm_index + 1}",
                                    "description": f"**Channel:** <#{self.channel_id}>",
                                    "color": 0x00ff00,
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                await self.webhook_sender("farm_status", embed)
                            
                            continue
                        
                        if not session.get(f"rest_{rest_index}_logged", False):
                            logger.info(f"💤 Đang nghỉ batch {rest_index+1}: còn {time_left/3600:.2f}h")
                            session[f"rest_{rest_index}_logged"] = True
                        
                        if time_left > 300:
                            await asyncio.sleep(300)
                        else:
                            await asyncio.sleep(60)
                
                except asyncio.CancelledError:
                    logger.info(f"Farm loop cancelled for {self.channel_id}")
                    break
                except Exception as e:
                    logger.error(f"Lỗi inner loop: {e}", exc_info=True)
                    await asyncio.sleep(10)
        
        except Exception as e:
            logger.error(f"Lỗi farm loop: {e}", exc_info=True)
        
        finally:
            self.status_manager.update_status(
                "owo_farm",
                self.channel_id,
                False,
                gems_used=self.state["gems_used"].get(self.channel_id, 0),
                commands_sent=self.state["commands_sent"].get(self.channel_id, 0),
                banned=self.state.get("banned", {}).get(self.channel_id, False)
            )
            
            logger.info(f"🔴 Dừng farm loop cho {self.channel_id}")
