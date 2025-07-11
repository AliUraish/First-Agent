from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from typing import Optional
from ..database import get_db, get_db_type
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Load client secrets from the downloaded OAuth 2.0 credentials
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

@router.get("/login")
async def login():
    """Initiates the Gmail OAuth2 flow"""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/auth/callback"
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        return RedirectResponse(authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def callback(request: Request):
    """Handles the OAuth2 callback from Gmail"""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/auth/callback"
        )
        
        # Get authorization code from URL
        code = request.query_params.get("code")
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Validate that we have a refresh token
        if not credentials.refresh_token:
            raise HTTPException(
                status_code=400,
                detail="No refresh token received. Please try authenticating again."
            )
        
        # Get user email
        email = get_user_email(credentials)
        
        # Store credentials in database
        user = User(email=email, credentials=credentials_to_dict(credentials))
        
        try:
            with get_db() as db:
                cursor = db.cursor()
                
                if get_db_type() == "postgres":
                    # PostgreSQL syntax
                    cursor.execute(
                        "INSERT INTO users (email, credentials) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET credentials = EXCLUDED.credentials",
                        (user.email, json.dumps(user.credentials))
                    )
                else:
                    # SQLite syntax
                    cursor.execute(
                        "INSERT OR REPLACE INTO users (email, credentials) VALUES (?, ?)",
                        (user.email, json.dumps(user.credentials))
                    )
                db.commit()
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save credentials. Please try again."
            )
        
        # Verify the data was saved
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
            else:
                cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
            saved_user = cursor.fetchone()
            
            if not saved_user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to verify saved credentials. Please try again."
                )
        
        # Redirect to frontend with success parameter
        return RedirectResponse("http://localhost:8080?auth=success")
    except Exception as e:
        error_message = str(e)
        print(f"Auth callback error: {error_message}")
        # Redirect to frontend with error parameter
        return RedirectResponse(f"http://localhost:8080?error={error_message}")

@router.get("/status")
async def get_status():
    """Check if user is connected to Gmail"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("SELECT email, credentials FROM users LIMIT 1")
            user = cursor.fetchone()
            
            if user and user['credentials']:
                return {
                    "is_connected": True,
                    "email": user['email']
                }
            return {"is_connected": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout():
    """Disconnect from Gmail but preserve user data"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            # Only remove credentials but keep the user record and their flag configurations
            cursor.execute("""
                UPDATE users 
                SET credentials = NULL 
                WHERE credentials IS NOT NULL
            """)
            db.commit()
        return {"message": "Successfully disconnected while preserving your settings"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset():
    """Clear all user data including flags and history"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            # Delete all user data
            cursor.execute("DELETE FROM flag_history")
            cursor.execute("DELETE FROM user_flags")
            cursor.execute("DELETE FROM users")
            db.commit()
        return {"message": "Successfully cleared all data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-credentials")
async def clear_credentials():
    """Clear invalid credentials to allow re-authentication"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("UPDATE users SET credentials = NULL WHERE credentials IS NOT NULL")
            else:
                cursor.execute("UPDATE users SET credentials = NULL WHERE credentials IS NOT NULL")
            db.commit()
        return {"message": "Credentials cleared. Please authenticate again."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def credentials_to_dict(credentials: Credentials) -> dict:
    """Convert credentials to dictionary for storage"""
    from ..config import get_settings
    settings = get_settings()
    
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri or "https://oauth2.googleapis.com/token",
        'client_id': credentials.client_id or settings.google_client_id,
        'client_secret': credentials.client_secret or settings.google_client_secret,
        'scopes': credentials.scopes or SCOPES
    }

def get_user_email(credentials: Credentials) -> str:
    """Get user's email from Gmail API"""
    try:
        service = build('gmail', 'v1', credentials=credentials)
        user_info = service.users().getProfile(userId='me').execute()
        return user_info['emailAddress']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user email: {str(e)}") 