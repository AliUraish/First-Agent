import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
from pathlib import Path
import sys
from dotenv import load_dotenv
import os

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from app.config import get_settings

def get_sqlite_connection():
    """Connect to SQLite database"""
    return sqlite3.connect(Path(__file__).parent.parent / "app" / "app.db")

def get_postgres_connection():
    """Connect to Supabase PostgreSQL database"""
    settings = get_settings()
    if not settings.supabase_db_url:
        raise ValueError("Supabase database URL not configured!")
    return psycopg2.connect(settings.supabase_db_url)

def create_tables(pg_conn):
    """Create tables in Supabase"""
    with pg_conn.cursor() as cur:
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                credentials JSONB
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
        
        pg_conn.commit()

def migrate_table(sqlite_cur, pg_conn, table_name, columns):
    """Migrate data from SQLite table to PostgreSQL"""
    print(f"Migrating {table_name}...")
    
    # Get data from SQLite
    sqlite_cur.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cur.fetchall()
    
    if not rows:
        print(f"No data found in {table_name}")
        return
    
    # Insert into PostgreSQL
    with pg_conn.cursor() as pg_cur:
        columns_str = ', '.join(columns)
        values_template = ', '.join(['%s'] * len(columns))
        query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({values_template})
            ON CONFLICT DO NOTHING
        """
        execute_values(pg_cur, query, rows)
    
    pg_conn.commit()
    print(f"Migrated {len(rows)} rows from {table_name}")

def main():
    """Main migration function"""
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent / "details.env")
    
    try:
        # Connect to both databases
        sqlite_conn = get_sqlite_connection()
        pg_conn = get_postgres_connection()
        
        # Create tables in Supabase
        create_tables(pg_conn)
        
        # Get SQLite cursor
        sqlite_cur = sqlite_conn.cursor()
        
        # Define table structures
        tables = {
            'users': ['email', 'credentials'],
            'user_flags': ['email', 'flag_name', 'flag_description', 'flag_color', 'is_active', 'created_at', 'updated_at'],
            'flag_history': ['email', 'message_id', 'flag_name', 'action', 'timestamp'],
            'gmail_labels': ['email', 'label_name', 'label_id', 'label_color', 'created_at', 'updated_at', 'is_active'],
            'sorting_sessions': ['email', 'session_id', 'start_time', 'end_time', 'status', 'total_emails', 'processed_emails', 'error_message', 'flags_used'],
            'email_processing_log': ['session_id', 'email_id', 'email_subject', 'email_from', 'assigned_label', 'confidence_score', 'processing_time', 'status', 'error_details']
        }
        
        # Migrate each table
        for table_name, columns in tables.items():
            migrate_table(sqlite_cur, pg_conn, table_name, columns)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise
    
    finally:
        # Close connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main() 