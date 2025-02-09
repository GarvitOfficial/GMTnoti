#!/bin/bash

# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and required packages
sudo apt install -y python3-pip python3-venv git

# Clone the repository
git clone https://github.com/GarvitOfficial/GMTnoti.git
cd GMTnoti/gmtNoti

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service file
sudo tee /etc/systemd/system/gmtbot.service << EOF
[Unit]
Description=GMT Notification Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/GMTnoti/gmtNoti
Environment=PYTHONPATH=/root/GMTnoti/gmtNoti
ExecStart=/root/GMTnoti/gmtNoti/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the service
sudo systemctl daemon-reload
sudo systemctl start gmtbot
sudo systemctl enable gmtbot

echo "Bot has been installed and started as a service!"
