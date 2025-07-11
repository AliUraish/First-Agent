import sys
sys.path.append('.')
from app.database import get_db, get_db_type
from app.routers.email_sorting import get_user_by_email
import asyncio

try:
    print(f"Database type: {get_db_type()}")
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT email, credentials FROM users')
        users = cursor.fetchall()
        print(f'Found {len(users)} users in database:')
        
        user_emails = []
        for user in users:
            if hasattr(user, 'keys'):  # Dictionary-like object (PostgreSQL)
                email = user['email']
                has_creds = bool(user['credentials'])
            else:  # Tuple-like object (SQLite)
                email = user[0]
                has_creds = bool(user[1])
            
            print(f'- Email: {email}')
            print(f'- Has credentials: {has_creds}')
            user_emails.append(email)
            print()
        
        # Test get_user_by_email function
        if user_emails:
            print(f"Testing get_user_by_email with: {user_emails[0]}")
            user_obj = asyncio.run(get_user_by_email(user_emails[0]))
            if user_obj:
                print(f"✓ Successfully retrieved user: {user_obj.email}")
            else:
                print("✗ Failed to retrieve user")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 