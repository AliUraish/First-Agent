import sys
sys.path.append('.')
import asyncio
from app.routers.email_sorting import get_user_by_email
from app.services.gmail import GmailService
from app.services.email_categorization import EmailCategorizationService

async def test_complete_sorting():
    try:
        # Get user
        email = "66prototype27@gmail.com"
        print(f"🔍 Testing complete email sorting for: {email}")
        user = await get_user_by_email(email)
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✅ User found: {user.email}")
        
        # Initialize services
        gmail_service = GmailService()
        categorization_service = EmailCategorizationService()
        
        service = gmail_service.build_service(user)
        if not service:
            print("❌ Failed to build Gmail service")
            return
        
        print("✅ Gmail service built successfully")
        
        # Define working flags (avoiding "Important" which conflicts with Gmail)
        test_flags = [
            {"name": "Urgent", "description": "High priority emails requiring immediate attention"},
            {"name": "Business", "description": "Important business emails and meetings"},
            {"name": "Follow-up", "description": "Emails requiring follow-up or response"}
        ]
        
        print(f"🏷️  Step 1: Setting up labels...")
        flag_names = [flag["name"] for flag in test_flags]
        label_mapping = await gmail_service.verify_labels_exist(service, email, flag_names)
        print(f"📋 Label mapping: {label_mapping}")
        
        if len(label_mapping) != len(flag_names):
            print("⚠️  Some labels missing, but continuing...")
        
        print(f"\n📧 Step 2: Getting recent emails...")
        recent_emails = await gmail_service.get_recent_emails(service, max_results=10)
        print(f"📧 Found {len(recent_emails)} recent emails")
        
        print(f"\n🤖 Step 3: Categorizing emails...")
        categorized_count = 0
        labeled_count = 0
        
        for i, email_data in enumerate(recent_emails[:5]):  # Test first 5 emails
            print(f"\n--- Email {i+1}: {email_data.get('subject', 'No subject')[:50]}... ---")
            print(f"From: {email_data.get('from', 'Unknown')}")
            
            # Categorize email
            best_flag, confidence = categorization_service.categorize_email(email_data, test_flags)
            
            if best_flag and confidence > 0:
                categorized_count += 1
                print(f"🎯 Categorized as: {best_flag} (confidence: {confidence:.2f})")
                
                # Apply label if we have the mapping
                if best_flag in label_mapping:
                    label_id = label_mapping[best_flag]
                    print(f"🏷️  Applying label '{best_flag}' (ID: {label_id})")
                    
                    # Apply the label
                    success = await gmail_service.apply_label(service, email_data['id'], label_id)
                    if success:
                        labeled_count += 1
                        print(f"✅ Successfully applied label")
                    else:
                        print(f"❌ Failed to apply label")
                else:
                    print(f"⚠️  Label ID not found for '{best_flag}'")
            else:
                print(f"🔍 No categorization (confidence too low: {confidence:.2f})")
        
        print(f"\n📊 Summary:")
        print(f"   Total emails processed: {min(len(recent_emails), 5)}")
        print(f"   Emails categorized: {categorized_count}")
        print(f"   Labels applied: {labeled_count}")
        
        if labeled_count > 0:
            print(f"🎉 SUCCESS: {labeled_count} emails were successfully categorized and labeled!")
        else:
            print(f"⚠️  No emails were labeled. Check categorization logic and label creation.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_sorting()) 