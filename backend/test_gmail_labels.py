import sys
sys.path.append('.')
import asyncio
from app.routers.email_sorting import get_user_by_email
from app.services.gmail import GmailService

async def test_gmail_labels():
    try:
        # Get user
        email = "66prototype27@gmail.com"
        user = await get_user_by_email(email)
        
        # Test Gmail service
        gmail_service = GmailService()
        service = gmail_service.build_service(user)
        
        # Get all labels
        existing_labels = await gmail_service.get_labels(service)
        print(f"📋 Found {len(existing_labels)} existing labels in Gmail:")
        
        # Separate system vs user labels
        system_labels = []
        user_labels = []
        
        for label in existing_labels:
            label_name = label.get('name', 'No name')
            label_id = label.get('id', 'No ID')
            
            if label_id.startswith('CATEGORY_') or label_id in ['INBOX', 'SENT', 'TRASH', 'DRAFT', 'SPAM', 'IMPORTANT', 'STARRED', 'UNREAD', 'CHAT']:
                system_labels.append((label_name, label_id))
            else:
                user_labels.append((label_name, label_id))
        
        print(f"\n🔧 System Labels ({len(system_labels)}):")
        for name, label_id in system_labels:
            print(f"   {name} (ID: {label_id})")
        
        print(f"\n👤 User Labels ({len(user_labels)}):")
        for name, label_id in user_labels:
            print(f"   {name} (ID: {label_id})")
        
        # Test creating a label with different name
        print(f"\n🏷️  Testing alternative label creation...")
        test_names = ["Business", "Work Important", "High Priority"]
        
        for test_name in test_names:
            print(f"\nTrying to create: '{test_name}'")
            try:
                result = await gmail_service.create_label(service, test_name)
                if result:
                    print(f"✅ Successfully created '{test_name}' with ID: {result['id']}")
                else:
                    print(f"❌ Failed to create '{test_name}'")
            except Exception as e:
                print(f"❌ Error creating '{test_name}': {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gmail_labels()) 