# Discord Selfbot - Complete Documentation

A powerful Discord selfbot with multiple automation features, AI integration, and utility commands.
---
##  https://discord.gg/7euPjreCY7
## 🚀 Installation & Setup

### Prerequisites
```bash
Python 3.12+
```

**Required packages (`requirements.txt`):**
```txt
discord.py==1.7.3
discord.py-self_embed
aiohttp>=3.8.0
pynacl>=1.5.0
python-dotenv>=0.19.0
google-generativeai
googletrans==4.0.0-rc1
requests
pillow
pystyle
colorama
```

#### 3. Configure Bot
Edit `config.json` with your settings:

```json
{
  "token": "YOUR_DISCORD_TOKEN",
  "prefix": ".",
  "voice_token": ["TOKEN1", "TOKEN2"],
  "token_owo": [
    {"CHANNEL_ID_1": "TOKEN_1"},
    {"CHANNEL_ID_2": "TOKEN_2"}
  ],
  "webhooks": {
    "general": "WEBHOOK_URL",
    "owo_farm": "WEBHOOK_URL",
    "owo_bet": "WEBHOOK_URL"
  },
  "ai_config": {
    "gemini_keys": ["KEY1", "KEY2"],
    "gemini_model": "gemini-2.5-flash",
    "chatgpt_keys": ["KEY1", "KEY2"],
    "chatgpt_api_url": "https://ai.seal.io.vn/v1/chat/completions",
    "default_provider": "gemini"
  }
}
```

#### 4. Run Bot
```bash
python main.py
```

---

## 🔧 Cog Management Guide

### Understanding Cogs

**Cogs** are modular components that organize bot commands into categories. Each cog file in the `cogs/` folder contains related commands.

### Project Structure
```
discord-selfbot/
├── main.py                 # Main bot file
├── config.json             # Configuration
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── cogs/                  # Cog modules
│   ├── __init__.py
│   ├── general.py         # Basic commands
│   ├── moderation.py      # Moderation tools
│   ├── owo.py             # OwO automation
│   ├── presence.py        # Status & RPC
│   ├── reactions.py       # Auto reactions
│   ├── utility.py         # Utility commands
│   ├── voice.py           # Voice management
│   ├── afk.py             # AFK status
│   ├── ai_responder.py    # AI integration
│   └── auto_mess.py       # Auto messaging
├── src/                   # Helper modules
│   ├── owofarm.py
│   ├── owobet.py
│   ├── clone.py
│   └── solvecaptcha.py
└── data/                  # Data storage
    ├── songs.json
    ├── rich_presence.json
    ├── afk_status.json
    ├── ai_learning_data.json
    ├── triggers.json
    ├── message_sent.txt
    └── bot_status.json
```

### How to Enable/Disable Cogs

#### Method 1: Edit `main.py` (Recommended)

Open `main.py` and find the `load_cogs()` function (around line 400):

```python
async def load_cogs():
    """Load all cogs from the cogs directory."""
    cogs_dir = "cogs"
    
    # Option A: Load ALL cogs automatically
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = filename[:-3]
            try:
                bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog_name}: {e}")
```

**OR** replace with manual selection:

```python
async def load_cogs():
    """Load specific cogs only."""
    
    # Option B: Load SPECIFIC cogs only
    cogs_to_load = [
        'general',      # ✅ Basic commands (KEEP)
        'moderation',   # ✅ Moderation tools (KEEP)
        'owo',          # ✅ OwO automation (KEEP)
        'presence',     # ✅ Status & RPC (KEEP)
        'reactions',    # ❌ Auto reactions (DISABLE THIS)
        # 'utility',    # ❌ DISABLED - Comment out to disable
        # 'voice',      # ❌ DISABLED
        'afk',          # ✅ AFK status (KEEP)
        'ai_responder', # ✅ AI integration (KEEP)
        'auto_mess',    # ✅ Auto messaging (KEEP)
    ]
    
    for cog_name in cogs_to_load:
        try:
            bot.load_extension(f"cogs.{cog_name}")
            logger.info(f"✅ Loaded cog: {cog_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load cog {cog_name}: {e}")
```

#### Method 2: Runtime Commands (No restart needed)

Use these commands **in Discord** while bot is running:

