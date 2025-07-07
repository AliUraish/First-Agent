import sqlite3
from contextlib import contextmanager

DATABASE_URL = "app.db"

def init_db():
    with get_db() as db:
        # Users table for OAuth credentials
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                credentials TEXT
            )
        """)
        
        # User flags table to store flag configurations
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_flags (
                email TEXT,
                flag_name TEXT,
                flag_description TEXT,
                flag_color TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (email, flag_name),
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Flag history table to track changes
        db.execute("""
            CREATE TABLE IF NOT EXISTS flag_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                message_id TEXT,
                flag_name TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        db.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close() 