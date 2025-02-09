#!/bin/bash

# Function to prompt for credentials if not provided
setup_credentials() {
    if [ -z "$WEB_USERNAME" ]; then
        read -p "Enter username for web interface (default: admin): " WEB_USERNAME
        WEB_USERNAME=${WEB_USERNAME:-admin}
    fi

    if [ -z "$WEB_PASSWORD" ]; then
        read -s -p "Enter password for web interface (or press enter to generate): " WEB_PASSWORD
        echo
        if [ -z "$WEB_PASSWORD" ]; then
            WEB_PASSWORD=$(openssl rand -base64 12)
            echo "Generated password: $WEB_PASSWORD"
        fi
    fi

    if [ -z "$TELEGRAM_TOKEN" ]; then
        read -s -p "Enter your Telegram bot token: " TELEGRAM_TOKEN
        echo
    fi
}

# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and required packages
sudo apt install -y python3-pip python3-venv git

# Get credentials
setup_credentials

# Clone the repository
git clone https://github.com/GarvitOfficial/GMTnoti.git
cd GMTnoti

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all required packages
pip install python-telegram-bot==20.7
pip install python-dotenv==1.0.0
pip install pytz==2023.3
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1

# Create config directory and env file
mkdir -p config
cat > config/.env << EOF
TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
WEB_USERNAME=${WEB_USERNAME}
WEB_PASSWORD=${WEB_PASSWORD}
EOF

# Secure the .env file
chmod 600 config/.env

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

# Create systemd service file for the web server
sudo tee /etc/systemd/system/gmtweb.service << EOF
[Unit]
Description=GMT Notification Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/GMTnoti
Environment=PYTHONPATH=/root/GMTnoti
ExecStart=/root/GMTnoti/venv/bin/python web_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable both services
sudo systemctl daemon-reload
sudo systemctl start gmtbot gmtweb
sudo systemctl enable gmtbot gmtweb

# Open port 5002 for web access
sudo apt install -y ufw
sudo ufw allow 5002/tcp
sudo ufw --force enable

echo "Bot and Web Server have been installed and started as services!"
echo "Access the web interface at http://YOUR_DROPLET_IP:5002"
echo "Web interface credentials:"
echo "Username: ${WEB_USERNAME}"
echo "Password: ${WEB_PASSWORD}"
echo "SAVE THESE CREDENTIALS SOMEWHERE SAFE!"
