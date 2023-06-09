import os
import random
from typing import List

import discord
from discord.ext import commands, tasks
import datetime

from BotPersonalities import PersonalityName, personalities
from ChatGPTCommunicator import ChatGPTCommunicator
from SeremCoinWalletManager import SeremCoinWalletManager

# ----------------------------------------------------------#
"""
    * SeremBot
    * Author: xpeli
    * Version: 1.0
    * Description: Discord bot for tracking pooping time
"""
# ----------------------------------------------------------#
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

pooping_users = {}
summary = {}
pooping_prices = {}
wallet_manager = SeremCoinWalletManager()  # Create an instance of SeremCoinWallet

chat_gpt = ChatGPTCommunicator()


# Start pooping command
@bot.command()
async def start_pooping(ctx):
    user_id = ctx.author.id
    if user_id not in pooping_users:
        pooping_users[user_id] = datetime.datetime.now()
        wallet_manager.create_wallet(user_id, ctx.author.name)  # Create a wallet for the user if it doesn't exist
        await ctx.send(f"{ctx.author.mention} started pooping.")
    else:
        await ctx.send(f"{ctx.author.mention} you're already pooping!")


# Stop pooping command
@bot.command()
async def stop_pooping(ctx):
    user_id = ctx.author.id
    if user_id in pooping_users:
        start_time = pooping_users[user_id]
        duration = datetime.datetime.now() - start_time
        duration_in_minutes = duration.total_seconds() / 60

        if user_id not in summary:
            summary[user_id] = 0

        summary[user_id] += duration_in_minutes

        if user_id not in pooping_prices:
            pooping_prices[user_id] = 0

        pooping_prices[user_id] += (duration.total_seconds() / 3600) * 300
        seremcoins_to_add = (duration.total_seconds() / 3600) * 10  # Calculate SeremCoins to add based on duration
        wallet_manager.add_seremcoins(user_id, seremcoins_to_add)  # Add SeremCoins to the user's wallet
        del pooping_users[user_id]

        await ctx.send(
            f"{ctx.author.mention} stopped pooping. Total duration: {duration_in_minutes:.2f} minutes. Earned SeremCoins: {seremcoins_to_add:.2f}.")
    else:
        await ctx.send(f"{ctx.author.mention} you're not currently pooping!")


# Check for users who forgot to stop pooping
@tasks.loop(minutes=1)
async def check_pooping_users():
    current_time = datetime.datetime.now()
    for user_id, start_time in pooping_users.copy().items():
        duration = current_time - start_time
        if duration.total_seconds() >= 3600:  # 1 hour in seconds
            summary[user_id] += 20
            pooping_prices[user_id] += (20 / 60) * 250
            del pooping_users[user_id]


@bot.command()
async def poop_summary(ctx):
    summary_message = "Poop Summary:\n"
    total_duration = 0
    total_cost = 0

    for user_id, duration in summary.items():
        user = await bot.fetch_user(user_id)
        price = pooping_prices[user_id]
        seremcoins = wallet_manager.get_balance(user_id)
        total_duration += duration
        total_cost += price
        summary_message += f"{user.name}: {duration:.2f} minutes, {price:.2f} CZK, {seremcoins:.2f} SeremCoins\n"

    summary_message += f"\nTotal duration for all users: {total_duration:.2f} minutes"
    summary_message += f"\nTotal cost for all users: {total_cost:.2f} CZK"

    await ctx.send(summary_message)

@bot.command()
async def ask(ctx, *, prompt: str):
    messages = [
        {"role": "system", "content": personalities.get(PersonalityName.MOLOTOV_MICKEY).value}
    ]
    async for message in ctx.channel.history(limit=20):
        role = "user"
        if message.author.name == "SeremBot":
            role = "assistant"

        messages.append(
            {
                "role": role,
                "content": message.content
            }
        )

    messages.append({"role": "user", "content": prompt})

    response = chat_gpt.send_chat_prompt(messages)
    await ctx.send(f"{ctx.author.mention}: {response}")

@bot.command()
async def cicina(ctx):
    length = random.randint(0, 30)
    if(length <= 5):
        await ctx.send(f"{ctx.author.mention}, horšie to už byť nemôže: {length}cm. Nechcel by som nehehehe")
    elif(5 < length <= 10):
        await ctx.send(f"{ctx.author.mention}, máš fess malú cicinu: {length}cm. S týmto veľa nezrobiš xdddd")
    elif(10 < length <= 15):
        await ctx.send(f"{ctx.author.mention}, Zavárané uharky sú väčšie: {length}cm. Snaha bola, ale nevyšlo to")
    elif(15 < length <= 20):
        await ctx.send(f"{ctx.author.mention}, Je to pohodička: {length}cm. Mr Pohodička")
    elif(20 < length <= 25):
        await ctx.send(f"{ctx.author.mention}, To jak paprikáš saláma: {length}cm. Saláma je dobrá")
    elif(25 < length <= 30):
        await ctx.send(f"{ctx.author.mention}, To je jak sústruh: {length}cm. Drátenka would be proud")
    


@bot.command()
async def generate_image(ctx, *, prompt: str):
    image_savefile = f"{ctx.author.id}_image.png"
    chat_gpt.generate_image(prompt, image_savefile, "1024x1024")

    with open(image_savefile, "rb") as img_file:
        await ctx.send(f"{ctx.author.mention}: Here's the generated image for '{prompt}':", file=discord.File(img_file))


@bot.command()
async def seremcoin_balance(ctx):
    user_id = ctx.author.id
    balance = wallet_manager.get_balance(user_id)
    if balance is not None:
        await ctx.send(f"{ctx.author.mention}, your SeremCoin balance is: {balance:.2f} SeremCoins.")
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have a SeremCoin wallet yet. Start pooping to create one!")

# Start the check_pooping_users task
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="github.com/xpeli/SeremBot"))
    check_pooping_users.start()


def _available_emojis_chatgpt_message() -> str:
    return "Emojis available to you: " + _available_emojis().__str__()

def _available_emojis() -> List[str]:
    emojis = []
    for emoji in bot.emojis:
        emojis.append(emoji.__str__())

    return emojis


bot.run(os.environ.get("DISCORD_TOKEN"))
