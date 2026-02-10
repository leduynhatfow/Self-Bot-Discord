"""
OwO Bet Module
Xử lý logic bet OwO bot với martingale strategy + Captcha Solver
Hoàn toàn độc lập, không phụ thuộc respond.py
"""

import asyncio
import random
import time
import logging
import json
import os
import aiohttp, unicodedata, re
from datetime import datetime

logger = logging.getLogger(__name__)

class OwOBet:
    def __init__(self, channel_id, token, config, state, messenger, status_manager, webhook_sender, captcha_solver=None):
        self.channel_id = str(channel_id)
        self.token = token
        self.config = config
        self.state = state
        self.messenger = messenger
        self.status_manager = status_manager
        self.webhook_sender = webhook_sender
        self.captcha_solver = captcha_solver
        
        self.bet_sequence = [1, 4, 20, 100, 500, 1500, 5015, 11946, 25020, 46507, 93555, 184200, 250000]
        self.current_index = 0
        
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
        self.state.setdefault("bets_placed", {})
        if self.channel_id not in self.state["bets_placed"]:
            self.state["bets_placed"][self.channel_id] = 0
        
        self.state.setdefault("bet_profit", {})
        if self.channel_id not in self.state["bet_profit"]:
            self.state["bet_profit"][self.channel_id] = 0
        
        self.state.setdefault("current_bet_amount", {})
        if self.channel_id not in self.state["current_bet_amount"]:
            self.state["current_bet_amount"][self.channel_id] = 0
    
    async def check_ban(self):
        """Kiểm tra ban/captcha - CHỈ PHÁT HIỆN, KHÔNG GIẢI"""
        check_phrases = [
            "captcha",
            "please complete this within 10 minutes",
            "please complete your captcha",
            "are you a real human?",
            "verification",
            "please DM me"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=10",
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
                                    logger.warning(f"⚠️ Phát hiện ban/captcha bet: {msg_norm[:100]}...")
                                    return True
                        return False
        except Exception as e:
            logger.error(f"Lỗi check ban: {e}")
            return False
    
    async def handle_ban_detection(self):
        """Xử lý khi phát hiện ban"""
        logger.critical(f"🚨 BAN DETECTED cho bet {self.channel_id}!")
        
        try:
            embed = {
                "title": "🚨 BAN DETECTED - OWO BET",
                "description": f"**Channel:** <#{self.channel_id}>\n⚠️ Đã phát hiện ban/captcha! Bot đã dừng hoàn toàn.\n\n**Hành động:** Sử dụng lệnh start để kích hoạt lại.",
                "fields": [
                    {"name": "🎰 Bets đã đặt", "value": f"`{self.state['bets_placed'].get(self.channel_id, 0)}`", "inline": True},
                    {"name": "📊 Profit/Loss", "value": f"`{self.state['bet_profit'].get(self.channel_id, 0):+,}`", "inline": True}
                ],
                "color": 0xff0000,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "OwO Bet Bot - DỪNG"}
            }
            await self.webhook_sender("ban_alert", embed)
        except Exception as e:
            logger.error(f"Lỗi gửi webhook ban: {e}")
        
        self.state["owobet_mode"][self.channel_id] = False
        self.state.setdefault("banned", {})[self.channel_id] = True
        self.state["stopped_by_command"][self.channel_id] = True
        
        # ========== CANCEL TASKS ==========
        tasks = self.state.get("owobet_tasks", {}).get(self.channel_id, [])
        for task in tasks:
            try:
                task.cancel()
            except:
                pass
        self.state["owobet_tasks"][self.channel_id] = []
        logger.debug(f"Cancelled {len(tasks)} tasks")
        
        # Update status
        self.status_manager.update_status(
            "owo_bet",
            self.channel_id,
            False,
            bets_placed=self.state["bets_placed"].get(self.channel_id, 0),
            profit=self.state["bet_profit"].get(self.channel_id, 0),
            banned=True
        )
        
        # ========== GỬI DISCORD MESSAGE ==========
        try:
            await self.messenger.send_message(
                self.channel_id,
                "🚨 **BAN DETECTED!**\n\n"
                "Bet bot đã dừng hoàn toàn. Vui lòng:\n"
                "1. Giải quyết captcha/ban\n"
                "2. Sử dụng lệnh `.owobet <index> on` để kích hoạt lại",
                self.token
            )
        except:
            pass
        
        return True
    
    async def fetch_latest_message(self):
        """Lấy message mới nhất từ OwO bot"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{self.channel_id}/messages?limit=1",
                    headers={"Authorization": self.token}
                ) as response:
                    if response.status == 200:
                        messages = await response.json()
                        if messages and messages[0]["author"]["id"] == "408785106942164992":
                            return messages[0]
        except Exception as e:
            logger.error(f"Lỗi fetch message: {e}")
        
        return None
    
    async def place_bet(self, amount):
        """Đặt bet với số tiền"""
        await self.messenger.send_message(self.channel_id, f"owo cf {amount}", self.token)
        self.state["bets_placed"][self.channel_id] += 1
        self.state["current_bet_amount"][self.channel_id] = amount
        
        logger.info(f"🎰 Đặt bet {amount} (total: {self.state['bets_placed'][self.channel_id]})")
        
        # Update status
        self.status_manager.update_status(
            "owo_bet",
            self.channel_id,
            True,
            bets_placed=self.state["bets_placed"][self.channel_id],
            profit=self.state["bet_profit"][self.channel_id],
            banned=False
        )
    
    def get_random_delay(self):
        """Tạo delay ngẫu nhiên giữa các bet"""
        base_delay = random.uniform(13.7, 23.4)
        extra = random.choice([0.3, 0.7, 1.1, 1.4, 0.9, 1.6])
        return base_delay + extra
    
    async def bet_loop(self):
        """Main bet loop với martingale strategy"""
        try:
            logger.info(f"🟢 Starting bet loop for {self.channel_id}")
            
            await self.place_bet(self.bet_sequence[self.current_index])
            
            while self.state["owobet_mode"].get(self.channel_id, False):
                try:
                    ban_detected = await self.check_ban()
                    
                    if ban_detected:
                        if await self.handle_ban_detection():
                            break
                    
                    await asyncio.sleep(2)
                    message = await self.fetch_latest_message()
                    
                    if not message:
                        continue
                    
                    content = message.get("content", "").lower()
                    
                    if "you lost it all" in content:
                        bet_amount = self.state["current_bet_amount"][self.channel_id]
                        self.state["bet_profit"][self.channel_id] -= bet_amount
                        
                        logger.info(f"❌ THUA -{bet_amount} | Profit: {self.state['bet_profit'][self.channel_id]:+,}")
                        
                        self.current_index += 1
                        
                        if self.current_index >= len(self.bet_sequence):
                            self.current_index = 0
                            logger.warning(f"⚠️ Đã hết sequence, reset về {self.bet_sequence[0]}")
                        
                        next_bet = self.bet_sequence[self.current_index]
                        delay = self.get_random_delay()
                        
                        await asyncio.sleep(delay)
                        await self.place_bet(next_bet)
                    
                    elif "you won" in content:
                        bet_amount = self.state["current_bet_amount"][self.channel_id]
                        self.state["bet_profit"][self.channel_id] += bet_amount
                        
                        logger.info(f"✅ THẮNG +{bet_amount} | Profit: {self.state['bet_profit'][self.channel_id]:+,}")
                        
                        self.current_index = 0
                        next_bet = self.bet_sequence[self.current_index]
                        delay = self.get_random_delay()
                        
                        await asyncio.sleep(delay)
                        await self.place_bet(next_bet)
                    
                    else:
                        await asyncio.sleep(1)
                
                except asyncio.CancelledError:
                    logger.info(f"Bet loop cancelled for {self.channel_id}")
                    break
                except Exception as e:
                    logger.error(f"Lỗi inner bet loop: {e}", exc_info=True)
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Lỗi bet loop: {e}", exc_info=True)
        
        finally:
            self.status_manager.update_status(
                "owo_bet",
                self.channel_id,
                False,
                bets_placed=self.state["bets_placed"].get(self.channel_id, 0),
                profit=self.state["bet_profit"].get(self.channel_id, 0),
                banned=self.state.get("banned", {}).get(self.channel_id, False)
            )
            
            logger.info(f"🔴 Dừng bet loop cho {self.channel_id}")
