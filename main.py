"""
Discord Selfbot - Main Entry Point
Refactored with Cog Architecture
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands
from pystyle import Center, Colorate, Colors
from colorama import init as colorama_init

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Pillow not installed. Image help will be disabled.")
    print("Install: pip install pillow")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logging.getLogger('discord').setLevel(logging.ERROR)

colorama_init()

CONFIG_PATH = "config.json"
DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

# ==================== DATA RESET ====================

def reset_data_files():
    """Reset all data JSON files to default state on bot startup."""
    default_data = {
        "triggers.json": {
            "auto_responses": {},
            "auto_messages": {},
            "auto_mess_config": {
                "active": False,
                "mode": "message",
                "value": 5,
                "channel_id": None
            }
        },
        "message_afk.json": {
            "auto_responses": {},
            "auto_messages": {},
            "afk_data": {}
        },
        "bot_status.json": {
            "owo_farm": {},
            "owo_bet": {},
            "snipe_nitro": {},
            "rotator": {
                "active": False
            }
        }
    }
    
    for filename, default_content in default_data.items():
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=4)
            logger.info(f"✅ Reset {filename} to default state")
        except Exception as e:
            logger.error(f"❌ Failed to reset {filename}: {e}")

# ==================== CONFIG LOADER ====================

def load_config():
    """Load configuration from JSON file."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {CONFIG_PATH}")
        sys.exit(1)

def save_config(config):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

# ==================== IMAGE GENERATOR ====================

