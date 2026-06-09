"""SeremBot — Discord bot with ChatGPT-powered conversation and image generation.

Slash commands:
  /ask <prompt>         — talk to the bot (shared conversation)
  /image <prompt>       — generate an image with DALL-E 3
  /personality <name>   — switch the bot's personality (global)
  /reset                — start a fresh conversation
  /status               — show current personality and conversation length
  /ping                 — check if the bot is alive
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import discord
from discord import app_commands
from discord.ext import commands

from BotPersonalities import PersonalityName, personalities
from ChatGPTCommunicator import ChatGPTCommunicator

# ── Ensure data directory exists ───────────────────────────────────────────────
Path.home().joinpath(".serembot").mkdir(exist_ok=True)
Path.home().joinpath(".serembot", "images").mkdir(exist_ok=True)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path.home() / ".serembot" / "serembot.log"),
    ],
)
log = logging.getLogger("serembot")

# ── Token validation ─────────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    log.critical(
        "DISCORD_TOKEN not set.  Export it in your shell or add it to .env:\n"
        "  export DISCORD_TOKEN='your-token-here'"
    )
    sys.exit(1)

# ── Bot setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
chat_gpt = ChatGPTCommunicator()

# Current personality (global — shared by all users in the server)
_current_personality: PersonalityName = PersonalityName.MOLOTOV_MICKEY


def _get_instructions() -> str:
    return personalities[_current_personality]


# ── Events ───────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info("SeremBot online as %s", bot.user)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"/ask | {_current_personality.value}",
        )
    )
    await bot.tree.sync()
    log.info("Slash commands synced — personality: %s", _current_personality.value)


# ── Slash commands ───────────────────────────────────────────────────────────

@bot.tree.command(name="ask", description="Ask the bot anything")
@app_commands.describe(prompt="Your question or message")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    log.info("/ask from %s: %s", interaction.user, prompt[:80])

    try:
        instructions = _get_instructions()
        response = chat_gpt.send_chat_completion(prompt, instructions)
        # Public conversation: show the question + answer so everyone can follow
        name = interaction.user.display_name
        await interaction.followup.send(f"**{name}:** {prompt}\n\n{response}")
    except Exception as e:
        log.exception("/ask failed")
        await interaction.followup.send(
            f"❌ Something broke: {e}. Try again."
        )


@bot.tree.command(name="image", description="Generate an image with DALL-E 3")
@app_commands.describe(prompt="Describe the image you want")
async def image(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    log.info("/image from %s: %s", interaction.user, prompt[:80])

    image_path = str(
        Path.home() / ".serembot" / "images" / f"{interaction.user.id}_image.png"
    )
    try:
        chat_gpt.generate_image(prompt, image_path)
        await interaction.followup.send(
            f"{interaction.user.mention}: Here's your image for *{prompt}*:",
            file=discord.File(image_path),
        )
    except RuntimeError as e:
        await interaction.followup.send(
            f"{interaction.user.mention}: ❌ {e}"
        )
    except Exception as e:
        log.exception("/image failed")
        await interaction.followup.send(
            f"❌ Image generation failed: {e}"
        )


@bot.tree.command(
    name="personality", description="Switch the bot's personality (global)"
)
@app_commands.describe(name="Which personality to use")
@app_commands.choices(
    name=[
        app_commands.Choice(name=p.value, value=p.name)
        for p in PersonalityName
    ]
)
async def personality(interaction: discord.Interaction, name: str):
    global _current_personality
    try:
        new_personality = PersonalityName[name]
    except KeyError:
        await interaction.response.send_message(
            f"Unknown personality: {name}. Available: "
            + ", ".join(p.value for p in PersonalityName),
            ephemeral=True,
        )
        return

    _current_personality = new_personality
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"/ask | {_current_personality.value}",
        )
    )
    await interaction.response.send_message(
        f"🎭 Personality switched to **{_current_personality.value}** "
        f"(global — affects everyone)"
    )
    log.info("Personality changed to %s by %s", _current_personality.value, interaction.user)


@bot.tree.command(name="reset", description="Start a fresh conversation")
async def reset(interaction: discord.Interaction):
    chat_gpt.reset_conversation()
    await interaction.response.send_message(
        "🔄 Conversation reset! Fresh start."
    )
    log.info("Conversation reset by %s", interaction.user)


@bot.tree.command(name="status", description="Show bot status")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🎭 **Personality:** {_current_personality.value}\n"
        f"💬 **Conversation turns:** {chat_gpt.turn_count} "
        f"(auto-reset at 20)\n"
        f"🖼️ **Model:** gpt-4o-mini / gpt-image-1"
    )


@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! ({round(bot.latency * 1000)}ms)"
    )


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
