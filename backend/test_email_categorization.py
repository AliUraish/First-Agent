import sys
sys.path.append('.')
import asyncio
from app.routers.email_sorting import get_user_by_email
from app.services.gmail import GmailService
from app.services.email_categorization import EmailCategorizationService

async def test_email_categorization():
    try:
        # Get user
        email = "66prototype27@gmail.com"
        print(f"🔍 Testing email categorization for: {email}")
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
        
        # Get recent emails for testing
        print("📧 Getting recent emails...")
        recent_emails = await gmail_service.get_recent_emails(service, max_results=10)
        print(f"📧 Found {len(recent_emails)} recent emails")
        
        # Test categorization service
        categorization_service = EmailCategorizationService()
        
        # Test with some flags
        test_flags = [
            {"name": "Urgent", "description": "High priority emails requiring immediate attention"},
            {"name": "Important", "description": "Important business emails"},
            {"name": "Follow-up", "description": "Emails requiring follow-up"}
        ]
        
        print(f"\n🤖 Testing categorization with {len(test_flags)} flags...")
        
        for i, email_data in enumerate(recent_emails[:3]):  # Test first 3 emails
            print(f"\n--- Email {i+1} ---")
            print(f"Subject: {email_data.get('subject', 'No subject')}")
            print(f"From: {email_data.get('from', 'Unknown')}")
            print(f"Body preview: {email_data.get('body', 'No body')[:200]}...")
            
            # Test categorization
            best_flag, confidence = categorization_service.categorize_email(
                email_data, test_flags
            )
            
            if best_flag:
                print(f"🎯 Best match: {best_flag} (confidence: {confidence:.2f})")
            else:
                print("❌ No categorization match found")
        
        # Test label verification
        print(f"\n🏷️  Testing label verification...")
        flag_names = [flag["name"] for flag in test_flags]
        label_mapping = await gmail_service.verify_labels_exist(service, email, flag_names)
        print(f"📋 Label mapping: {label_mapping}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_categorization()) 