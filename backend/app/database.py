import sqlite3
from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from .config import get_settings

settings = get_settings()

def get_db_type():
    """Determine which database to use based on configuration"""
    return "postgres" if settings.supabase_db_url else "sqlite"

@contextmanager
def get_db():
    """Database connection context manager"""
    if get_db_type() == "postgres":
        conn = psycopg2.connect(
            settings.supabase_db_url,
            cursor_factory=RealDictCursor
        )
    else:
        conn = sqlite3.connect("app.db")
        conn.row_factory = sqlite3.Row
    
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        cur = conn.cursor()
        
        # Users table for OAuth credentials
        if get_db_type() == "postgres":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    credentials JSONB
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    credentials TEXT
                )
            """)
        
        # User flags table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_flags (
                email TEXT,
                flag_name TEXT,
                flag_description TEXT,
                flag_color TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (email, flag_name),
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Flag history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flag_history (
                id SERIAL PRIMARY KEY,
                email TEXT,
                message_id TEXT,
                flag_name TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Gmail labels table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gmail_labels (
                id SERIAL PRIMARY KEY,
                email TEXT,
                label_name TEXT,
                label_id TEXT,
                label_color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(email, label_name),
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Sorting sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sorting_sessions (
                id SERIAL PRIMARY KEY,
                email TEXT,
                session_id TEXT UNIQUE,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'running',
                total_emails INTEGER DEFAULT 0,
                processed_emails INTEGER DEFAULT 0,
                error_message TEXT,
                flags_used TEXT,
                FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Email processing log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_processing_log (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                email_id TEXT,
                email_subject TEXT,
                email_from TEXT,
                assigned_label TEXT,
                confidence_score REAL,
                processing_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                error_details TEXT,
                FOREIGN KEY (session_id) REFERENCES sorting_sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit() 