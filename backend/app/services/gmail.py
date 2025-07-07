from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import base64
from typing import Optional, Tuple, Dict, List
import json

from ..config import get_settings
from ..models.database import User

settings = get_settings()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/userinfo.email'
]

class GmailService:
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

    def create_authorization_url(self) -> Tuple[str, str]:
        """Create Gmail OAuth URL"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return auth_url, state

    def get_token_from_code(self, code: str) -> Dict:
        """Exchange auth code for tokens"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": (datetime.utcnow() + 
                           timedelta(seconds=credentials.expiry.timestamp()))
        }

    def build_service(self, user: User):
        """Build Gmail API service"""
        try:
            credentials = Credentials(
                token=user.access_token,
                refresh_token=user.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                scopes=SCOPES
            )
            return build('gmail', 'v1', credentials=credentials)
        except Exception:
            return None

    async def get_user_email(self, service) -> Optional[str]:
        """Get user's email address"""
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception:
            return None

    async def get_labels(self, service) -> List[Dict]:
        """Get all Gmail labels"""
        try:
            results = service.users().labels().list(userId='me').execute()
            return results.get('labels', [])
        except Exception:
            return []

    async def create_label(self, service, name: str) -> Optional[Dict]:
        """Create a new Gmail label"""
        try:
            label_object = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            return service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
        except Exception:
            return None

    async def apply_label(self, service, message_id: str, label_id: str) -> bool:
        """Apply label to an email"""
        try:
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            return True
        except Exception:
            return False

    async def remove_label(self, service, message_id: str, label_id: str) -> bool:
        """Remove label from an email"""
        try:
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': [label_id]}
            ).execute()
            return True
        except Exception:
            return False

    async def search_messages(
        self, 
        service, 
        query: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """Search Gmail messages"""
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            detailed_messages = []
            
            for msg in messages:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = message['payload']['headers']
                subject = next(
                    (h['value'] for h in headers if h['name'] == 'Subject'),
                    'No Subject'
                )
                sender = next(
                    (h['value'] for h in headers if h['name'] == 'From'),
                    'Unknown'
                )
                date = next(
                    (h['value'] for h in headers if h['name'] == 'Date'),
                    'Unknown'
                )
                
                detailed_messages.append({
                    'id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'labelIds': message.get('labelIds', [])
                })
                
            return detailed_messages
        except Exception:
            return []

    async def archive_message(self, service, message_id: str) -> bool:
        """Archive a message (remove INBOX label)"""
        try:
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception:
            return False 