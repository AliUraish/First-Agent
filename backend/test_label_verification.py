import sys
sys.path.append('.')
import asyncio
from app.routers.email_sorting import get_user_by_email
from app.services.gmail import GmailService

async def test_label_verification():
    try:
        # Get user
        email = "66prototype27@gmail.com"
        print(f"🔍 Testing label verification for: {email}")
        user = await get_user_by_email(email)
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✅ User found: {user.email}")
        
        # Test Gmail service
        gmail_service = GmailService()
        service = gmail_service.build_service(user)
        
        if not service:
            print("❌ Failed to build Gmail service")
            return
        
        print("✅ Gmail service built successfully")
        
        # Test label verification with debug
        test_flag_names = ["Urgent", "Important", "Follow-up"]
        print(f"\n🏷️  Testing label verification for flags: {test_flag_names}")
        
        try:
            label_mapping = await gmail_service.verify_labels_exist(service, email, test_flag_names)
            print(f"✅ Label verification completed successfully")
            print(f"📋 Final label mapping: {label_mapping}")
        except Exception as e:
            print(f"❌ Error in label verification: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Main error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_label_verification()) 