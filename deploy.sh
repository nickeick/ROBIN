#!/bin/bash
cd /home/pi/app

# Activate Python environment and install dependencies
source /home/pi/app/venv/bin/activate
pip install -r requirements.txt

# Restart the bot
sudo systemctl restart discord-bot.service