| Command | Description |
|---------|-------------|
| `.load <cog>` | Load a specific cog |
| `.unload <cog>` | Unload a specific cog |
| `.reload <cog>` | Reload a specific cog |
| `.reload` | Reload ALL cogs |
| `.cogs` | List all loaded cogs |

**Examples:**
```
.load utility
.unload reactions
.reload general
.reload
.cogs
```

### Cog Dependencies Table

| Cog | Required Config | Optional Files | Description |
|-----|----------------|----------------|-------------|
| `general.py` | `token`, `prefix` | None | Basic bot commands |
| `moderation.py` | `token`, `prefix` | None | Server moderation |
| `owo.py` | `token_owo`, `webhooks` | `data/bot_status.json` | OwO bot automation |
| `presence.py` | `token` | `data/songs.json`, `data/rich_presence.json` | Custom status/Spotify/RPC |
| `reactions.py` | `token`, `prefix` | None | Auto emoji reactions |
| `utility.py` | `token`, `prefix` | None | Weather, image gen, server clone |
| `voice.py` | `voice_token` | None | Voice channel management |
| `afk.py` | `token`, `prefix` | `data/afk_status.json` | AFK status system |
| `ai_responder.py` | `ai_config` | `data/ai_learning_data.json` | AI auto-responder |
| `auto_mess.py` | `token`, `prefix` | `data/triggers.json`, `data/message_sent.txt` | Auto keyword responses |

### Creating Your Own Cog

1. Create a new file in `cogs/` folder (e.g., `cogs/mycog.py`)

```python
"""
My Custom Cog
Description of what this cog does.
"""

import discord
from discord.ext import commands

class mycog(commands.Cog):
    """My custom commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='mycommand')
    async def my_command(self, ctx):
        """Usage: {prefix}mycommand"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("Hello from my custom cog!")

def setup(bot):
    """Setup function for cog."""
    bot.add_cog(mycog(bot))
```

2. Load it with `.load mycog` or add `'mycog'` to the cogs list in `main.py`

---

## 📚 Command Categories

### 🔧 General Commands (`general.py`)

| Command | Usage | Description |
|---------|-------|-------------|
| `selfbot` | `.selfbot` | Display bot information (name, ID, uptime, servers) |
| `info` | `.info` | Alias for selfbot command |
| `about` | `.about` | Alias for selfbot command |
| `clear` | `.clear [amount]` | Delete your own messages (default: 10) |
| `purge` | `.purge [amount]` | Alias for clear command |
| `spam` | `.spam <times> <message>` | Send a message multiple times (max: 20) |
| `dm` | `.dm <user> <message>` | Send DM to a user |
| `srvinfo` | `.srvinfo` | Display server information |
| `serverinfo` | `.serverinfo` | Alias for srvinfo |
| `userinfo` | `.userinfo [member]` | Display user information |
| `user_info` | `.user_info [member]` | Alias for userinfo |
| `whois` | `.whois [member]` | Alias for userinfo |

**Examples:**
```
.selfbot
.clear 5
.spam 3 Hello World!
.dm @User#1234 Hey there!
.srvinfo
.userinfo @User#1234
```

---

### 🛡️ Moderation Commands (`moderation.py`)

#### Moderation Actions
| Command | Usage | Description |
|---------|-------|-------------|
| `kick` | `.kick <member> [reason]` | Kick a member from server |
| `ban` | `.ban <member> [reason]` | Ban a member from server |
| `banid` | `.banid <user_id> [reason]` | Ban user by ID |
| `unban` | `.unban <user_id>` | Unban a user |

#### Channel Management
| Command | Usage | Description |
|---------|-------|-------------|
| `hide` | `.hide` | Hide current channel from @everyone |
| `unhide` | `.unhide` | Unhide current channel |
| `nuke` | `.nuke` | Clone and delete current channel |
| `nukesrv` | `.nukesrv` | Nuke entire server (requires confirmation) |
| `create_channel` | `.create_channel <name> [category]` | Create a new text channel |
| `create_role` | `.create_role <name> [hex_color]` | Create a new role |

#### Friend Management
| Command | Usage | Description |
|---------|-------|-------------|
| `massdmfrnds` | `.massdmfrnds <message>` | Send DM to all friends |
| `delallfriends` | `.delallfriends` | Delete all friends (requires confirmation) |
| `leaveallgroups` | `.leaveallgroups` | Leave all group channels |
| `closealldms` | `.closealldms` | Close all DM channels |

