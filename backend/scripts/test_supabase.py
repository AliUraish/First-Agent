import psycopg2
from pathlib import Path
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from app.config import get_settings

def get_postgres_connection():
    """Connect to Supabase PostgreSQL database"""
    settings = get_settings()
    if not settings.supabase_db_url:
        raise ValueError("Supabase database URL not configured!")
    return psycopg2.connect(settings.supabase_db_url)

def run_test_queries(conn):
    """Run test queries on all tables"""
    with conn.cursor() as cur:
        # Test 1: Insert test user
        print("\nTest 1: Inserting test user...")
        test_credentials = {"test": "credentials"}
        cur.execute(
            "INSERT INTO users (email, credentials) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING",
            ("test@example.com", json.dumps(test_credentials))
        )
        
        # Test 2: Insert test flag
        print("\nTest 2: Inserting test flag...")
        cur.execute("""
            INSERT INTO user_flags (email, flag_name, flag_description, flag_color, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email, flag_name) DO NOTHING
        """, ("test@example.com", "Test Flag", "Test Description", "#FF0000", True))
        
        # Test 3: Insert test flag history
        print("\nTest 3: Inserting test flag history...")
        cur.execute("""
            INSERT INTO flag_history (email, message_id, flag_name, action)
            VALUES (%s, %s, %s, %s)
        """, ("test@example.com", "test_message_123", "Test Flag", "created"))
        
        # Test 4: Insert test Gmail label
        print("\nTest 4: Inserting test Gmail label...")
        cur.execute("""
            INSERT INTO gmail_labels (email, label_name, label_id, label_color)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email, label_name) DO NOTHING
        """, ("test@example.com", "Test Label", "Label_123", "#00FF00"))
        
        # Test 5: Insert test sorting session
        print("\nTest 5: Inserting test sorting session...")
        cur.execute("""
            INSERT INTO sorting_sessions 
            (email, session_id, status, total_emails, processed_emails, flags_used)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
        """, ("test@example.com", "session_123", "completed", 10, 10, "Test Flag"))
        
        # Test 6: Insert test processing log
        print("\nTest 6: Inserting test processing log...")
        cur.execute("""
            INSERT INTO email_processing_log 
            (session_id, email_id, email_subject, email_from, assigned_label, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("session_123", "email_123", "Test Subject", "sender@test.com", "Test Label", 0.95))
        
        # Commit the changes
        conn.commit()
        
        # Test 7: Query all tables
        print("\nTest 7: Querying all tables...")
        
        tables = ['users', 'user_flags', 'flag_history', 'gmail_labels', 
                 'sorting_sessions', 'email_processing_log']
        
        for table in tables:
            print(f"\nQuerying {table}:")
            cur.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cur.fetchall()
            print(f"Found {len(rows)} rows")
            if rows:
                print("Sample row:", rows[0])

def cleanup_test_data(conn):
    """Clean up test data"""
    print("\nCleaning up test data...")
    with conn.cursor() as cur:
        # Delete in reverse order of dependencies
        cur.execute("DELETE FROM email_processing_log WHERE session_id = 'session_123'")
        cur.execute("DELETE FROM sorting_sessions WHERE session_id = 'session_123'")
        cur.execute("DELETE FROM gmail_labels WHERE email = 'test@example.com'")
        cur.execute("DELETE FROM flag_history WHERE email = 'test@example.com'")
        cur.execute("DELETE FROM user_flags WHERE email = 'test@example.com'")
        cur.execute("DELETE FROM users WHERE email = 'test@example.com'")
        conn.commit()

def main():
    """Main test function"""
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent / "details.env")
    
    try:
        # Connect to Supabase
        print("Connecting to Supabase...")
        conn = get_postgres_connection()
        
        # Run test queries
        run_test_queries(conn)
        
        # Clean up test data
        cleanup_test_data(conn)
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise
    
    finally:
        # Close connection
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 