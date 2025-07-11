import sys
sys.path.append('.')
import asyncio
from app.database import get_db, get_db_type

async def test_user_flags():
    try:
        email = "66prototype27@gmail.com"
        print(f"🔍 Checking user flags for: {email}")
        
        with get_db() as db:
            cursor = db.cursor()
            
            # Check if user_flags table exists
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_flags'
                    )
                """)
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='user_flags'
                """)
            
            table_exists = cursor.fetchone()
            print(f"📋 user_flags table exists: {bool(table_exists)}")
            
            if table_exists:
                # Check flags for this user
                if get_db_type() == "postgres":
                    cursor.execute("""
                        SELECT flag_name, flag_color, description, created_at
                        FROM user_flags 
                        WHERE email = %s
                    """, (email,))
                else:
                    cursor.execute("""
                        SELECT flag_name, flag_color, description, created_at
                        FROM user_flags 
                        WHERE email = ?
                    """, (email,))
                
                flags = cursor.fetchall()
                print(f"📧 Found {len(flags)} flags for user:")
                for flag in flags:
                    print(f"   - {flag[0]} (color: {flag[1]}) - {flag[2]}")
                
                if len(flags) == 0:
                    print("⚠️  No flags configured for this user!")
                    print("💡 This explains the error - trying to query flags that don't exist")
                    
                    # Create some default flags
                    print("\n🔧 Creating default flags...")
                    default_flags = [
                        ("Urgent", "#ef4444", "High priority emails requiring immediate attention"),
                        ("Important", "#f97316", "Important business emails"),
                        ("Follow-up", "#eab308", "Emails requiring follow-up")
                    ]
                    
                    for flag_name, flag_color, description in default_flags:
                        if get_db_type() == "postgres":
                            cursor.execute("""
                                INSERT INTO user_flags (email, flag_name, flag_color, description)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (email, flag_name) DO NOTHING
                            """, (email, flag_name, flag_color, description))
                        else:
                            cursor.execute("""
                                INSERT OR IGNORE INTO user_flags (email, flag_name, flag_color, description)
                                VALUES (?, ?, ?, ?)
                            """, (email, flag_name, flag_color, description))
                    
                    db.commit()
                    print("✅ Created default flags")
            else:
                print("❌ user_flags table doesn't exist - need to create database schema")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_flags()) 