**Examples:**
```
.kick @User#1234 Spamming
.ban @User#1234 Breaking rules
.hide
.create_channel general-chat Community
.create_role VIP FF5733
```

---

### 🎮 OwO Bot Automation (`owo.py`)

| Command | Usage | Description |
|---------|-------|-------------|
| `owo` | `.owo <index> <on/off>` | Start/stop OwO farm for specific token |
| `owobet` | `.owobet <index> <on/off>` | Start/stop OwO betting for specific token |
| `owoall` | `.owoall <on/off>` | Start/stop farming for all tokens |
| `owoallsend` | `.owoallsend <text>` | Send message to all OwO channels |
| `status_owo` | `.status_owo [farm/bet]` | Check OwO automation status |

**Configuration Required:**
```json
"token_owo": [
  {"123456789": "MTE..."},
  {"987654321": "MTE..."}
],
"webhooks": {
  "owo_farm": "https://discord.com/api/webhooks/...",
  "owo_bet": "https://discord.com/api/webhooks/..."
}
```

**Examples:**
```
.owo 0 on
.owobet 0 on
.owoall on
.owoallsend owo h
.status_owo farm
```

---

### 🎨 Presence & Status (`presence.py`)

#### Custom Status
| Command | Usage | Description |
|---------|-------|-------------|
| `rotate` | `.rotate <emoji1>,<text1> / <emoji2>,<text2>` | Rotate custom status (5s interval) |
| `stop_rotate` | `.stop_rotate` | Stop status rotation |

#### Spotify Integration
| Command | Usage | Description |
|---------|-------|-------------|
| `rotate_listen` | `.rotate_listen` | Play shuffled Spotify playlist |
| `stop_rotate_listen` | `.stop_rotate_listen` | Stop Spotify mode |

#### Custom Rich Presence
| Command | Usage | Description |
|---------|-------|-------------|
| `custom_rpc` | `.custom_rpc` | Enable custom Rich Presence |
| `stop_custom_rpc` | `.stop_custom_rpc` | Stop custom RPC |

**Required Files:**
- `data/songs.json` - Spotify playlist export
- `data/rich_presence.json` - Custom RPC config

**Examples:**
```
.rotate 😎,Coding / 🔥,Gaming
.rotate <:pepe:123>,Dank / <a:dance:456>,Vibe
.rotate_listen
.custom_rpc
```

**Spotify Config (`data/songs.json`):**
```json
[
  {
    "track": {
      "name": "Song Name",
      "artists": [{"name": "Artist Name"}],
      "album": {
        "name": "Album Name",
        "images": [{"url": "https://i.scdn.co/image/..."}]
      },
      "duration_ms": 180000,
      "id": "spotify_track_id",
      "external_urls": {"spotify": "https://open.spotify.com/track/..."}
    }
  }
]
```

**Custom RPC Config (`data/rich_presence.json`):**
```json
{
  "large_text": ["Title 1", "Title 2", "Title 3"],
  "details": "https://example.com",
  "large_image": "https://i.imgur.com/image.png",
  "duration": 180
}
```

---

### 😀 Auto Reactions (`reactions.py`)

| Command | Usage | Description |
|---------|-------|-------------|
| `auto_react` | `.auto_react <@user/all> <emojis>` | Auto react to user's messages |
| `stop_react` | `.stop_react` | Stop auto reactions |
| `react_status` | `.react_status` | Check reaction status |

**Examples:**
```
.auto_react @User#1234 🔥 💀 😂
.auto_react all ❤️ 👍
.stop_react
.react_status
```

---

### 🛠️ Utility Commands (`utility.py`)

#### Weather
| Command | Usage | Description |
|---------|-------|-------------|
| `weather` | `.weather <city>` | Get weather information |
| `wth` | `.wth <city>` | Alias for weather |

#### Image Generation
| Command | Usage | Description |
|---------|-------|-------------|
| `genimg1` | `.genimg1 <description>` | Generate AI image (Pollinations) |
| `genimg2` | `.genimg2 <keyword>` | Get photo from Unsplash |

