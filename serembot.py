import os
from typing import List

import discord
from discord.ext import commands

from BotPersonalities import PersonalityName, personalities
from ChatGPTCommunicator import ChatGPTCommunicator

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
chat_gpt = ChatGPTCommunicator()


@bot.command()
async def ask(ctx, *, prompt: str):
    instructions = personalities.get(PersonalityName.MOLOTOV_MICKEY).value
    response = chat_gpt.send_chat_completion(prompt, instructions)
    await ctx.send(f"{ctx.author.mention}: {response}")


@bot.command()
async def generate_image(ctx, *, prompt: str):
    image_savefile = f"{ctx.author.id}_image.png"
    chat_gpt.generate_image(prompt, image_savefile, "1024x1024")

    with open(image_savefile, "rb") as img_file:
        await ctx.send(f"{ctx.author.mention}: Here's the generated image for '{prompt}':", file=discord.File(img_file))


bot.run(os.environ.get("DISCORD_TOKEN"))
