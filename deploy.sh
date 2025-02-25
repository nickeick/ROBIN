#!/bin/bash
cd /home/pi/discord-bot

# Activate Python environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart the bot
sudo systemctl restart discord-bot.service