#### Checkers
| Command | Usage | Description |
|---------|-------|-------------|
| `checktoken` | `.checktoken <token>` | Verify Discord token validity |
| `checkpromo` | `.checkpromo <code/link>` | Check promo code status |

#### Emoji Management
| Command | Usage | Description |
|---------|-------|-------------|
| `emoji_copy` | `.emoji_copy <source_id> <target_id>` | Copy all emojis between servers |
| `emoji_add` | `.emoji_add <source_id> <target_id> <emoji_id>` | Add specific emoji to server |

#### Server Cloning
| Command | Usage | Description |
|---------|-------|-------------|
| `server_clone` | `.server_clone <source_id> <target_id>` | Full server clone (roles, channels, categories) |
| `csrv` | `.csrv <source_id> <target_id>` | Alias for server_clone |
| `cloneserver` | `.cloneserver <source_id> <target_id>` | Alias for server_clone |
| `quick_clone` | `.quick_clone <source_id> <target_id>` | Quick clone (skip confirmations) |
| `qclone` | `.qclone <source_id> <target_id>` | Alias for quick_clone |

**Examples:**
```
.weather New York
.genimg1 cyberpunk city at night
.checktoken MTE...
.emoji_copy 123456789 987654321
.server_clone 123456789 987654321
```

---

### 🎙️ Voice Management (`voice.py`)

| Command | Usage | Description |
|---------|-------|-------------|
| `joinvoice` | `.joinvoice <channel_id> [token_index]` | Join voice channel with token |
| `leavevoice` | `.leavevoice <token_index>` | Leave voice channel |
| `statusvoice` | `.statusvoice` | Check voice connections status |
| `reloadvoicetokens` | `.reloadvoicetokens` | Reload voice tokens from config |

**Configuration Required:**
```json
"voice_token": [
  "MTE...",
  "MTE...",
  "MTE..."
]
```

**Examples:**
```
.joinvoice 123456789 0
.leavevoice 0
.statusvoice
```

---

### 💤 AFK Status (`afk.py`)

| Command | Usage | Description |
|---------|-------|-------------|
| `afk` | `.afk [reason]` | Set AFK status with optional reason |
| `unafk` | `.unafk` | Remove AFK status |

**Features:**
- Auto-reply when mentioned or DMed
- Auto-remove AFK when you send a message
- Persistent across restarts
- 10-second cooldown per user

**Examples:**
```
.afk I'm sleeping
.afk
.unafk
```

---

### 🤖 AI Auto Responder (`ai_responder.py`)

#### Main Commands
| Command | Usage | Description |
|---------|-------|-------------|
| `auto_ai` | `.auto_ai [on/off] [provider]` | Toggle AI auto-responder |
| `ai_mode` | `.ai_mode [on/off] [provider]` | Alias for auto_ai |
| `ai_provider` | `.ai_provider [gemini/chatgpt]` | Switch AI provider |
| `switch_ai` | `.switch_ai [provider]` | Alias for ai_provider |
| `provider` | `.provider [provider]` | Alias for ai_provider |
| `ask_ai` | `.ask_ai <question>` | Ask AI directly |
| `ai` | `.ai <question>` | Alias for ask_ai |
| `check_keys` | `.check_keys` | Test all API keys |
| `ai_history` | `.ai_history [clear/stats/save]` | Manage conversation history |

**Configuration Required:**
```json
"ai_config": {
  "gemini_keys": ["AIza...", "AIza..."],
  "gemini_model": "gemini-2.5-flash",
  "chatgpt_keys": ["sk-...", "sk-..."],
  "chatgpt_api_url": "https://ai.seal.io.vn/v1/chat/completions",
  "default_provider": "gemini"
}
```

**Features:**
- Multi-key rotation (auto-switch on failure)
- Learning system (saves 200 Q&A)
- Vietnamese personality (bro-style, witty)
- Mirror user's pronouns (mày-tao, bạn-mình)
- Ronaldo & Man United fan mode
- Auto-reply on mention/reply/DM

**Examples:**
```
.auto_ai on gemini
.auto_ai off
.ai_provider chatgpt
.ask_ai What's the weather?
.check_keys
.ai_history stats
.ai_history clear
```

---

### 💬 Auto Messaging (`auto_mess.py`)

