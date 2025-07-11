from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import base64
from typing import Optional, Tuple, Dict, List
import json
import uuid

from ..config import get_settings
from ..models import User
from ..database import get_db
from ..database import get_db_type

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
            # Extract credentials from the user's credentials dict
            creds_dict = user.credentials
            
            # Ensure all required fields are present
            token = creds_dict.get('token')
            refresh_token = creds_dict.get('refresh_token')
            token_uri = creds_dict.get('token_uri', "https://oauth2.googleapis.com/token")
            client_id = creds_dict.get('client_id', settings.google_client_id)
            client_secret = creds_dict.get('client_secret', settings.google_client_secret)
            scopes = creds_dict.get('scopes', SCOPES)
            
            if not token:
                print("Error: No access token in credentials")
                return None
                
            if not refresh_token:
                print("Error: No refresh token in credentials")
                return None
                
            if not client_id or not client_secret:
                print("Error: Missing client_id or client_secret")
                return None
            
            credentials = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri=token_uri,
                client_id=client_id,
                client_secret=client_secret,
                scopes=scopes
            )
            
            return build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            import traceback
            traceback.print_exc()
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

    def resolve_label_name_conflict(self, label_name: str) -> str:
        """Resolve conflicts with Gmail system labels by using safe alternatives"""
        # Gmail system labels that might conflict
        gmail_system_labels = {
            'Important': 'Important Emails',
            'IMPORTANT': 'Important Emails', 
            'Spam': 'Spam Emails',
            'SPAM': 'Spam Emails',
            'Inbox': 'Inbox Emails',
            'INBOX': 'Inbox Emails',
            'Sent': 'Sent Emails',
            'SENT': 'Sent Emails',
            'Draft': 'Draft Emails',
            'DRAFT': 'Draft Emails',
            'Trash': 'Trash Emails',
            'TRASH': 'Trash Emails'
        }
        
        return gmail_system_labels.get(label_name, label_name)

    async def create_label(self, service, name: str, color: str = None) -> Optional[Dict]:
        """Create a new Gmail label"""
        try:
            # Resolve any potential name conflicts with Gmail system labels
            safe_name = self.resolve_label_name_conflict(name)
            
            label_object = {
                'name': safe_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            # Don't set custom colors for now - Gmail has specific palette requirements
            # if color:
            #     label_object['color'] = {
            #         'backgroundColor': color,
            #         'textColor': '#ffffff'
            #     }
            result = service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            print(f"Successfully created label: {safe_name} with ID: {result.get('id')}")
            return result
        except Exception as e:
            print(f"Failed to create label '{name}': {e}")
            return None

    async def get_or_create_label(self, service, email: str, label_name: str, label_color: str = None) -> Optional[str]:
        """Get existing label or create new one, sync with database"""
        try:
            # Resolve label name conflicts first
            safe_label_name = self.resolve_label_name_conflict(label_name)
            
            # First check existing labels
            existing_labels = await self.get_labels(service)
            # Check for both original and safe names
            existing_label = next(
                (label for label in existing_labels 
                 if label['name'] == label_name or label['name'] == safe_label_name), 
                None
            )
            
            if existing_label:
                # Update database with existing label info
                await self.sync_label_to_db(email, label_name, existing_label['id'], label_color or '#000000')
                print(f"Found existing label '{existing_label['name']}' for flag '{label_name}'")
                return existing_label['id']
            
            # Create new label with safe name
            new_label = await self.create_label(service, safe_label_name)
            if new_label:
                # Add to database with original flag name
                await self.sync_label_to_db(email, label_name, new_label['id'], label_color or '#000000')
                print(f"Created label '{safe_label_name}' for flag '{label_name}'")
                return new_label['id']
            
            return None
        except Exception as e:
            print(f"Error in get_or_create_label: {e}")
            return None

    async def sync_label_to_db(self, email: str, label_name: str, label_id: str, label_color: str):
        """Sync label information to database"""
        try:
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        INSERT INTO gmail_labels 
                        (email, label_name, label_id, label_color, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (email, label_name) 
                        DO UPDATE SET 
                            label_id = EXCLUDED.label_id,
                            label_color = EXCLUDED.label_color,
                            updated_at = CURRENT_TIMESTAMP
                    """, (email, label_name, label_id, label_color))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO gmail_labels 
                        (email, label_name, label_id, label_color, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (email, label_name, label_id, label_color))
                db.commit()
        except Exception as e:
            print(f"Error syncing label to database: {e}")

    async def update_label(self, service, label_id: str, new_name: str) -> bool:
        """Update Gmail label name"""
        try:
            label_object = {
                'name': new_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            service.users().labels().update(
                userId='me',
                id=label_id,
                body=label_object
            ).execute()
            print(f"Successfully updated label ID {label_id} to name: {new_name}")
            return True
        except Exception as e:
            print(f"Failed to update label '{label_id}' to '{new_name}': {e}")
            return False

    async def sync_label_changes(self, service, email: str, current_flag_names: List[str]) -> Dict[str, str]:
        """Sync label changes when user flag names are updated"""
        try:
            # Get current Gmail labels
            existing_labels = await self.get_labels(service)
            existing_label_dict = {label['name']: label['id'] for label in existing_labels}
            
            # Get stored label mappings from database
            stored_labels = {}
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        SELECT label_name, label_id 
                        FROM gmail_labels 
                        WHERE email = %s
                    """, (email,))
                else:
                    cursor.execute("""
                        SELECT label_name, label_id 
                        FROM gmail_labels 
                        WHERE email = ?
                    """, (email,))
                for row in cursor.fetchall():
                    stored_labels[row[0]] = row[1]
            
            # Check for label name changes
            updated_mapping = {}
            
            # Get current user flags from database with old and new names
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        SELECT flag_name, flag_color 
                        FROM user_flags 
                        WHERE email = %s AND is_active = true
                    """, (email,))
                else:
                    cursor.execute("""
                        SELECT flag_name, flag_color 
                        FROM user_flags 
                        WHERE email = ? AND is_active = 1
                    """, (email,))
                current_db_flags = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Handle label updates and creations
            for flag_name in current_flag_names:
                if flag_name in existing_label_dict:
                    # Label exists with same name - just update mapping
                    updated_mapping[flag_name] = existing_label_dict[flag_name]
                    await self.sync_label_to_db(email, flag_name, existing_label_dict[flag_name], 
                                              current_db_flags.get(flag_name, '#000000'))
                else:
                    # Check if this is a renamed label by looking for orphaned labels
                    orphaned_labels = []
                    for stored_name, stored_id in stored_labels.items():
                        if stored_name not in current_flag_names and stored_id in [l['id'] for l in existing_labels]:
                            orphaned_labels.append((stored_name, stored_id))
                    
                    if orphaned_labels:
                        # Rename the first orphaned label to the new flag name
                        old_name, label_id = orphaned_labels[0]
                        success = await self.update_label(service, label_id, flag_name)
                        if success:
                            updated_mapping[flag_name] = label_id
                            # Update database record
                            await self.sync_label_to_db(email, flag_name, label_id, 
                                                      current_db_flags.get(flag_name, '#000000'))
                            # Remove old database record
                            with get_db() as db:
                                cursor = db.cursor()
                                if get_db_type() == "postgres":
                                    cursor.execute("DELETE FROM gmail_labels WHERE email = %s AND label_name = %s", 
                                                 (email, old_name))
                                else:
                                    cursor.execute("DELETE FROM gmail_labels WHERE email = ? AND label_name = ?", 
                                                 (email, old_name))
                                db.commit()
                            print(f"Renamed label '{old_name}' to '{flag_name}'")
                        else:
                            # If rename failed, create new label
                            label_id = await self.get_or_create_label(service, email, flag_name, 
                                                                    current_db_flags.get(flag_name))
                            if label_id:
                                updated_mapping[flag_name] = label_id
                    else:
                        # Create new label
                        label_id = await self.get_or_create_label(service, email, flag_name, 
                                                                current_db_flags.get(flag_name))
                        if label_id:
                            updated_mapping[flag_name] = label_id
            
            # Clean up unused labels in database (optional - keep labels in Gmail but remove from our tracking)
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        DELETE FROM gmail_labels 
                        WHERE email = %s AND label_name NOT IN ({})
                    """.format(','.join(['%s'] * len(current_flag_names))), 
                    [email] + current_flag_names)
                else:
                    cursor.execute("""
                        DELETE FROM gmail_labels 
                        WHERE email = ? AND label_name NOT IN ({})
                    """.format(','.join(['?'] * len(current_flag_names))), 
                    [email] + current_flag_names)
                db.commit()
            
            return updated_mapping
            
        except Exception as e:
            print(f"Error syncing label changes: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def verify_labels_exist(self, service, email: str, flag_names: List[str]) -> Dict[str, str]:
        """Verify all labels exist, create missing ones, handle updates, return label_name -> label_id mapping"""
        label_mapping = {}
        
        try:
            print(f"Verifying labels for flags: {flag_names}")
            
            # First, sync any label changes (renames, etc.)
            label_mapping = await self.sync_label_changes(service, email, flag_names)
            
            # Then ensure all current flags have labels
            existing_labels = await self.get_labels(service)
            existing_label_names = {label['name']: label['id'] for label in existing_labels}
            print(f"Found {len(existing_labels)} existing labels in Gmail")
            
            # Get flag colors from database if any flags exist
            flag_colors = {}
            if flag_names:  # Only query if we have flag names
                try:
                    with get_db() as db:
                        cursor = db.cursor()
                        if get_db_type() == "postgres":
                            placeholders = ','.join(['%s'] * len(flag_names))
                            cursor.execute(f"""
                                SELECT flag_name, flag_color 
                                FROM user_flags 
                                WHERE email = %s AND flag_name IN ({placeholders})
                            """, [email] + flag_names)
                        else:
                            placeholders = ','.join(['?'] * len(flag_names))
                            cursor.execute(f"""
                                SELECT flag_name, flag_color 
                                FROM user_flags 
                                WHERE email = ? AND flag_name IN ({placeholders})
                            """, [email] + flag_names)
                        flag_colors = {row[0]: row[1] for row in cursor.fetchall()}
                        print(f"Found colors for {len(flag_colors)} flags in database")
                except Exception as db_error:
                    print(f"Warning: Could not get flag colors from database: {db_error}")
                    # Continue without colors
            
            # Check for any missing labels and create them
            for flag_name in flag_names:
                if flag_name not in label_mapping:
                    # Check for both original and safe label names
                    safe_label_name = self.resolve_label_name_conflict(flag_name)
                    
                    if flag_name in existing_label_names:
                        # Original label name exists
                        label_id = existing_label_names[flag_name]
                        label_mapping[flag_name] = label_id
                        print(f"Found existing label '{flag_name}' with ID: {label_id}")
                        await self.sync_label_to_db(email, flag_name, label_id, flag_colors.get(flag_name, '#000000'))
                    elif safe_label_name in existing_label_names:
                        # Safe label name exists (conflict resolution was already applied)
                        label_id = existing_label_names[safe_label_name]
                        label_mapping[flag_name] = label_id
                        print(f"Found existing safe label '{safe_label_name}' for flag '{flag_name}' with ID: {label_id}")
                        await self.sync_label_to_db(email, flag_name, label_id, flag_colors.get(flag_name, '#000000'))
                    else:
                        # Create new label with conflict resolution
                        print(f"Creating new label for flag '{flag_name}' (safe name: '{safe_label_name}')")
                        label_id = await self.get_or_create_label(service, email, flag_name, flag_colors.get(flag_name))
                        if label_id:
                            label_mapping[flag_name] = label_id
                            print(f"Successfully created label for '{flag_name}' with ID: {label_id}")
                        else:
                            print(f"Failed to create label for flag: {flag_name}")
            
            print(f"Final label mapping: {label_mapping}")
            return label_mapping
        except Exception as e:
            print(f"Error in verify_labels_exist: {e}")
            import traceback
            traceback.print_exc()
            return {}

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

    async def get_recent_emails(self, service, max_results: int = 50) -> List[Dict]:
        """Get recent emails with full content for categorization"""
        try:
            # Get list of messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='in:inbox -in:trash -in:spam'  # Only inbox emails, exclude trash and spam
            ).execute()
            
            messages = results.get('messages', [])
            email_data = []
            
            for message in messages:
                try:
                    # Get full message details
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = msg.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # Extract body content
                    body = self._extract_email_body(msg.get('payload', {}))
                    
                    email_data.append({
                        'id': message['id'],
                        'subject': subject,
                        'from': sender,
                        'date': date,
                        'body': body[:1000] if body else '',  # Limit body to 1000 chars
                        'snippet': msg.get('snippet', ''),
                        'threadId': msg.get('threadId', '')
                    })
                    
                except Exception as e:
                    print(f"Error processing message {message['id']}: {e}")
                    continue
            
            print(f"Successfully retrieved {len(email_data)} emails")
            return email_data
            
        except Exception as e:
            print(f"Error getting recent emails: {e}")
            return []

    def _extract_email_body(self, payload: Dict) -> str:
        """Extract text content from email payload"""
        try:
            body = ""
            
            # Check if payload has parts (multipart message)
            if 'parts' in payload:
                for part in payload['parts']:
                    body += self._extract_email_body(part)
            else:
                # Single part message
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        # Decode base64
                        decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
                        body += decoded
                elif payload.get('mimeType') == 'text/html':
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        # Decode base64 and strip HTML tags
                        decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
                        # Simple HTML tag removal
                        import re
                        body += re.sub(r'<[^>]+>', '', decoded)
            
            return body.strip()
            
        except Exception as e:
            print(f"Error extracting email body: {e}")
            return ""

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