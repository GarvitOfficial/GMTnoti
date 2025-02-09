from flask import Flask, render_template, jsonify, request, Response
import sqlite3
import os
from datetime import datetime
import pytz
from functools import wraps
from dotenv import load_dotenv

app = Flask(__name__)
# Change DATABASE_PATH to match bot.py
DATABASE_PATH = 'data/reminders.db'

# Load environment variables
load_dotenv('config/.env')

# Check if required environment variables are set
if not os.getenv('WEB_USERNAME') or not os.getenv('WEB_PASSWORD'):
    raise ValueError("WEB_USERNAME and WEB_PASSWORD must be set in config/.env")

# Set up the IST time zone
IST = pytz.timezone('Asia/Kolkata')

# Create database directory if it doesn't exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

def init_db():
    """Initialize database with required tables"""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            category TEXT CHECK(category IN ('foundation', 'diploma', 'bsc', 'bs')),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create reminders table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            date TEXT NOT NULL,
            message TEXT NOT NULL,
            categories TEXT NOT NULL DEFAULT 'all',
            last_sent TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()
    db.close()

# Initialize database on startup
init_db()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = dict_factory
    return db

def check_auth(username, password):
    """Check if username and password match the ones in .env file"""
    correct_username = os.getenv('WEB_USERNAME')
    correct_password = os.getenv('WEB_PASSWORD')
    return username == correct_username and password == correct_password

def authenticate():
    """Send 401 response that enables basic auth"""
    return Response(
        'Authentication required.\n',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

@app.route('/api/reminders', methods=['GET'])
@requires_auth
def get_reminders():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, time, date, message, categories
        FROM reminders 
        ORDER BY 
            date, 
            CAST(substr(time, 1, 2) AS INTEGER) * 60 + CAST(substr(time, 4, 2) AS INTEGER)
    ''')
    reminders = cursor.fetchall()
    db.close()
    return jsonify(reminders)

@app.route('/api/reminders', methods=['POST'])
@requires_auth
def add_reminder():
    try:
        data = request.json
        
        if not all(key in data for key in ['date', 'time', 'message', 'categories']):
            print(f"Missing fields in data: {data}")
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            # Validate date and time format
            datetime.strptime(f"{data['date']} {data['time']}", '%d/%m/%Y %H:%M')
            
            # Validate categories
            categories = data['categories'].split(',')
            valid_categories = {'all', 'foundation', 'diploma', 'bsc', 'bs'}
            if not all(cat.strip() in valid_categories for cat in categories):
                print(f"Invalid categories: {categories}")
                return jsonify({'error': 'Invalid categories'}), 400
                
        except ValueError as e:
            print(f"Date/time validation error: {str(e)}")
            return jsonify({'error': 'Invalid date or time format'}), 400

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                'INSERT INTO reminders (date, time, message, categories) VALUES (?, ?, ?, ?)',
                (data['date'], data['time'], data['message'], data['categories'])
            )
            db.commit()
            print(f"Successfully added reminder: {data}")
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            db.close()
        
        return jsonify({'message': 'Reminder added successfully'}), 201
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@requires_auth
def delete_reminder(reminder_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    db.commit()
    db.close()
    return '', 204

@app.route('/api/stats', methods=['GET'])
@requires_auth
def get_stats():
    db = get_db()
    cursor = db.cursor()
    
    # Get counts by category
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM users 
        GROUP BY category
    ''')
    user_stats = cursor.fetchall()
    
    # Get total reminders
    cursor.execute('SELECT COUNT(*) as count FROM reminders')
    reminder_count = cursor.fetchone()['count']
    
    db.close()
    
    return jsonify({
        'user_stats': user_stats,
        'total_reminders': reminder_count
    })

if __name__ == '__main__':
    # For production deployment
    app.run(host='0.0.0.0', port=5002, debug=False)
else:
    # For Vercel deployment
    app = app