#### Auto Response (Keyword Triggers)
| Command | Usage | Description |
|---------|-------|-------------|
| `ar` | `.ar <keyword>, <response>` | Add keyword auto-response |
| `ar_list` | `.ar_list` | List all active auto-responses |

#### Auto Message (Fixed Interval)
| Command | Usage | Description |
|---------|-------|-------------|
| `am` | `.am <seconds> <channel_id> <content>` | Send message at fixed intervals |

#### Auto Mess Random (Smart Messaging)
| Command | Usage | Description |
|---------|-------|-------------|
| `auto_mess` | `.auto_mess <on/off> [mode] [value]` | Smart random messaging |

**Modes:**
- `time` - Send message every X seconds
- `message` - Send after X messages from others

**Required Files:**
- `data/triggers.json` - Stores auto-responses
- `data/message_sent.txt` - Random message pool

**Examples:**
```
.ar hello, Hi there!
.ar_list

.am 60 123456789 Hello every minute!

.auto_mess on time 120
.auto_mess on message 10
.auto_mess off
```

**Message Pool (`data/message_sent.txt`):**
```
Hello from auto message!
Thank you for messaging.
Have a great day.
What's up?
```

---

### ⚙️ Bot Management Commands

#### Reload Commands
| Command | Usage | Description |
|---------|-------|-------------|
| `reload_all` | `.reload_all` | Reload config + RPC + all cogs |
| `rall` | `.rall` | Alias for reload_all |
| `reload` | `.reload [cog]` | Reload all cogs or specific cog |
| `rl` | `.rl [cog]` | Alias for reload |
| `reload_config` | `.reload_config` | Reload config.json |
| `rconfig` | `.rconfig` | Alias for reload_config |
| `rc` | `.rc` | Alias for reload_config |
| `reload_rpc` | `.reload_rpc` | Reload rich_presence.json |
| `rrpc` | `.rrpc` | Alias for reload_rpc |

#### Cog Management
| Command | Usage | Description |
|---------|-------|-------------|
| `load` | `.load <cog>` | Load a specific cog |
| `unload` | `.unload <cog>` | Unload a specific cog |
| `cogs` | `.cogs` | List all loaded cogs |

#### Bot Control
| Command | Usage | Description |
|---------|-------|-------------|
| `help` | `.help [cog]` | Show help menu (with images!) |
| `cmd` | `.cmd [cog]` | Alias for help |
| `h` | `.h [cog]` | Alias for help |
| `ping` | `.ping` | Check bot latency |
| `prefix` | `.prefix <new_prefix>` | Change command prefix |
| `shutdown` | `.shutdown` | Shutdown the bot |
| `stop` | `.stop` | Alias for shutdown |
| `quit` | `.quit` | Alias for shutdown |

**Examples:**
```
.reload_all
.reload general
.reload_config
.load utility
.unload reactions
.cogs
.help
.help general
.ping
.prefix !
.shutdown
```

---

## 📁 Configuration Examples

### Complete `config.json` Template
```json
{
  "token": "YOUR_MAIN_TOKEN_HERE",
  "prefix": ".",
  
  "voice_token": [
    "VOICE_TOKEN_1",
    "VOICE_TOKEN_2",
    "VOICE_TOKEN_3"
  ],
  
  "token_owo": [
    {"CHANNEL_ID_1": "OWO_TOKEN_1"},
    {"CHANNEL_ID_2": "OWO_TOKEN_2"}
  ],
  
  "webhooks": {
    "general": "https://discord.com/api/webhooks/.../...",
    "owo_farm": "https://discord.com/api/webhooks/.../...",
    "owo_bet": "https://discord.com/api/webhooks/.../...."
  },
  
  "ai_config": {
    "gemini_keys": [
      "AIzaSy...",
      "AIzaSy..."
    ],
    "gemini_model": "gemini-2.5-flash",
    "chatgpt_keys": [
      "sk-proj-...",
      "sk-proj-..."
    ],
    "chatgpt_api_url": "https://ai.seal.io.vn/v1/chat/completions",
    "default_provider": "gemini"
  }
}
```

### Required Data Files

