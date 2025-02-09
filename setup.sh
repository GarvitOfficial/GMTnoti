#!/bin/bash

# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and required packages
sudo apt install -y python3-pip python3-venv git

# Clone the repository
git clone https://github.com/GarvitOfficial/GMTnoti.git
cd GMTnoti

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages for the bot
pip install python-telegram-bot==20.7
pip install python-dotenv==1.0.0
pip install pytz==2023.3

# Create config directory and env file
mkdir -p config
echo "TELEGRAM_TOKEN=${TELEGRAM_TOKEN}" > config/.env

# Create systemd service file for the bot
sudo tee /etc/systemd/system/gmtbot.service << EOF
[Unit]
Description=GMT Notification Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/GMTnoti
Environment=PYTHONPATH=/root/GMTnoti
ExecStart=/root/GMTnoti/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the bot service
sudo systemctl daemon-reload
sudo systemctl start gmtbot
sudo systemctl enable gmtbot

echo "Bot has been installed and started as a service!"