def generate_help_image(cog_name, commands_data, prefix):
    """Generate simple help image with dark blue background and white text."""
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Simple color scheme: dark blue background, white text
        bg_color = '#0A1929'  # Xanh biển đen
        text_color = '#FFFFFF'  # Chữ trắng
        box_color = '#1E3A5F'  # Xanh đậm hơn một chút cho command boxes
        
        num_commands = len(commands_data)
        line_height = 80
        header_height = 100
        footer_height = 50
        padding = 40
        
        width = 800
        height = header_height + (num_commands * line_height) + footer_height + (padding * 2)
        
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            cmd_font = ImageFont.truetype("arial.ttf", 24)
            desc_font = ImageFont.truetype("arial.ttf", 18)
            footer_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                cmd_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                title_font = ImageFont.load_default()
                cmd_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
                footer_font = ImageFont.load_default()
        
        current_y = padding
        
        header_text = f"{cog_name.upper()} COMMANDS"
        draw.text((width // 2, current_y + 20), header_text, 
                 fill=text_color, font=title_font, anchor="mm")
        
        # Draw subtitle
        subtitle = f"{num_commands} Available Commands"
        draw.text((width // 2, current_y + 60), subtitle, 
                 fill=text_color, font=desc_font, anchor="mm")
        
        current_y += header_height
        
        draw.line([(padding, current_y), (width - padding, current_y)], 
                 fill=text_color, width=2)
        current_y += 20
        
        for cmd_name, aliases, description in commands_data:
            box_y = current_y
            draw.rectangle(
                [(padding, box_y), (width - padding, box_y + line_height - 10)],
                fill=box_color,
                outline=text_color,
                width=1
            )
            
            # Command name
            cmd_text = f"{prefix}{cmd_name}"
            if aliases:
                cmd_text += f" ({aliases})"
            
            draw.text((padding + 20, box_y + 15), cmd_text, 
                     fill=text_color, font=cmd_font)
            
            # Description
            desc_text = description[:70] + "..." if len(description) > 70 else description
            draw.text((padding + 20, box_y + 45), desc_text, 
                     fill=text_color, font=desc_font)
            
            current_y += line_height
        
        # Draw footer
        current_y += 20
        draw.line([(padding, current_y), (width - padding, current_y)], 
                 fill=text_color, width=2)
        current_y += 20
        
        footer_text = f"Usage: {prefix}<command> | Prefix: {prefix}"
        draw.text((width // 2, current_y + 10), footer_text, 
                 fill=text_color, font=footer_font, anchor="mm")
        
        # Save to BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        return img_bytes
        
    except Exception as e:
        logger.error(f"Error generating help image: {e}")
        return None

# ==================== BOT SETUP ====================

config = load_config()
PREFIX = config.get('prefix', '.')
TOKEN = config.get('token')

if not TOKEN:
    logger.error("No token found in config.json")
    sys.exit(1)

# Strip whitespace from token (common issue)
TOKEN = TOKEN.strip()

# Debug: Check token format (without exposing full token)
if TOKEN:
    logger.info(f"Token length: {len(TOKEN)} characters")
    logger.info(f"Token starts with: {TOKEN[:10]}...")
    # Check if it looks like a user token or bot token
    if TOKEN.count('.') != 2:
        logger.warning("Token format may be incorrect (expected 2 dots for Discord token)")

# Create bot instance
# Note: For selfbots, intents may not be needed
bot = commands.Bot(
    description='BOT',
    command_prefix=PREFIX,
    self_bot=True
)
bot.remove_command('help')

# Store config in bot instance
bot.config = config
bot.config_path = CONFIG_PATH

# ==================== EVENT HANDLERS ====================

@bot.event
async def on_ready():
    """Bot ready event."""
    try:
        os.system('clear' if os.name != 'nt' else 'cls')
        
        print(
            Center.XCenter(
                Colorate.Vertical(
                    Colors.blue_to_cyan,
                    f"Đã đăng nhập với tên {bot.user.name}",
                    1,
                )
            )
        )
        
        logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
        logger.info(f"Prefix: {PREFIX}")
        logger.info(f"Loaded {len(bot.cogs)} cogs")
        logger.info(f"Loaded {len(bot.commands)} commands")
        
        # Load all cogs
        await load_cogs()
        
        # Store start time
        bot.start_time = datetime.now()
        
    except Exception as e:
        logger.error(f"Error in on_ready: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore command not found
    
    logger.error(f"Command error: {error}")
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    error_msg = str(error)
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."
    
    await ctx.send(f"❌ **Lỗi:** {error_msg}", delete_after=10)

@bot.event
async def on_message(message):
    """Handle incoming messages."""
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)

# ==================== COG MANAGEMENT ====================

async def load_cogs():
    """Load all cogs from the cogs directory."""
    cogs_dir = "cogs"
    
    if not os.path.exists(cogs_dir):
        logger.warning(f"Cogs directory not found: {cogs_dir}")
        return
    
    loaded = 0
    failed = 0
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = filename[:-3]
            try:
                bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"✅ Loaded cog: {cog_name}")
                loaded += 1
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog_name}: {e}")
                failed += 1
    
    logger.info(f"Cogs loaded: {loaded} | Failed: {failed}")

# ==================== RELOAD COMMANDS ====================

@bot.command(name='reload', aliases=['rl'])
async def reload_cogs(ctx, cog_name: str = None):
    """
    Reload cogs (tất cả hoặc chỉ định).
    
    Cách dùng:
        .reload           - Reload tất cả cogs
        .reload general   - Reload cog 'general'
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    if cog_name:
        # Reload specific cog
        try:
            bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ **Đã reload cog:** `{cog_name}`", delete_after=5)
            logger.info(f"✅ Reloaded cog: {cog_name}")
        except Exception as e:
            await ctx.send(f"❌ **Lỗi reload `{cog_name}`:** {e}", delete_after=10)
            logger.error(f"Failed to reload {cog_name}: {e}")
    else:
        # Reload all cogs
        reloaded = 0
        failed = 0
        failed_cogs = []
        
        for ext_name in list(bot.extensions.keys()):
            try:
                bot.reload_extension(ext_name)
                reloaded += 1
                logger.info(f"✅ Reloaded: {ext_name}")
            except Exception as e:
                failed += 1
                cog_short_name = ext_name.split('.')[-1]
                failed_cogs.append(cog_short_name)
                logger.error(f"❌ Failed to reload {ext_name}: {e}")
        
        # Tạo message chi tiết
        result_msg = f"✅ **Đã reload {reloaded} cogs**"
        if failed > 0:
            result_msg += f"\n❌ **Thất bại: {failed} cogs** ({', '.join(failed_cogs)})"
        
        await ctx.send(result_msg, delete_after=10)

@bot.command(name='reload_config', aliases=['rconfig', 'rc'])
async def reload_config(ctx):
    """
    Reload file config.json.
    
    Chức năng:
        - Tải lại config.json
        - Cập nhật prefix nếu có thay đổi
        - Cập nhật các settings khác
    
    Cách dùng:
        .reload_config
        .rconfig
        .rc
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        # Reload config
        global config, PREFIX
        config = load_config()
        
        # Update bot config
        bot.config = config
        
        # Update prefix if changed
        new_prefix = config.get('prefix', '.')
        prefix_changed = (new_prefix != PREFIX)
        
        if prefix_changed:
            PREFIX = new_prefix
            bot.command_prefix = new_prefix
        
        # Tạo thông báo chi tiết
        msg = "✅ **Đã reload config.json**\n"
        msg += f"📌 **Prefix:** `{PREFIX}`"
        if prefix_changed:
            msg += " *(đã thay đổi)*"
        msg += f"\n🔑 **Token length:** {len(config.get('token', ''))} chars"
        
        await ctx.send(msg, delete_after=10)
        logger.info("✅ Config reloaded successfully")
        
    except Exception as e:
        await ctx.send(f"❌ **Lỗi reload config:** {e}", delete_after=10)
        logger.error(f"Failed to reload config: {e}")

@bot.command(name='reload_rpc', aliases=['rrpc'])
async def reload_rpc(ctx):
    """
    Reload file rich_presence.json cho Presence cog.
    
    Chức năng:
        - Tải lại rich_presence.json
        - Cập nhật config cho custom RPC
        - RPC đang chạy sẽ dùng config mới ở chu kỳ tiếp theo
    
    Cách dùng:
        .reload_rpc
        .rrpc
    
    Lưu ý:
        - Presence cog phải được load
        - File rich_presence.json phải tồn tại
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        # Check if presence cog exists
        presence_cog = bot.get_cog('presence')
        
        if not presence_cog:
            await ctx.send("❌ **Presence cog không được load**\n💡 Dùng `.load presence` để load", delete_after=10)
            return
        
        # Reload RPC config
        if hasattr(presence_cog, '_load_rpc_config'):
            rpc_data = presence_cog._load_rpc_config()
            presence_cog.rpc_data = rpc_data
            
            msg = "✅ **Đã reload rich_presence.json**\n"
            msg += f"📊 **Status:** {'Loaded' if rpc_data else 'Empty/Error'}\n"
            msg += "💡 **Tip:** Custom RPC đang chạy sẽ tự động dùng config mới ở chu kỳ tiếp theo"
            
            await ctx.send(msg, delete_after=15)
            logger.info("✅ Rich presence config reloaded")
        else:
            await ctx.send("❌ **Presence cog không hỗ trợ reload RPC**", delete_after=10)
            
    except Exception as e:
        await ctx.send(f"❌ **Lỗi reload RPC:** {e}", delete_after=10)
        logger.error(f"Failed to reload RPC: {e}")

@bot.command(name='reload_all', aliases=['rall'])
async def reload_all(ctx):
    """
    Reload mọi thứ: config.json, rich_presence.json, và tất cả cogs.
    
    Chức năng:
        1. Reload config.json
        2. Reload rich_presence.json (nếu có Presence cog)
        3. Reload tất cả cogs
    
    Cách dùng:
        .reload_all
        .rall
    
    Đây là lệnh tiện lợi để refresh toàn bộ bot sau khi sửa config hoặc code.
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    results = []
    
    # 1. Reload config
    try:
        global config, PREFIX
        config = load_config()
        bot.config = config
        
        new_prefix = config.get('prefix', '.')
        if new_prefix != PREFIX:
            PREFIX = new_prefix
            bot.command_prefix = new_prefix
        
        results.append("✅ Config")
        logger.info("✅ Config reloaded")
    except Exception as e:
        results.append(f"❌ Config: {str(e)[:50]}")
        logger.error(f"Config reload failed: {e}")
    
    # 2. Reload RPC
    try:
        presence_cog = bot.get_cog('presence')
        if presence_cog and hasattr(presence_cog, '_load_rpc_config'):
            rpc_data = presence_cog._load_rpc_config()
            presence_cog.rpc_data = rpc_data
            results.append("✅ Rich Presence")
            logger.info("✅ RPC reloaded")
        else:
            results.append("⚠️ Rich Presence (cog not loaded)")
    except Exception as e:
        results.append(f"❌ Rich Presence: {str(e)[:50]}")
        logger.error(f"RPC reload failed: {e}")
    
    # 3. Reload all cogs
    reloaded = 0
    failed = 0
    failed_cogs = []
    
    for ext_name in list(bot.extensions.keys()):
        try:
            bot.reload_extension(ext_name)
            reloaded += 1
            logger.info(f"✅ Reloaded: {ext_name}")
        except Exception as e:
            failed += 1
            cog_short_name = ext_name.split('.')[-1]
            failed_cogs.append(cog_short_name)
            logger.error(f"❌ Failed to reload {ext_name}: {e}")
    
    if failed > 0:
        results.append(f"✅ Cogs: {reloaded} | ❌ Failed: {failed} ({', '.join(failed_cogs)})")
    else:
        results.append(f"✅ Cogs: {reloaded}")
    
    # Send results
    msg = "**🔄 RELOAD EVERYTHING**\n"
    msg += "\n".join(f"• {r}" for r in results)
    
    await ctx.send(msg, delete_after=15)
    logger.info(f"Reload all completed: {reloaded} cogs reloaded, {failed} failed")

@bot.command(name='load')
async def load_cog(ctx, cog_name: str):
    """
    Load một cog cụ thể.
    
    Cách dùng:
        .load general
        .load reactions
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ **Đã load cog:** `{cog_name}`", delete_after=5)
        logger.info(f"✅ Loaded cog: {cog_name}")
    except Exception as e:
        await ctx.send(f"❌ **Lỗi load `{cog_name}`:** {e}", delete_after=10)
        logger.error(f"Failed to load {cog_name}: {e}")

@bot.command(name='unload')
async def unload_cog(ctx, cog_name: str):
    """
    Unload một cog cụ thể.
    
    Cách dùng:
        .unload general
        .unload reactions
    """
    try:
        await ctx.message.delete()
    except:
        pass
    
    try:
        bot.unload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ **Đã unload cog:** `{cog_name}`", delete_after=5)
        logger.info(f"✅ Unloaded cog: {cog_name}")
    except Exception as e:
        await ctx.send(f"❌ **Lỗi unload `{cog_name}`:** {e}", delete_after=10)
        logger.error(f"Failed to unload {cog_name}: {e}")

# ==================== BASIC COMMANDS ====================

@bot.command(name='help', aliases=['cmd', 'h'])
async def help_command(ctx, category: str = None):
    """Display help menu with beautiful images."""
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not category:
        # Main menu - text version
        cogs_info = []
        
        # Danh sách các cog có trong bot
        for cog_name in sorted(bot.cogs.keys()):
            cog = bot.cogs[cog_name]
            cmd_count = len(cog.get_commands())
            if cmd_count > 0:
                cogs_info.append(f"{cog_name.lower():<12} ({cmd_count} cmds)")
        
        # Chia thành 2 cột
        half = (len(cogs_info) + 1) // 2
        col1 = cogs_info[:half]
        col2 = cogs_info[half:]
        
        help_text = f"""```
🤖 SELFBOT MENU | Prefix: {PREFIX}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 AVAILABLE COGS:
"""
        # Ghép 2 cột
        for i in range(max(len(col1), len(col2))):
            left = col1[i] if i < len(col1) else ""
            right = col2[i] if i < len(col2) else ""
            help_text += f"\n{left:<30} {right}"
        
        help_text += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 USAGE:
  {PREFIX}help <cog>     - Xem lệnh của cog (với ảnh!)
  {PREFIX}cogs           - Danh sách cogs
  
🔄 RELOAD COMMANDS:
  {PREFIX}reload_all     - Reload config/rpc/cogs (ALL)
  {PREFIX}reload         - Reload tất cả cogs
  {PREFIX}reload <cog>   - Reload 1 cog cụ thể
  {PREFIX}reload_config  - Reload config.json
  {PREFIX}reload_rpc     - Reload rich_presence.json
  
📌 QUICK COMMANDS:
  {PREFIX}ping           - Kiểm tra latency
  {PREFIX}prefix <new>   - Đổi prefix
  {PREFIX}shutdown       - Tắt bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```"""
        await ctx.send(help_text, delete_after=60)
    else:
        # Category specific help - IMAGE VERSION
        # Try to find cog by name (case-insensitive)
        cog = None
        category_lower = category.lower()
        for cog_name, cog_obj in bot.cogs.items():
            if cog_name.lower() == category_lower:
                cog = cog_obj
                break
        
        if not cog:
            await ctx.send(f"❌ Không tìm thấy cog: `{category}`\nDùng `{PREFIX}help` để xem danh sách", delete_after=10)
            return
        
        commands_list = cog.get_commands()
        if not commands_list:
            await ctx.send(f"❌ Cog `{category}` không có lệnh nào.", delete_after=10)
            return
        
        # Prepare commands data
        commands_data = []
        for cmd in sorted(commands_list, key=lambda x: x.name):
            # Aliases
            aliases = ", ".join(cmd.aliases) if cmd.aliases else ""
            
            # Description - chỉ lấy dòng đầu
            desc = cmd.help or cmd.brief or "No description"
            desc = desc.split('\n')[0].strip()
            
            commands_data.append((cmd.name, aliases, desc))
        
        # Try to generate image
        if PIL_AVAILABLE:
            img_bytes = generate_help_image(category, commands_data, PREFIX)
            
            if img_bytes:
                # Send image
                file = discord.File(img_bytes, filename=f"{category}_help.png")
                await ctx.send(file=file)
                return
        
        # Fallback to text if image generation failed
        help_text = f"**{category.upper()} COMMANDS** ({len(commands_list)} lệnh)\n"
        help_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n```\n"
        
        for cmd_name, aliases, desc in commands_data:
            if aliases:
                cmd_display = f"{cmd_name} ({aliases})"
            else:
                cmd_display = cmd_name
            
            if len(desc) > 60:
                desc = desc[:57] + "..."
            
            help_text += f"{PREFIX}{cmd_display}\n"
            help_text += f"  └─ {desc}\n\n"
        
        help_text += "```\n"
        help_text += f"💡 **Tip:** Gõ `{PREFIX}<command>` để dùng lệnh"
        
        await ctx.send(help_text, delete_after=60)

@bot.command(name='cogs')
async def list_cogs(ctx):
    """List all loaded cogs."""
    try:
        await ctx.message.delete()
    except:
        pass
    
    cogs_list = "**📦 LOADED COGS**\n```\n"
    for cog_name, cog in bot.cogs.items():
        command_count = len(cog.get_commands())
        cogs_list += f"✅ {cog_name} ({command_count} commands)\n"
    cogs_list += "```"
    await ctx.send(cogs_list, delete_after=30)

@bot.command(name='prefix')
async def change_prefix(ctx, new_prefix: str):
    """Change bot prefix."""
    try:
        await ctx.message.delete()
    except:
        pass
    
    global PREFIX
    PREFIX = new_prefix
    bot.command_prefix = new_prefix
    bot.config['prefix'] = new_prefix
    save_config(bot.config)
    
    await ctx.send(f"✅ Đã đổi prefix thành: `{new_prefix}`", delete_after=10)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency."""
    try:
        await ctx.message.delete()
    except:
        pass
    
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 **Pong!** Latency: {latency}ms", delete_after=10)

# ==================== SHUTDOWN ====================

@bot.command(name='shutdown', aliases=['stop', 'quit'])
async def shutdown(ctx):
    """Shutdown the bot."""
    try:
        await ctx.message.delete()
    except:
        pass
    
    await ctx.send("👋 **Shutting down...**")
    logger.info("Bot shutdown requested")
    await bot.close()

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    try:
        # 0. Reset data files về trạng thái gốc
        print("🔄 Đang reset data files...")
        reset_data_files()
        
        # 1. Kiểm tra token
        if not config.get("token"):
            print("❌ KHÔNG TÌM THẤY TOKEN trong config.json!")
            print("Vui lòng thêm token vào config.json")
            sys.exit(1)
        
        TOKEN = config.get("token")
        
        if not TOKEN or len(TOKEN) < 50:
            print("❌ TOKEN KHÔNG HỢP LỆ! (quá ngắn hoặc trống)")

        if not PIL_AVAILABLE:
            print("\n⚠️  WARNING: Pillow not installed")
            print("Image help will use text fallback")
            print("Install with: pip install pillow\n")

        print("🚀 Đang khởi động bot...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        bot.run(TOKEN, bot=False)
        
    except KeyboardInterrupt:
        print("\nℹ️ Bot đã dừng")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ LỖI: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
