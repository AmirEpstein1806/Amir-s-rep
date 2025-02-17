from flask import Flask, render_template, request, jsonify
from discord_webhook import DiscordWebhook
import sqlite3
from datetime import datetime, timedelta

app=Flask(__name__)

DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1340645328990507099/5H5MxLGtlLB2EgC-1oSRWDlkq7vdBSiMwMQRWUcN_EqC1ylnlOVeUbgAFX4yPPY61UXJ'

def get_db_connection():
    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_database(text):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Attempting to save:", text, "at", timestamp)  
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO messages (content, timestamp) VALUES (?, ?)', (text, timestamp))
            conn.commit()

        print("Message successfully saved!")  
    except Exception as e:
        print("Database Error:", e)  


def send_to_discord(text):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=text)
    webhook.execute()

@app.route('/input_text', methods=['POST'])
def input_text():
    try:
        data = request.form.get('text')
        if not data or not isinstance(data, str):
            return jsonify({"status": "error", "message": "Invalid input"}), 400

        save_to_database(data)
        send_to_discord(data)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY message_id DESC LIMIT 1")
        latest_message = cursor.fetchone()
        conn.close()

        print("Latest message in DB:", latest_message)

        return jsonify({"status": "success", "message": "Message sent successfully!"})

    except Exception as e:
        print("Error:", e) 
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        cutoff_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT content, timestamp FROM messages WHERE timestamp > ?', (cutoff_time,))
        messages = cursor.fetchall()
        conn.close()

        return jsonify({"status": "success", "messages":[{"content": row['content'], "timestamp": row['timestamp']} for row in messages]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)