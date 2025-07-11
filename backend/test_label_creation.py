import sys
sys.path.append('.')
import asyncio
from app.routers.email_sorting import get_user_by_email
from app.services.gmail import GmailService

async def test_label_creation():
    try:
        # Get user
        email = "66prototype27@gmail.com"
        print(f"🔍 Testing label creation for: {email}")
        user = await get_user_by_email(email)
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✅ User found: {user.email}")
        
        # Test Gmail service
        gmail_service = GmailService()
        print("🔧 Building Gmail service...")
        service = gmail_service.build_service(user)
        
        if not service:
            print("❌ Failed to build Gmail service")
            return
        
        print("✅ Gmail service built successfully")
        
        # Test getting existing labels
        print("📋 Getting existing labels...")
        existing_labels = await gmail_service.get_labels(service)
        print(f"📋 Found {len(existing_labels)} existing labels:")
        for label in existing_labels[:10]:  # Show first 10
            print(f"   - {label.get('name', 'No name')} (ID: {label.get('id', 'No ID')})")
        
        # Test creating a test label
        test_label_name = "Test Urgent Flag"
        print(f"\n🏷️  Testing label creation: {test_label_name}")
        
        # Check if label already exists
        existing_test_label = next((label for label in existing_labels if label['name'] == test_label_name), None)
        if existing_test_label:
            print(f"⚠️  Label '{test_label_name}' already exists with ID: {existing_test_label['id']}")
        else:
            # Create the label without color
            new_label = await gmail_service.create_label(service, test_label_name)
            if new_label:
                print(f"✅ Successfully created label '{test_label_name}' with ID: {new_label['id']}")
            else:
                print(f"❌ Failed to create label '{test_label_name}'")
        
        # Test get_or_create_label function
        print(f"\n🔄 Testing get_or_create_label for 'Urgent'...")
        label_id = await gmail_service.get_or_create_label(service, email, "Urgent")
        if label_id:
            print(f"✅ Urgent label ID: {label_id}")
        else:
            print("❌ Failed to get/create Urgent label")
        
        # Test email search
        print(f"\n📧 Testing email search...")
        recent_emails = await gmail_service.get_recent_emails(service, max_results=5)
        print(f"📧 Found {len(recent_emails)} recent emails:")
        for i, email_data in enumerate(recent_emails):
            print(f"   {i+1}. Subject: {email_data.get('subject', 'No subject')[:50]}...")
            print(f"      From: {email_data.get('from', 'Unknown')}")
            print(f"      Body: {email_data.get('body', 'No body')[:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_label_creation()) 