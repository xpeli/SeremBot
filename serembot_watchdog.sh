#!/usr/bin/env bash
# SeremBot watchdog — restart if the bot process is not running.
# Runs every 5 minutes via cron (no_agent, script-only mode).
set -euo pipefail

SEREMBOT_DIR="/home/thinksmart/Projects/SeremBot"
cd "$SEREMBOT_DIR"

# Check if serembot.py is already running
if pgrep -f "serembot\.py" > /dev/null 2>&1; then
    # Bot is running — nothing to do
    exit 0
fi

# Bot is down — restart it
echo "SeremBot down at $(date -Iseconds) — restarting..."
source .venv/bin/activate
nohup .venv/bin/python -u serembot.py >> /home/thinksmart/.serembot/serembot.log 2>&1 &
echo "SeremBot restarted with PID $!"
