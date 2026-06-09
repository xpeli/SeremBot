# SeremBot

Discord bot with ChatGPT-powered conversation, DALL-E 3 image generation,
and switchable personalities.

## Setup

### 1. Create a Discord bot

1. Go to https://discord.com/developers/applications
2. Create a New Application, name it "SeremBot"
3. Go to **Bot** → enable **Message Content Intent** (required for reading messages)
4. Go to **OAuth2** → **URL Generator** → select `bot` + `applications.commands`
   → copy the invite URL and open it in your browser to add the bot to your server
5. Copy the bot token from **Bot** → **Reset Token**

### 2. Set environment variables

```bash
export DISCORD_TOKEN="your-discord-bot-token"
export CHATGPT_TOKEN="your-openai-api-key"
```

Or create a `.env` file:

```
DISCORD_TOKEN=***
CHATGPT_TOKEN=***
```

### 3. Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 serembot.py
```

The bot will sync slash commands on startup and show its current personality
in the Discord status bar.

## Commands

| Command | Description |
|---|---|
| `/ask <prompt>` | Chat with the bot (shared conversation — everyone talks to the same thread) |
| `/image <prompt>` | Generate an image with DALL-E 3 |
| `/personality <name>` | Switch the bot's personality (global, affects everyone) |
| `/reset` | Start a fresh conversation (auto-resets after 20 turns) |
| `/status` | Show current personality and conversation length |
| `/ping` | Check if the bot is alive |

## Personalities

- **Molotov Mickey** — gangster from the Bronx (default)
- **Helpful Assistant** — standard helpful AI
- **Pirate Captain** — arrr, matey
- **Shakespeare** — thee and thou, dramatic metaphors
- **ChatGPT Skeptic** — an AI deeply skeptical of AIs

## Project structure

```
SeremBot/
├── serembot.py               # Bot entry point, slash commands, events
├── ChatGPTCommunicator.py     # OpenAI API wrapper with conversation management
├── BotPersonalities.py        # Personality definitions
├── requirements.txt
├── tests/
│   ├── conftest.py            # Shared fixtures
│   └── test_communicator.py   # 19 tests for the communicator
└── README.md
```

## Logs

Logs are written to `~/.serembot/serembot.log` and stdout.
Images are cached in `~/.serembot/images/` (auto-cleaned when >100 MB).

## Running tests

```bash
source .venv/bin/activate
pytest tests/ -v
```
