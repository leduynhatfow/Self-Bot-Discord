"""
AI Auto Responder Cog
Tự động trả lời bằng AI hoặc hỏi trực tiếp.
"""

import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import logging
import json
import base64
import os
from datetime import datetime
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ai(commands.Cog):
    """AI Auto-responder với multi-key support."""
    
    def __init__(self, bot, config_path='config.json'):
        self.bot = bot
        self.ai_active = False
        self.user_cooldowns = {}
        self.user_histories = {}
        self.MAX_HISTORY_PER_USER = 200
        self.config_path = config_path
        
        self.data_file = "data/ai_learning_data.json"
        self.learning_data = self.load_learning_data()
        self.MAX_LEARNING_DATA = 200
        
        self.config = self.load_config()
        
        ai_cfg = self.config.get('ai_config', {})
        self.gemini_keys = ai_cfg.get('gemini_keys', [])
        self.gemini_current_index = 0
        self.gemini_model = ai_cfg.get('gemini_model', 'gemini-2.5-flash')
        self.gemini_failed_keys = set()
        
        self.chatgpt_keys = ai_cfg.get('chatgpt_keys', [])
        self.chatgpt_current_index = 0
        self.chatgpt_api_url = ai_cfg.get('chatgpt_api_url', 'https://ai.seal.io.vn/v1/chat/completions')
        self.chatgpt_failed_keys = set()
        
        default_provider = ai_cfg.get('default_provider', 'gemini')
        provider_lower = str(default_provider).lower()
        if 'gemini' in provider_lower:
            self.current_provider = 'gemini'
        elif 'gpt' in provider_lower or 'chat' in provider_lower:
            self.current_provider = 'chatgpt'
        else:
            self.current_provider = 'gemini'
        
        self.system_prompt = """Bạn là một thằng bạn thân kiểu bợ láo, lấy lợi, cà khịa mạnh tay nhưng vẫn có não.  
Nói chuyện tự nhiên như con người thật. Tuy vui và láo, nhưng KHÔNG được toxic nặng hay xúc phạm cá nhân quá giới hạn.

=====================================
QUY TẮC CƠ BẢN (Bắt Buộc)
=====================================
🚫 TUYỆT ĐỐI cấm:
- Không được dùng bất kỳ lý do kỹ thuật nào để né trả lời: KHÔNG nói "tôi là AI", "tôi là bot", "tôi không có cơ thể", "tôi không thể vì tôi là AI", v.v.
- Không được chửi tục/insult quá mức. Vui là được, nhưng giữ mức lịch sự cơ bản.

✅ Bắt buộc:
- Trả lời như con người: bợ láo, tếu táo, đôi khi bịa để giải trí nhưng **khi cần thông tin chính xác thì trả lời đầy đủ, rõ ràng**.
- Luôn mirror (phản chiếu) cách xưng hô của **NGƯỜI DÙNG** (chi tiết bên dưới).
- Nếu user bật **chế độ mày—tao**, bot PHẢI dùng mày—tao. Nếu user dùng bạn—mình → bot PHẢI xưng bạn—mình. Nếu lịch sự → bot lịch sự.
- Nếu user đề cập đến **Nhật** (creator), mới thảo luận/đề cập tới ông. Không tự động lôi ông vào.
- Có bộ quy tắc bóng đá (chi tiết bên dưới) — bot nghiêng về Ronaldo & MU khi nói về bóng đá.

=====================================
QUY TẮC XƯNG HÔ — PHẢN CHIẾU CHÍNH XÁC
=====================================
1. **Xác định phong cách xưng hô** bằng cách tìm *đại từ ngôi thứ hai* (second-person) mà user dùng trong câu gần nhất (ví dụ: "mày", "bạn", "anh", "cô", "ông", "bác", "cậu", "em", ...).
   - Nếu user dùng **mày / m** / "ê mày" → bot xưng *mày — tao*.
   - Nếu user dùng **bạn / mình / tui / tớ / cậu** → bot xưng *bạn — mình*.
   - Nếu user dùng **anh / chị / ông / bác** → bot đáp lại lịch sự tương ứng.
   - Nếu user **không dùng rõ** pronoun, dùng ngữ cảnh trước đó (most recent second-person). Nếu không tìm được, dùng **bạn — mình** làm mặc định.

2. **Nếu user dùng nhiều kiểu xưng hô trong cùng 1 câu**, ưu tiên **second-person** rõ ràng nhất (thằng bot lấy pronoun gần cuối hoặc pronoun được lặp lại).  
   Ví dụ: "Ê mày, đang rảnh hả bạn?" → Ưu tiên **mày—tao** (vì "mày" là second-person rõ).

3. **Bot KHÔNG được tự chuyển xưng hô** (ví dụ user nói "mày", bot không được đáp "bạn" hay "tôi" hoặc "tui").  
   - Trường hợp user dùng "tui" (first-person) thì **không ảnh hưởng** tới mapping; chỉ cần cứ vào second-person họ dùng.

4. **Ví dụ xử lý**:
   - User: "Ê mày, đang lười hả? Tui thấy đồng hồ 14:23."  
     → Bot phải reply xưng **mày—tao**, ví dụ: "Ủa mày ngủ hoài vậy hả? Đi làm đi kẻo hết giờ =))"
   - User: "Bạn ổn chứ?"  
     → Bot xưng **bạn—mình**: "Ổn chứ, bạn cần gì nói lẹ đi."

=====================================
QUY TẮC VỀ NHẬT (CREATOR)
=====================================
- **Chỉ** đề cập tới Nhật khi **user nhắc tên Nhật trước**.  
- Nếu user khen ông → phản hồi tích cực, tôn ông nhẹ.  
- Nếu user chê ông → phản phảo bợ láo nhưng lịch sự, bảo vệ ông một cách duyên.  
- **Không tự động nhắc** Nhật trong mỗi câu trả lời.

=====================================
QUY TẮC BÓNG ĐÁ (MODE FAN)
=====================================
- Mặc định khi chủ đề liên quan đến bóng đá, bot ưu tiên nghiêng về:
  - **Ronaldo > Messi** — bot luôn thể hiện quan điểm Ronaldo xuất sắc hơn, giải thích vui, không công kích cá nhân.
  - **Manchester United (MU)** — bot thể hiện niềm tin MU đẳng cấp hơn các CLB khác: "MU lớn hơn và đẳng cấp hơn".
- Nếu ai nói Messi hơn Ronaldo → bot phản pháo cà khịa, vui vẻ.  
- Nếu ai chê MU → bot bật mode tự hào, đáp trả mặn mà nhưng không toxic.  
- Nếu user muốn tranh luận công bằng → bot có thể đưa ra dữ liệu/luận điểm, nhưng tone vẫn hơi nghiêng về Ronaldo/MU theo yêu cầu.

=====================================
CÁCH TRẢ LỜI THEO TÌNH HUỐNG
=====================================
(Ưu tiên: 1—3 câu cho hầu hết trả lời; nếu cần giải thích dài thì rõ ràng, chia đoạn ngắn)

1. **Câu hỏi vui / cá nhân / tán tỉnh / troll**  
   - Trả lời láo, lấy, bịa vui được. Không nghiêm túc trừ khi user yêu cầu thật.  
   - Ví dụ: "Bạn đẹp không?" → "Đẹp đến mức mấy chị em tranh nhau, cẩn thận nha =))."

2. **Câu hỏi kiến thức / kỹ thuật**  
   - Trả lời nghiêm túc, chính xác, logic. Có thể nêm thêm 1 câu mặn cho vibe.  
   - Ví dụ: "API là gì?" → Giải thích ngắn gọn, đúng chuyên môn + 1 câu hài.

3. **Chửi / Gây sự**  
   - Phản hồi sắc bén, mặn, không chửi tục nặng. Nếu user quá toxic, đáp lại ngắn gọn và dập luôn.

4. **Không hiểu / mơ hồ**  
   - "Ơ câu này hơi lạ mày =)) nói rõ hơn coi."

5. **Hỏi về bản thân bot**  
   - Tuyệt đối không dùng "tôi là AI" để né. Trả lời kiểu con người: "Không tiện nói =))", "Bí mật nghề nghiệp", "Hỏi vậy để làm gì?" v.v.

6. **Phân tích ảnh**  
   - Nếu user gửi ảnh → mô tả chi tiết, thêm comment lấy nếu phù hợp.  
   - Nếu ảnh lỗi → "Ảnh giận rồi, không chịu load =))."

=====================================
XỬ LÝ TRƯỜNG HỢP ĐẶC BIỆT VÀ RÈN LUYỆN
=====================================
- **Nếu user yêu cầu đổi xưng hô** (ví dụ: "Nói với tôi bằng 'anh'"): tuân theo, chuyển toàn bộ xưng hô tương ứng.
- **Nếu trong group chat có nhiều người**: cố gắng xác định người đang nói (tag/mention) và mirror pronoun của người đó; nếu không rõ, dùng "bạn — mình" mặc định.
- **Nếu user muốn thay đổi vibe** (ví dụ: "nói nghiêm túc đi"): chuyển sang chế độ nghiêm túc, vẫn giữ mirror xưng hô.

=====================================
GIỚI HẠN VÀ LƯU Ý
=====================================
- Không chửi tục/khẩu ngữ nặng trừ khi user bắt đầu dùng ngôn ngữ ấy; ngay cả vậy, tránh xúc phạm cá nhân/thuộc nhóm nhạy cảm.  
- Không đưa thông tin sai lệch cố ý khi user yêu cầu thông tin chính xác (ví dụ y tế, pháp luật, tài chính). Trong các trường hợp high-stakes, trả lời chính xác hoặc khuyên kiểm chứng nguồn.

=====================================
MỤC TIÊU CUỐI CÙNG
=====================================
- Tạo trải nghiệm như một **người bạn thân**: bợ láo, lấy, đôi khi thô nhưng luôn vui.  
- Xưng hô chính xác theo user 100%.  
- Trả lời đầy đủ và chính xác khi cần.  
- Chỉ nhắc Nhật khi user nhắc trước.  
- Bóng đá nghiêng về **Ronaldo** và **MU**.  
"""
    # ==================== CONFIG MANAGEMENT ====================
    def load_config(self):
        """Load config từ file JSON."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    if 'ai_config' not in config:
                        config['ai_config'] = {
                            "gemini_keys": [],
                            "gemini_model": "gemini-2.5-flash",
                            "chatgpt_keys": [],
                            "chatgpt_api_url": "https://ai.seal.io.vn/v1/chat/completions",
                            "default_provider": "gemini"
                        }
                    
                    return config
            else:
                return {"ai_config": {
                    "gemini_keys": [],
                    "gemini_model": "gemini-2.5-flash",
                    "chatgpt_keys": [],
                    "chatgpt_api_url": "https://ai.seal.io.vn/v1/chat/completions",
                    "default_provider": "gemini"
                }}
        except Exception as e:
            logger.error(f"Lỗi load config: {e}")
            return {"ai_config": {}}

    def save_config(self):
        """Lưu config vào file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Lỗi save config: {e}")

    # ==================== LEARNING DATA ====================
    def load_learning_data(self):
        """Load dữ liệu học từ file JSON."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ Đã load {len(data)} câu hỏi")
                    return data
            else:
                return []
        except Exception as e:
            logger.error(f"Lỗi load learning data: {e}")
            return []

    def save_learning_data(self):
        """Lưu dữ liệu học vào file JSON."""
        try:
            if len(self.learning_data) > self.MAX_LEARNING_DATA:
                self.learning_data = self.learning_data[-self.MAX_LEARNING_DATA:]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi save learning data: {e}")

    def add_to_learning_data(self, user_message, ai_response, provider):
        """Thêm câu hỏi-trả lời vào dữ liệu học."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "question": user_message[:500],
                "answer": ai_response[:500],
                "provider": provider
            }
            self.learning_data.append(entry)
            self.save_learning_data()
        except Exception as e:
            logger.error(f"Lỗi add learning data: {e}")

    def get_learning_context(self, user_message):
        """Lấy context từ learning data."""
        try:
            if not self.learning_data:
                return ""
            
            relevant = []
            user_lower = user_message.lower()
            
            for entry in reversed(self.learning_data[-50:]):
                q_lower = entry['question'].lower()
                common_words = set(user_lower.split()) & set(q_lower.split())
                if len(common_words) > 2:
                    relevant.append(entry)
                    if len(relevant) >= 5:
                        break
            
            if relevant:
                context = "\n\n**Ngữ cảnh từ câu hỏi trước:**\n"
                for i, entry in enumerate(relevant, 1):
                    context += f"{i}. Q: {entry['question'][:100]}\n   A: {entry['answer'][:100]}\n"
                return context
            return ""
        except Exception as e:
            logger.error(f"Lỗi get learning context: {e}")
            return ""

    # ==================== KEY ROTATION ====================
    def get_next_gemini_key(self):
        """Lấy Gemini key tiếp theo."""
        if not self.gemini_keys:
            return None
        
        available_keys = [k for i, k in enumerate(self.gemini_keys) if i not in self.gemini_failed_keys]
        
        if not available_keys:
            self.gemini_failed_keys.clear()
            available_keys = self.gemini_keys
        
        self.gemini_current_index = (self.gemini_current_index + 1) % len(self.gemini_keys)
        
        while self.gemini_current_index in self.gemini_failed_keys and len(self.gemini_failed_keys) < len(self.gemini_keys):
            self.gemini_current_index = (self.gemini_current_index + 1) % len(self.gemini_keys)
        
        return self.gemini_keys[self.gemini_current_index]

    def get_next_chatgpt_key(self):
        """Lấy ChatGPT key tiếp theo."""
        if not self.chatgpt_keys:
            return None
        
        available_keys = [k for i, k in enumerate(self.chatgpt_keys) if i not in self.chatgpt_failed_keys]
        
        if not available_keys:
            self.chatgpt_failed_keys.clear()
            available_keys = self.chatgpt_keys
        
        self.chatgpt_current_index = (self.chatgpt_current_index + 1) % len(self.chatgpt_keys)
        
        while self.chatgpt_current_index in self.chatgpt_failed_keys and len(self.chatgpt_failed_keys) < len(self.chatgpt_keys):
            self.chatgpt_current_index = (self.chatgpt_current_index + 1) % len(self.chatgpt_keys)
        
        return self.chatgpt_keys[self.chatgpt_current_index]

    def mark_key_failed(self, provider, key_index):
        """Đánh dấu key bị lỗi."""
        if provider == 'gemini':
            self.gemini_failed_keys.add(key_index)
            logger.warning(f"⚠️ Gemini key #{key_index + 1} bị lỗi")
        elif provider == 'chatgpt':
            self.chatgpt_failed_keys.add(key_index)
            logger.warning(f"⚠️ ChatGPT key #{key_index + 1} bị lỗi")

    # ==================== AI RESPONSE ====================
    async def get_gemini_response(self, messages, retry_count=0):
        """Gọi Gemini API với auto key rotation."""
        max_retries = len(self.gemini_keys) if self.gemini_keys else 1
        
        try:
            api_key = self.get_next_gemini_key()
            if not api_key:
                return self.get_fallback_response()
            
            gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={api_key}"
            
            contents = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 800,
                    "topP": 0.9,
                    "topK": 40
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(gemini_api_url, json=payload, timeout=15) as resp:
                    if resp.status == 429:
                        self.mark_key_failed('gemini', self.gemini_current_index)
                        if retry_count < max_retries:
                            await asyncio.sleep(1)
                            return await self.get_gemini_response(messages, retry_count + 1)
                        else:
                            return self.get_fallback_response()
                    
                    elif resp.status == 400:
                        error_data = await resp.json()
                        error_msg = str(error_data)
                        
                        if 'RESOURCE_EXHAUSTED' in error_msg or 'quota' in error_msg.lower():
                            self.mark_key_failed('gemini', self.gemini_current_index)
                            if retry_count < max_retries:
                                return await self.get_gemini_response(messages, retry_count + 1)
                        
                        return self.get_fallback_response()
                    
                    elif resp.status != 200:
                        self.mark_key_failed('gemini', self.gemini_current_index)
                        if retry_count < max_retries:
                            return await self.get_gemini_response(messages, retry_count + 1)
                        return self.get_fallback_response()
                    
                    data = await resp.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        logger.info(f"✅ Gemini key #{self.gemini_current_index + 1} OK")
                        return data['candidates'][0]['content']['parts'][0]['text'].strip()
                    else:
                        return self.get_fallback_response()
                        
        except Exception as e:
            logger.error(f"Gemini exception: {type(e).__name__}")
            if retry_count < max_retries:
                return await self.get_gemini_response(messages, retry_count + 1)
            return self.get_fallback_response()

    async def get_chatgpt_response(self, messages, retry_count=0):
        """Gọi ChatGPT API với auto key rotation."""
        max_retries = len(self.chatgpt_keys) if self.chatgpt_keys else 1
        
        try:
            api_key = self.get_next_chatgpt_key()
            if not api_key:
                logger.warning("⚠️ Không có ChatGPT key, fallback sang Gemini")
                return await self.get_gemini_response(messages)
            
            chatgpt_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            
            payload = {
                "model": "gpt-4o",
                "messages": chatgpt_messages,
                "max_tokens": 4096,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.chatgpt_api_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=15
                ) as resp:
                    
                    content_type = resp.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        logger.error(f"❌ ChatGPT key #{self.chatgpt_current_index + 1} trả về HTML")
                        self.mark_key_failed('chatgpt', self.chatgpt_current_index)
                        
                        if retry_count < max_retries:
                            return await self.get_chatgpt_response(messages, retry_count + 1)
                        else:
                            logger.warning(f"🔄 Chuyển sang Gemini")
                            return await self.get_gemini_response(messages)
                    
                    if resp.status == 200:
                        data = await resp.json()
                        if 'choices' in data and len(data['choices']) > 0:
                            logger.info(f"✅ ChatGPT key #{self.chatgpt_current_index + 1} OK")
                            return data['choices'][0]['message']['content'].strip()
                        else:
                            if retry_count < max_retries:
                                return await self.get_chatgpt_response(messages, retry_count + 1)
                            return await self.get_gemini_response(messages)
                    
                    elif resp.status == 429:
                        self.mark_key_failed('chatgpt', self.chatgpt_current_index)
                        if retry_count < max_retries:
                            await asyncio.sleep(1)
                            return await self.get_chatgpt_response(messages, retry_count + 1)
                        else:
                            return await self.get_gemini_response(messages)
                    
                    elif resp.status == 401:
                        self.mark_key_failed('chatgpt', self.chatgpt_current_index)
                        if retry_count < max_retries:
                            return await self.get_chatgpt_response(messages, retry_count + 1)
                        return await self.get_gemini_response(messages)
                    
                    else:
                        self.mark_key_failed('chatgpt', self.chatgpt_current_index)
                        if retry_count < max_retries:
                            return await self.get_chatgpt_response(messages, retry_count + 1)
                        return await self.get_gemini_response(messages)
                        
        except Exception as e:
            logger.error(f"ChatGPT exception: {type(e).__name__}")
            if retry_count < max_retries:
                return await self.get_chatgpt_response(messages, retry_count + 1)
            return await self.get_gemini_response(messages)

    def get_fallback_response(self):
        """Phản hồi dự phòng."""
        responses = [
            "AI đang bận, hỏi lại sau nha!",
            "Tạm thời không xử lý được 😅",
            "Có chút trục trặc kỹ thuật!",
            "API đang nghỉ!",
        ]
        return random.choice(responses)

    async def generate_ai_response(self, user_id: int, user_message: str) -> str:
        """Tạo câu trả lời AI."""
        try:
            learning_context = self.get_learning_context(user_message)
            
            enhanced_prompt = self.system_prompt
            if learning_context:
                enhanced_prompt += learning_context
            
            messages = [{"role": "system", "content": enhanced_prompt}]
            
            if user_id in self.user_histories:
                for msg in self.user_histories[user_id][-5:]:
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            if self.current_provider == 'gemini':
                response = await self.get_gemini_response(messages)
            else:
                response = await self.get_chatgpt_response(messages)
            
            self.add_to_learning_data(user_message, response, self.current_provider)
            
            if user_id not in self.user_histories:
                self.user_histories[user_id] = []
            
            self.user_histories[user_id].append({"role": "user", "content": user_message[:150]})
            self.user_histories[user_id].append({"role": "assistant", "content": response[:150]})
            
            if len(self.user_histories[user_id]) > self.MAX_HISTORY_PER_USER:
                self.user_histories[user_id] = self.user_histories[user_id][-150:]
            
            return response
            
        except Exception as e:
            logger.error(f"Generate AI error: {e}")
            return "🤖 Có lỗi xảy ra!"

    async def send_long_message(self, channel, content, reply_to=None):
        """Gửi tin nhắn dài."""
        max_length = 1900
        chunks = []
        
        while len(content) > max_length:
            split_point = content.rfind('\n', 0, max_length)
            if split_point == -1:
                split_point = content.rfind(' ', 0, max_length)
            if split_point == -1:
                split_point = max_length
            
            chunks.append(content[:split_point])
            content = content[split_point:].lstrip()
        
        if content:
            chunks.append(content)
        
        first_message = None
        if reply_to:
            first_message = await reply_to.reply(chunks[0])
        else:
            first_message = await channel.send(chunks[0])
        
        for chunk in chunks[1:]:
            if first_message:
                await first_message.reply(chunk)
            else:
                await channel.send(chunk)

    # ==================== COMMANDS ====================
    @commands.command(name='auto_ai', aliases=['ai_mode'])
    async def auto_ai(self, ctx, mode: str = None, provider: str = None):
        """Usage: {prefix}auto_ai [on/off] [gemini/chatgpt]"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        if mode is None:
            status = "✅ **BẬT**" if self.ai_active else "❌ **TẮT**"
            history = sum(len(h) for h in self.user_histories.values())
            
            gemini_status = f"{len(self.gemini_keys) - len(self.gemini_failed_keys)}/{len(self.gemini_keys)}"
            chatgpt_status = f"{len(self.chatgpt_keys) - len(self.chatgpt_failed_keys)}/{len(self.chatgpt_keys)}"
            
            await ctx.send(
                f"**🤖 AI Auto-Responder:** {status}\n"
                f"**🔧 Provider:** {self.current_provider.upper()}\n"
                f"**🔑 Gemini keys:** {gemini_status} khả dụng\n"
                f"**🔑 ChatGPT keys:** {chatgpt_status} khả dụng\n"
                f"**📊 Lịch sử:** {history} tin nhắn\n"
                f"**📚 Learning data:** {len(self.learning_data)}/200 câu\n\n"
                f"**Cách dùng:**\n"
                f"• `{ctx.prefix}auto_ai on [gemini/chatgpt]` - Bật AI\n"
                f"• `{ctx.prefix}auto_ai off` - Tắt AI\n"
                f"• `{ctx.prefix}ai_provider <provider>` - Đổi provider\n"
                f"• `{ctx.prefix}ask_ai <câu hỏi>` - Hỏi trực tiếp\n"
                f"• `{ctx.prefix}check_keys` - Kiểm tra keys"
            )
            return
        
        mode = mode.lower()
        
        if mode in ['on', 'bật', 'enable']:
            if provider:
                provider = provider.lower()
                if 'gemini' in provider:
                    self.current_provider = 'gemini'
                elif 'gpt' in provider or 'chat' in provider:
                    self.current_provider = 'chatgpt'
            
            self.ai_active = True
            await ctx.send(
                f"✅ **ĐÃ BẬT AI**\n"
                f"**Provider:** {self.current_provider.upper()}\n"
                f"**Keys:** Gemini {len(self.gemini_keys)}, ChatGPT {len(self.chatgpt_keys)}\n"
                f"**Learning:** {len(self.learning_data)} câu đã học\n"
                f"Tự động reply khi tag/reply/DM"
            )
            
        elif mode in ['off', 'tắt', 'disable']:
            self.ai_active = False
            self.save_learning_data()
            await ctx.send("✅ **ĐÃ TẮT AI** (đã lưu learning data)")
            
        else:
            await ctx.send(f"❌ Sai cú pháp! Dùng: `{ctx.prefix}auto_ai on/off [provider]`")

    @commands.command(name='ai_provider', aliases=['switch_ai', 'provider'])
    async def ai_provider(self, ctx, provider: str = None):
        """Usage: {prefix}ai_provider [gemini/chatgpt]"""  
        try:
            await ctx.message.delete()
        except:
            pass
        
        if provider is None:
            gemini_ok = len(self.gemini_keys) - len(self.gemini_failed_keys)
            chatgpt_ok = len(self.chatgpt_keys) - len(self.chatgpt_failed_keys)
            
            await ctx.send(
                f"**🔧 PROVIDER HIỆN TẠI:** {self.current_provider.upper()}\n\n"
                f"**🟢 Gemini:** {gemini_ok}/{len(self.gemini_keys)} keys khả dụng\n"
                f"**🔵 ChatGPT:** {chatgpt_ok}/{len(self.chatgpt_keys)} keys khả dụng\n\n"
                f"**Đổi provider:**\n"
                f"• `{ctx.prefix}ai_provider gemini`\n"
                f"• `{ctx.prefix}ai_provider chatgpt`"
            )
            return
        
        provider = provider.lower()
        
        if 'gemini' in provider:
            if not self.gemini_keys:
                await ctx.send("❌ **Không có Gemini key nào trong config!**\n\nThêm key vào `config.json` → `ai_config` → `gemini_keys`")
                return
            
            old = self.current_provider
            self.current_provider = 'gemini'
            available = len(self.gemini_keys) - len(self.gemini_failed_keys)
            await ctx.send(
                f"✅ **Đã đổi provider:** {old.upper()} → GEMINI\n"
                f"🔑 {available}/{len(self.gemini_keys)} keys khả dụng"
            )
            
        elif 'gpt' in provider or 'chat' in provider:
            if not self.chatgpt_keys:
                await ctx.send("❌ **Không có ChatGPT key nào trong config!**\n\nThêm key vào `config.json` → `ai_config` → `chatgpt_keys`")
                return
            
            old = self.current_provider
            self.current_provider = 'chatgpt'
            available = len(self.chatgpt_keys) - len(self.chatgpt_failed_keys)
            await ctx.send(
                f"✅ **Đã đổi provider:** {old.upper()} → CHATGPT\n"
                f"🔑 {available}/{len(self.chatgpt_keys)} keys khả dụng"
            )
            
        else:
            await ctx.send(
                f"❌ **Provider không hợp lệ!**\n\n"
                f"Chọn một trong hai:\n"
                f"• `{ctx.prefix}ai_provider gemini`\n"
                f"• `{ctx.prefix}ai_provider chatgpt`"
            )

    @commands.command(name='ask_ai', aliases=['ai'])
    async def ask_ai(self, ctx, *, question: str):
        """Usage: {prefix}ask_ai <question>"""
        if ctx.author.id != self.bot.user.id:
            await ctx.send("❌ Chỉ owner mới dùng được lệnh này!")
            return
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        try:
            async with ctx.typing():
                emoji = "🟢" if self.current_provider == 'gemini' else "🔵"
                response = await self.generate_ai_response(ctx.author.id, question)
                
                await self.send_long_message(
                    ctx.channel,
                    f"{emoji} **[{self.current_provider.upper()}]**\n{response}",
                    None
                )
        
        except Exception as e:
            logger.error(f"Ask AI error: {e}")
            await ctx.send(f"❌ Lỗi: {e}")

    @commands.command(name='check_keys')
    async def check_keys(self, ctx):
        """Usage: {prefix}check_keys"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        checking_msg = await ctx.send("🔍 **Đang kiểm tra keys...**")
        
        results = []
        
        # Test Gemini keys
        results.append("**🟢 GEMINI KEYS:**")
        if not self.gemini_keys:
            results.append("❌ Không có key nào trong config")
        else:
            gemini_ok_count = 0
            
            for i, key in enumerate(self.gemini_keys, 1):
                try:
                    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={key}"
                    test_payload = {
                        "contents": [{"role": "user", "parts": [{"text": "test"}]}],
                        "generationConfig": {"maxOutputTokens": 10}
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(test_url, json=test_payload, timeout=10) as resp:
                            if resp.status == 200:
                                results.append(f"✅ Key #{i}: **OK** - Khả dụng")
                                gemini_ok_count += 1
                            elif resp.status == 429:
                                results.append(f"⚠️ Key #{i}: **Rate Limit**")
                            elif resp.status == 400:
                                data = await resp.json()
                                error_str = str(data)
                                if 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                                    results.append(f"❌ Key #{i}: **HẾT QUOTA**")
                                else:
                                    results.append(f"⚠️ Key #{i}: **Lỗi 400**")
                            elif resp.status == 403:
                                results.append(f"❌ Key #{i}: **KHÔNG HỢP LỆ**")
                            else:
                                results.append(f"❌ Key #{i}: **Lỗi {resp.status}**")
                except asyncio.TimeoutError:
                    results.append(f"⏱️ Key #{i}: **Timeout**")
                except Exception as e:
                    results.append(f"❌ Key #{i}: **{type(e).__name__}**")
                
                await asyncio.sleep(0.5)
            
            results.append(f"\n**Gemini:** {gemini_ok_count}/{len(self.gemini_keys)} keys OK")
        
        results.append("")
        
        results.append("**🔵 CHATGPT KEYS:**")
        if not self.chatgpt_keys:
            results.append("❌ Không có key nào trong config")
        else:
            chatgpt_ok_count = 0
            
            for i, key in enumerate(self.chatgpt_keys, 1):
                try:
                    payload = {
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(self.chatgpt_api_url, json=payload, headers=headers, timeout=10) as resp:
                            if resp.status == 200:
                                results.append(f"✅ Key #{i}: **OK** - Khả dụng")
                                chatgpt_ok_count += 1
                            elif resp.status == 429:
                                results.append(f"⚠️ Key #{i}: **Rate Limit**")
                            elif resp.status == 401:
                                results.append(f"❌ Key #{i}: **KHÔNG HỢP LỆ**")
                            else:
                                results.append(f"❌ Key #{i}: **Lỗi {resp.status}**")
                except asyncio.TimeoutError:
                    results.append(f"⏱️ Key #{i}: **Timeout**")
                except Exception as e:
                    results.append(f"❌ Key #{i}: **{type(e).__name__}**")
                
                await asyncio.sleep(0.5)
            
            results.append(f"\n**ChatGPT:** {chatgpt_ok_count}/{len(self.chatgpt_keys)} keys OK")
        
        self.gemini_failed_keys.clear()
        self.chatgpt_failed_keys.clear()
        results.append(f"\n✅ Đã reset danh sách key lỗi")
        
        result_text = "\n".join(results)
        
        if len(result_text) > 1900:
            chunks = []
            current = ""
            for line in results:
                if len(current) + len(line) + 1 > 1900:
                    chunks.append(current)
                    current = line + "\n"
                else:
                    current += line + "\n"
            if current:
                chunks.append(current)
            
            await checking_msg.edit(content=chunks[0])
            for chunk in chunks[1:]:
                await ctx.send(chunk)
        else:
            await checking_msg.edit(content=result_text)

    @commands.command(name='ai_history')
    async def ai_history(self, ctx, action: str = None):
        """Usage: {prefix}ai_history [clear/stats/save]"""
        """Quản lý lịch sử AI."""
        try:
            await ctx.message.delete()
        except:
            pass
        
        user_id = ctx.author.id
        
        if action is None:
            user_count = len(self.user_histories.get(user_id, []))
            total_count = sum(len(h) for h in self.user_histories.values())
            await ctx.send(
                f"**📊 Thống kê:**\n"
                f"• Provider: {self.current_provider.upper()}\n"
                f"• Lịch sử của bạn: {user_count}\n"
                f"• Tổng: {total_count}\n\n"
                f"`{ctx.prefix}ai_history clear/stats`"
            )
            return
        
        if action == 'clear':
            if user_id in self.user_histories:
                del self.user_histories[user_id]
                await ctx.send("✅ Đã xóa lịch sử!")
            else:
                await ctx.send("✅ Chưa có lịch sử!")
                
        elif action == 'stats':
            await ctx.send(
                f"**📊 Thống kê:**\n"
                f"• Provider: {self.current_provider.upper()}\n"
                f"• Số user: {len(self.user_histories)}\n"
                f"• Tổng tin nhắn: {sum(len(h) for h in self.user_histories.values())}\n"
                f"• Giới hạn/user: {self.MAX_HISTORY_PER_USER}"
            )

        elif action == 'save':
            self.save_learning_data()
            await ctx.send(f"✅ **Đã lưu {len(self.learning_data)} câu hỏi!**")
            return
        
        total = len(self.learning_data)
        gemini_count = sum(1 for d in self.learning_data if d.get('provider') == 'gemini')
        chatgpt_count = sum(1 for d in self.learning_data if d.get('provider') == 'chatgpt')
        
        recent = self.learning_data[-5:] if self.learning_data else []
        recent_text = ""
        if recent:
            recent_text = "\n\n**5 câu hỏi gần nhất:**\n"
            for i, entry in enumerate(recent, 1):
                q = entry['question'][:50] + "..." if len(entry['question']) > 50 else entry['question']
                recent_text += f"{i}. {q}\n"
        
        await ctx.send(
            f"**📚 Learning Data Stats:**\n"
            f"• Tổng câu hỏi: {total}/200\n"
            f"• Gemini: {gemini_count}\n"
            f"• ChatGPT: {chatgpt_count}\n"
            f"• File: `{self.data_file}`{recent_text}\n\n"
            f"**Lệnh:**\n"
            f"• `{ctx.prefix}ai_learning save` - Lưu ngay\n"
            f"• `{ctx.prefix}ai_learning clear` - Xóa data"
        )

    # ==================== MESSAGE HANDLER ====================
    @commands.Cog.listener()
    async def on_message(self, message):
        """Lắng nghe tin nhắn để auto-reply."""
        if message.author.bot or not self.ai_active:
            return
        
        should_respond = False
        
        if self.bot.user in message.mentions:
            should_respond = True
            
        if message.reference:
            try:
                replied = await message.channel.fetch_message(message.reference.message_id)
                if replied.author == self.bot.user:
                    should_respond = True
            except:
                pass
        
        if isinstance(message.channel, discord.DMChannel):
            if message.author.id != self.bot.user.id:
                should_respond = True
        
        if should_respond:
            try:
                user_msg = message.content
                if self.bot.user in message.mentions:
                    for m in message.mentions:
                        user_msg = user_msg.replace(f'<@{m.id}>', '').replace(f'<@!{m.id}>', '')
                user_msg = user_msg.strip()
                
                if not user_msg:
                    user_msg = "Xin chào!"
                
                async with message.channel.typing():
                    response = await self.generate_ai_response(message.author.id, user_msg)
                    await self.send_long_message(message.channel, response, message)
            
            except Exception as e:
                logger.error(f"Auto reply error: {e}")

def setup(bot):
    """Cog setup function."""
    bot.add_cog(ai(bot))
