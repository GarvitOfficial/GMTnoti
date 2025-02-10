import logging
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
import asyncio
import pytz
from dotenv import load_dotenv
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables from the new location
load_dotenv('config/.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("No token found in environment variables")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set up the IST time zone
IST = pytz.timezone('Asia/Kolkata')

# Valid categories
VALID_CATEGORIES = {'foundation', 'diploma', 'bsc', 'bs'}

class Database:
    def __init__(self, db_path: str = 'data/reminders.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Initialize database with proper schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Check if database exists
        db_exists = os.path.exists(self.db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if not db_exists:
                logger.info("Creating new database with initial schema")
            else:
                logger.info("Checking and updating existing database schema")
                
            # Get existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Create or update users table
            if 'users' not in existing_tables:
                logger.info("Creating users table")
                cursor.execute('''
                    CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        category TEXT CHECK(category IN ('foundation', 'diploma', 'bsc', 'bs')),
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Create or update reminders table
            if 'reminders' not in existing_tables:
                logger.info("Creating reminders table")
                cursor.execute('''
                    CREATE TABLE reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT NOT NULL,
                        date TEXT NOT NULL,
                        message TEXT NOT NULL,
                        categories TEXT NOT NULL DEFAULT 'all',
                        last_sent TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # Check if categories column exists in reminders table
                cursor.execute("PRAGMA table_info(reminders)")
                columns = {row[1] for row in cursor.fetchall()}
                
                if 'categories' not in columns:
                    logger.info("Adding categories column to reminders table")
                    cursor.execute('ALTER TABLE reminders ADD COLUMN categories TEXT NOT NULL DEFAULT "all"')
                
                if 'last_sent' not in columns:
                    logger.info("Adding last_sent column to reminders table")
                    cursor.execute('ALTER TABLE reminders ADD COLUMN last_sent TIMESTAMP')
            
            conn.commit()
            logger.info("Database initialization completed successfully")

    def add_user(self, user_id: int, username: Optional[str], category: str) -> None:
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO users (user_id, username, category) VALUES (?, ?, ?)',
                (user_id, username, category.lower())
            )
            conn.commit()

    def get_user_category(self, user_id: int) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT category FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def remove_user(self, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()

    def get_all_users(self) -> List[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username FROM users')
            return cursor.fetchall()

    def get_users_by_categories(self, categories: List[str]) -> List[tuple]:
        categories = [cat.strip().lower() for cat in categories]
        if 'all' in categories:
            return self.get_all_users()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(categories))
            cursor.execute(
                f'SELECT user_id, username FROM users WHERE category IN ({placeholders})',
                categories
            )
            return cursor.fetchall()

    def get_all_reminders(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, time, date, message, categories, last_sent
                FROM reminders
                ORDER BY 
                    date,
                    CAST(substr(time, 1, 2) AS INTEGER) * 60 + CAST(substr(time, 4, 2) AS INTEGER)
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def update_reminder_sent(self, reminder_id: int, sent_time: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE reminders SET last_sent = ? WHERE id = ?',
                (sent_time, reminder_id)
            )
            conn.commit()

# Initialize database
db = Database()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler - Show available commands and usage"""
    help_text = (
        "🤖 *Reminder Bot Help*\n\n"
        "*Available Commands*\n"
        "/start - Start the bot and select your category\n"
        "/help - Show this help message\n"
        "/stop - Unsubscribe from reminders\n"
        "/support - Show ways to support us\n\n"
        "*Category Commands*\n"
        "/foundation - Register as Foundation student\n"
        "/diploma - Register as Diploma student\n"
        "/bsc - Register as BSc student\n"
        "/bs - Register as BS student\n\n"
        "*How to Use*\n"
        "1. Use /start to begin\n"
        "2. Select your category using one of the category commands\n"
        "3. You'll receive reminders based on your category\n"
        "4. Use /stop if you want to unsubscribe\n\n"
        "*Note:* You can change your category anytime by using a different category command."
    )
    
    try:
        await update.message.reply_text(help_text, parse_mode='Markdown')
        logger.info(f"Help message sent to user {update.message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending help message: {str(e)}", exc_info=True)

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Support command handler - Show donation information"""
    support_text = (
        "💖 *Support Reminder Bot*\n\n"
        "If you find this bot helpful, consider supporting us:\n\n"
        "*Ethereum (ETH)*\n"
        "`0x6119fCB96Ef440b9ACfCC7DE998cdD05BCf052C5`\n\n"
        "*Bitcoin (BTC)*\n"
        "`bc1qpfahyaqtkwpx73ww094wjzs9urh2e24s3l8kq`\n\n"
        "*Ripple (XRP)*\n"
        "`rJn5xUrXewGkdohG8sy8MftTtzuKK4Gp23`\n\n"
        "Thank you for your support! 🙏"
    )
    
    try:
        await update.message.reply_text(support_text, parse_mode='Markdown')
        logger.info(f"Support message sent to user {update.message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending support message: {str(e)}", exc_info=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler - Add user to the database"""
    try:
        user = update.message.from_user
        logger.debug(f"Start command received from user {user.id} ({user.username})")
        
        current_category = db.get_user_category(user.id)
        logger.debug(f"Current category for user {user.id}: {current_category}")
        
        if current_category:
            message = (
                f"👋 Welcome back! You're registered as a *{current_category.upper()}* student.\n\n"
                "*Available Commands*\n"
                "Change your category:\n"
                "/foundation - Foundation student\n"
                "/diploma - Diploma student\n"
                "/bsc - BSc student\n"
                "/bs - BS student\n\n"
                "/help - Show all commands\n"
                "/stop - Unsubscribe from reminders\n"
                "/support - Show ways to support us"
            )
        else:
            # Add user with default category 'bs'
            db.add_user(user.id, user.username, 'bs')
            logger.info(f"Added new user {user.id} ({user.username}) with default category 'bs'")
            
            message = (
                "👋 Welcome to the *Reminder Bot*! 🎉\n\n"
                "You've been registered with default category *BS*.\n\n"
                "*Change your category*\n"
                "/foundation - Foundation student\n"
                "/diploma - Diploma student\n"
                "/bsc - BSc student\n"
                "/bs - BS student\n\n"
                "*Other Commands*\n"
                "/help - Show all commands\n"
                "/stop - Unsubscribe from reminders\n"
                "/support - Show ways to support us"
            )
        
        logger.debug(f"Attempting to send message to user {user.id}")
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Welcome message sent to user {user.id}")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again later.")

async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user category handler"""
    try:
        user = update.message.from_user
        category = update.message.text[1:]  # Remove the '/' from command
        logger.debug(f"Set category command received: {category} from user {user.id} ({user.username})")
        
        try:
            logger.debug(f"Attempting to add user {user.id} with category {category}")
            db.add_user(user.id, user.username, category)
            message = (
                f"✅ You've been registered as a *{category.upper()}* student!\n\n"
                "You will receive reminders for your category.\n\n"
                "*Available Commands*\n"
                "/help - Show all commands\n"
                "/stop - Unsubscribe from reminders\n"
                "/support - Show ways to support us"
            )
            logger.info(f"Category {category} set successfully for user {user.id}")
        except ValueError as e:
            logger.error(f"Invalid category attempt from user {user.id}: {str(e)}")
            message = (
                "❌ Invalid category. Please use one of these commands:\n\n"
                "/foundation - Foundation student\n"
                "/diploma - Diploma student\n"
                "/bsc - BSc student\n"
                "/bs - BS student"
            )
        
        logger.debug(f"Attempting to send message to user {user.id}")
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Message sent successfully to user {user.id}")
    except Exception as e:
        logger.error(f"Error in set_category command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again later.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop command handler - Remove user from the database"""
    try:
        user = update.message.from_user
        logger.info(f"Stop command received from user {user.id} ({user.username})")
        
        # Get user's category before removing
        current_category = db.get_user_category(user.id)
        db.remove_user(user.id)
        
        message = (
            "👋 You've been unsubscribed from reminders.\n\n"
            f"Your previous category was: *{current_category.upper() if current_category else 'None'}*\n\n"
            "*Want to come back?*\n"
            "• Use `/start` to subscribe again\n"
            "• Use `/help` to see all commands"
        )
        
        logger.debug(f"Attempting to send message to user {user.id}")
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"User {user.id} successfully unsubscribed")
    except Exception as e:
        logger.error(f"Error in stop command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again later.")

async def broadcast_reminders(application: Application) -> None:
    """Main loop to handle broadcasting reminders"""
    while True:
        try:
            now = datetime.now(IST)
            reminders = db.get_all_reminders()
            
            for reminder in reminders:
                try:
                    reminder_time = datetime.strptime(f"{reminder['date']} {reminder['time']}", '%d/%m/%Y %H:%M')
                    reminder_time = IST.localize(reminder_time)
                    
                    # Check if reminder hasn't been sent in the last minute
                    last_sent = reminder.get('last_sent')
                    if last_sent:
                        last_sent = datetime.fromisoformat(last_sent)
                        if (now - last_sent).total_seconds() < 60:
                            continue

                    time_diff = (reminder_time - now).total_seconds()
                    if 0 <= time_diff <= 10:
                        # Get target categories
                        categories = [cat.strip() for cat in reminder['categories'].split(',')]
                        users = db.get_users_by_categories(categories)
                        
                        for user_id, username in users:
                            try:
                                message = (
                                    "⏰ *Reminder!*\n\n"
                                    f"{reminder['message']}\n\n"
                                    "_To stop receiving reminders, use /stop_"
                                )
                                await application.bot.send_message(
                                    chat_id=user_id,
                                    text=message,
                                    parse_mode='Markdown'
                                )
                                logger.info(f"Sent reminder to {username} (ID: {user_id})")
                            except Exception as e:
                                logger.error(f"Failed to send reminder to {user_id}: {str(e)}")
                        
                        # Update last_sent time
                        db.update_reminder_sent(reminder['id'], now.isoformat())
                
                except ValueError as e:
                    logger.error(f"Error parsing reminder time: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in broadcast loop: {str(e)}")
        
        await asyncio.sleep(10)

def main() -> None:
    """Main function to run the bot"""
    try:
        logger.info("Starting the bot...")
        logger.info(f"Using token: {TOKEN[:4]}...{TOKEN[-4:]}")
        
        # Build application with proper defaults
        application = (
            Application.builder()
            .token(TOKEN)
            .concurrent_updates(True)
            .arbitrary_callback_data(True)
            .build()
        )
        logger.info("Application built successfully")

        # Add handlers
        logger.info("Adding command handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stop", stop))
        application.add_handler(CommandHandler("support", support_command))
        
        # Add category handlers
        for category in VALID_CATEGORIES:
            application.add_handler(CommandHandler(category, set_category))
            logger.info(f"Added handler for /{category} command")

        logger.info("All handlers added successfully")

        # Start the broadcast loop in the background
        logger.info("Starting broadcast loop...")
        application.job_queue.run_once(broadcast_reminders, 0, application)
        logger.info("Broadcast loop started")

        # Start the bot with specific allowed updates
        logger.info("Starting polling...")
        application.run_polling(
            allowed_updates=[Update.MESSAGE],
            drop_pending_updates=True,
            pool_timeout=10.0
        )

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
