import sys
sys.path.append('.')
from app.services.email_categorization import EmailCategorizationService

def debug_categorization_detailed():
    email = {
        "subject": "Meeting at 3pm",
        "from": "Ali Uraish <aliuraishmirani@gmail.com>",
        "body": "Dear sir\n\nJust a quick note to confirm our meeting scheduled for today at 3:00 PM. Please let me know if you need to reschedule or require any specific documents in advance.\n\nLooking forward to seeing you!"
    }
    
    test_flags = [
        {"name": "Important", "description": "Important business emails"},
    ]
    
    service = EmailCategorizationService()
    
    print("🔍 Detailed Debugging for 'Meeting at 3pm' email\n")
    
    # Manually trace through the algorithm
    subject = email.get('subject', '').lower()
    sender = email.get('from', '').lower()
    body = email.get('body', '').lower()
    
    print(f"Subject (lower): '{subject}'")
    print(f"Sender (lower): '{sender}'")
    print(f"Body (lower): '{body[:100]}...'")
    
    for flag in test_flags:
        flag_name = flag['name'].lower()
        flag_description = flag['description'].lower()
        
        print(f"\n--- Processing flag: {flag['name']} (normalized: {flag_name}) ---")
        
        score = 0.0
        
        # 1. Check against predefined keywords
        print(f"Checking if '{flag_name}' in category_keywords...")
        if flag_name in service.category_keywords:
            print(f"✅ Found in category_keywords")
            keywords = service.category_keywords[flag_name]
            
            print(f"Keywords for '{flag_name}':")
            print(f"  Subject keywords: {keywords['subject']}")
            print(f"  Body keywords: {keywords['body']}")
            print(f"  Sender keywords: {keywords['sender']}")
            
            # Subject analysis (weight: 0.5) - increased weight
            subject_matches = sum(1 for keyword in keywords['subject'] if keyword in subject)
            subject_score = 0
            if subject_matches > 0:
                subject_score = min(subject_matches * 0.2, 0.5)  # Each match worth 0.2, max 0.5
                score += subject_score
            print(f"  Subject matches: {subject_matches} keywords = {subject_score:.3f}")
            
            # Body analysis (weight: 0.4) - increased weight  
            body_matches = sum(1 for keyword in keywords['body'] if keyword in body)
            body_score = 0
            if body_matches > 0:
                body_score = min(body_matches * 0.15, 0.4)  # Each match worth 0.15, max 0.4
                score += body_score
            print(f"  Body matches: {body_matches} keywords = {body_score:.3f}")
            
            # Sender analysis (weight: 0.2)
            sender_matches = sum(1 for keyword in keywords['sender'] if keyword in sender)
            sender_score = 0
            if sender_matches > 0:
                sender_score = min(sender_matches * 0.1, 0.2)  # Each match worth 0.1, max 0.2
                score += sender_score
            print(f"  Sender matches: {sender_matches} keywords = {sender_score:.3f}")
            
        else:
            print(f"❌ '{flag_name}' NOT found in category_keywords")
            print(f"Available keys: {list(service.category_keywords.keys())}")
        
        # 2. Check against user's custom flag description
        description_words = flag_description.split()
        desc_matches = sum(1 for word in description_words if word in subject or word in body)
        desc_score = 0
        if description_words and desc_matches > 0:
            desc_score = min((desc_matches / len(description_words)) * 0.4, 0.3)
            score += desc_score
        print(f"  Description matches: {desc_matches}/{len(description_words)} = {desc_score:.3f}")
        
        # 3. Pattern matching
        pattern_score = service._analyze_email_patterns(subject, body, sender, flag_name)
        score += pattern_score * 0.3  # Increased weight
        print(f"  Pattern score: {pattern_score:.3f} * 0.3 = {pattern_score * 0.3:.3f}")
        
        print(f"  TOTAL SCORE: {score:.3f}")
        print(f"  Threshold: 0.15")
        print(f"  Above threshold: {score >= 0.15}")

if __name__ == "__main__":
    debug_categorization_detailed() 