**`data/songs.json` (Spotify playlist):**
```json
[
  {
    "track": {
      "name": "Song Name",
      "artists": [{"name": "Artist"}],
      "album": {
        "name": "Album",
        "images": [{"url": "https://i.scdn.co/image/..."}]
      },
      "duration_ms": 210000,
      "id": "track_id",
      "external_urls": {"spotify": "https://open.spotify.com/track/..."}
    }
  }
]
```

**`data/rich_presence.json`:**
```json
{
  "large_text": ["Status 1", "Status 2"],
  "details": "https://yourwebsite.com",
  "large_image": "https://i.imgur.com/image.png",
  "duration": 180
}
```

**`data/message_sent.txt`:**
```
Hello!
How are you?
Have a nice day!
```

---

## 🎓 For New Members

### Quick Start Guide

1. **Install Python 3.12+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH"

2. **Clone & Setup**
   ```bash
   git clone <repo-url>
   cd discord-selfbot
   pip install -r requirements.txt
   ```

3. **Get Your Discord Token**
   - Open Discord in browser (NOT app)
   - Press `F12` to open Developer Tools
   - Go to `Network` tab
   - Type a message in any channel
   - Look for `messages` request
   - Click it, go to `Headers` → `Request Headers`
   - Copy the `authorization` value
   - Paste it in `config.json` as `"token"`

4. **Configure Bot**
   - Edit `config.json`
   - Set your token
   - Choose your prefix (default: `.`)
   - Add any optional configs (AI keys, voice tokens, etc.)

5. **Run Bot**
   ```bash
   python main.py
   ```

6. **Test Commands**
   - In Discord, type `.help`
   - Try `.ping` to check bot works
   - Explore other commands!

### Common Beginner Questions

**Q: Where do I get AI API keys?**
- Gemini: [Google AI Studio](https://aistudio.google.com/)
- ChatGPT: Use compatible API endpoints or OpenAI

**Q: How do I disable cogs I don't need?**
- Method 1: Edit `main.py` and comment out cogs in the load list
- Method 2: Use `.unload <cog>` command in Discord

**Q: Can I use this on multiple accounts?**
- Yes, but you need separate bot instances with different tokens

**Q: Is this against Discord ToS?**
- Yes, selfbots violate Discord's Terms of Service. Use at your own risk.

**Q: My bot isn't responding!**
- Check token is correct
- Verify prefix in config
- Make sure cogs are loaded (`.cogs` command)
- Check console for errors

---

## ⚠️ Important Notes

### Legal & Safety
- **Selfbots violate Discord Terms of Service** - Use at your own risk
- Your account may be banned
- Never share your token
- Use only on accounts you can afford to lose

### Best Practices
- Don't spam commands
- Be respectful to others
- Use webhooks for notifications
- Keep tokens secure
- Regular backups of data folder
- Start with minimal cogs, add as needed

### Performance Tips
- Disable unused cogs
- Limit message history in AI
- Use message mode for auto_mess
- Clear learning data periodically
- Use `.reload` instead of restarting bot

---

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't start:**
```
Error: Token invalid
→ Check token in config.json
→ Ensure no extra spaces
→ Token should start with "MTE" or similar
```

**Commands not working:**
```
Error: Command not found
→ Check prefix (.help)
→ Verify cog is loaded (.cogs)
→ Try .reload
```

**AI not responding:**
```
Error: API key invalid
→ Run .check_keys
→ Verify keys in config.json under ai_config
→ Check provider with .ai_provider
```

**Voice commands fail:**
```
Error: Cannot join voice
→ Check voice_token array
→ Verify token has permissions
→ Check channel ID is correct
```

**Import errors:**
```
Error: ModuleNotFoundError
→ Run: pip install -r requirements.txt
→ Check Python version (3.12+)
→ Try: pip install <missing-module>
```

**Cog won't load:**
```
Error: Extension failed to load
→ Check console for errors
→ Verify config requirements
→ Try .reload <cog>
```

---

## 📝 License

This project is for educational purposes only. Use responsibly.

---

## 🙏 Credits

- discord.py-self library
- Google Gemini API
- OpenAI-compatible APIs
- Community contributors

---

## 📞 Support

If you need help:
1. Check this README first
2. Look at console error messages
3. Try `.help` command in bot
4. Check if your issue is in Troubleshooting section
---

**Version:** 2.0  
**Last Updated:** January 2026  
**Python Version:** 3.12+
