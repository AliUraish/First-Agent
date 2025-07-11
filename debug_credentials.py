import sys
sys.path.append('.')
from app.database import get_db, get_db_type
import json

try:
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT email, credentials FROM users')
        users = cursor.fetchall()
        
        for user in users:
            if hasattr(user, 'keys'):  # PostgreSQL
                email = user['email']
                credentials = user['credentials']
            else:  # SQLite
                email = user[0]
                credentials = user[1]
            
            print(f"User: {email}")
            print("Credentials structure:")
            
            if isinstance(credentials, dict):
                creds_dict = credentials
            else:
                creds_dict = json.loads(credentials)
            
            for key, value in creds_dict.items():
                if key in ['token', 'refresh_token', 'client_secret']:
                    # Mask sensitive values
                    print(f"  {key}: {value[:10]}..." if value else f"  {key}: None")
                else:
                    print(f"  {key}: {value}")
            print()
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 