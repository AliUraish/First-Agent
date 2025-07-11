import psycopg2
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from app.config import get_settings

def get_postgres_connection():
    """Connect to Supabase PostgreSQL database"""
    settings = get_settings()
    if not settings.supabase_db_url:
        raise ValueError("Supabase database URL not configured!")
    return psycopg2.connect(settings.supabase_db_url)

def create_tables(pg_conn):
    """Create tables in Supabase"""
    with pg_conn.cursor() as cur:
        print("Creating tables in Supabase...")
        
        # Users table
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                credentials JSONB
            )
        """)
        
        # User flags table
        print("Creating user_flags table...")
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
        print("Creating flag_history table...")
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
        print("Creating gmail_labels table...")
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
        print("Creating sorting_sessions table...")
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
        print("Creating email_processing_log table...")
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
        print("All tables created successfully!")

def main():
    """Main setup function"""
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent / "details.env")
    
    try:
        # Connect to Supabase
        print("Connecting to Supabase...")
        pg_conn = get_postgres_connection()
        
        # Create tables
        create_tables(pg_conn)
        
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        raise
    
    finally:
        # Close connection
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main() 