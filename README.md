# GMT Notification System 🔔

A Telegram-based notification system with a web interface for managing academic reminders. Built with Python, Flask, and SQLite.

## Features ✨

- **Telegram Bot Integration**: Instant notifications via Telegram
- **Web Dashboard**: Easy-to-use interface for managing reminders
- **Category-based Notifications**: Support for different academic levels (BS, BSC, Foundation, Diploma)
- **Secure Authentication**: Protected web interface with username/password
- **Database Management**: SQLite for reliable data storage
- **Timezone Aware**: All times in GMT/IST for accuracy

## Tech Stack 🛠

- **Backend**: Python, Flask
- **Database**: SQLite3
- **Bot Framework**: python-telegram-bot
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: DigitalOcean

## Setup Guide 🚀

1. **Clone the Repository**
   ```bash
   git clone https://github.com/GarvitOfficial/GMTnoti.git
   cd GMTnoti
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Create `config/.env` file with:
     ```
     TELEGRAM_TOKEN=your_telegram_bot_token
     WEB_USERNAME=your_web_username
     WEB_PASSWORD=your_web_password
     ```

5. **Initialize Database**
   ```bash
   mkdir -p data
   ```
   - Database will be automatically created on first run

6. **Run the Application**
   ```bash
   # Start the Telegram bot
   python bot.py
   
   # Start the web server
   python web_server.py
   ```

## Usage Guide 📖

### Telegram Bot Commands
- `/start` - Register with the bot
- `/help` - Show available commands
- `/category` - Set your notification category

### Web Interface
- Access the dashboard at `http://your-server:5002`
- Login with your configured credentials
- Add, view, and manage reminders
- Filter reminders by category

## Security Notes 🔒

- Keep your `.env` file secure and never commit it
- Change default credentials immediately
- Use strong passwords
- Keep your system and dependencies updated

## Contributing 🤝

This is a proprietary project. While the code is visible for educational purposes, modifications and redistributions are not permitted without explicit permission.

## License ⚖️

Copyright (c) 2025 Garvit. All Rights Reserved.

This project and its source code are protected under copyright law. No permission is granted for:
- Commercial use
- Modification
- Distribution
- Private use without permission

For any usage permissions, please contact the author.

## Author ✍️

**Garvit**
- GitHub: [@GarvitOfficial](https://github.com/GarvitOfficial)

## Acknowledgments 🙏

- Thanks to the Python community
- Telegram Bot API team
- Flask framework developers
