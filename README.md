# SeremBot
Poop Tracker is a simple Discord bot that allows users to track their "pooping" time and calculates the cost of each session based on a given rate. The bot also provides a summary of each user's total pooping time and cost.


## Features

- Start and stop pooping commands (`!start_pooping` and `!stop_pooping`)
- Automatic 20-minute pooping session if the user forgets to stop pooping after 1 hour
- Poop summary command (`!poop_summary`) that shows the total pooping time and cost for each user

## Installation and Setup

1. Clone this repository or download the source code.
2. Install the required Python packages using the following command: ```pip install discord.py```
3. Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications) and obtain its token.
4. Replace `YOUR_TOKEN` in the `bot.py` file with the bot token you obtained from the Discord Developer Portal.
5. Invite the bot to your Discord server using the instructions provided in the [Discord Developer Portal](https://discord.com/developers/applications).
6. Run the `bot.py` file to start the bot: ```python bot.py```

## Usage

- Start pooping: `!start_pooping`
- Stop pooping: `!stop_pooping`
- Show poop summary: `!poop_summary`

## Notes

This bot is a simple example and can be improved upon, for instance, by storing data persistently or implementing better error handling.

The bot must be hosted on a server or platform to run 24/7. Free options like Replit may cause the bot to go to sleep after a period of inactivity, potentially affecting the automatic 1-hour check feature. Consider using a paid hosting solution or running the bot on a personal computer or server that's always on for a more reliable experience.
