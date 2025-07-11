from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import asyncio
from ..database import get_db, get_db_type
from ..services.gmail import GmailService
from ..services.email_categorization import EmailCategorizationService
from ..models import User
import uuid

router = APIRouter(prefix="/sorting", tags=["email_sorting"])

gmail_service = GmailService()
categorization_service = EmailCategorizationService()

async def get_user_by_email(email: str) -> User:
    """Get user from database by email"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("SELECT email, credentials FROM users WHERE email = %s", (email,))
            else:
                cursor.execute("SELECT email, credentials FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if row:
                # Handle different cursor types
                if hasattr(row, 'keys'):  # RealDictCursor (PostgreSQL)
                    email_val = row['email']
                    credentials_val = row['credentials']
                else:  # Regular cursor (SQLite)
                    email_val = row[0]
                    credentials_val = row[1]
                
                if credentials_val:
                    # For PostgreSQL, credentials might already be a dict
                    if isinstance(credentials_val, dict):
                        credentials_dict = credentials_val
                    else:
                        import json
                        credentials_dict = json.loads(credentials_val)
                    
                    return User(email=email_val, credentials=credentials_dict)
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        import traceback
        traceback.print_exc()
        return None

async def perform_email_sorting(email: str, active_flag_names: List[str]):
    """Background task to perform the actual email sorting"""
    try:
        # Get user and build Gmail service
        user = await get_user_by_email(email)
        if not user:
            return
        
        service = gmail_service.build_service(user)
        if not service:
            return
        
        # Create sorting session
        session_id = await categorization_service.create_sorting_session(email, active_flag_names)
        if not session_id:
            return
        
        # Get user flags for categorization
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color, is_active
                    FROM user_flags 
                    WHERE email = %s AND is_active = true
                """, (email,))
            else:
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color, is_active
                    FROM user_flags 
                    WHERE email = ? AND is_active = 1
                """, (email,))
            
            user_flags = []
            for row in cursor.fetchall():
                user_flags.append({
                    "name": row["flag_name"],
                    "description": row["flag_description"],
                    "color": row["flag_color"],
                    "isActive": bool(row["is_active"])
                })
        
        if not user_flags:
            await categorization_service.update_sorting_session(
                session_id, 
                status='failed', 
                error_message='No active flags found'
            )
            return
        
        # Verify/create Gmail labels
        label_mapping = await gmail_service.verify_labels_exist(service, email, active_flag_names)
        if not label_mapping:
            await categorization_service.update_sorting_session(
                session_id, 
                status='failed', 
                error_message='Failed to create/verify Gmail labels'
            )
            return
        
        # Get recent emails to sort
        emails = await gmail_service.get_recent_emails(service, max_results=100)
        total_emails = len(emails)
        print(f"Found {total_emails} emails to process")
        
        await categorization_service.update_sorting_session(
            session_id, 
            total_emails=total_emails
        )
        
        if not emails:
            print("No emails found to sort")
            await categorization_service.update_sorting_session(
                session_id, 
                status='completed', 
                processed_emails=0
            )
            return
        
        # Categorize and label emails
        processed_count = 0
        
        for email_item in emails:
            try:
                # Categorize the email using enhanced logic
                category, confidence = categorization_service.categorize_email_enhanced(email_item, user_flags)
                print(f"Email '{email_item.get('subject', 'No Subject')[:50]}...' -> Category: {category}, Confidence: {confidence}")
                
                # Check if this is a marketing/junk email that should be labeled as Marketing Mails
                if category and category.lower() == 'junk':
                    # Create/get Marketing Mails label
                    marketing_label_id = await gmail_service.get_or_create_label(service, email, "Marketing Mails", "#ff6b35")
                    
                    if marketing_label_id:
                        # Apply Marketing Mails label
                        label_success = await gmail_service.apply_label(service, email_item['id'], marketing_label_id)
                        print(f"Applied Marketing Mails label: {'Success' if label_success else 'Failed'}")
                        
                        # Log the labeling result
                        await categorization_service.log_email_processing(session_id, {
                            'email_id': email_item['id'],
                            'email_subject': email_item.get('subject'),
                            'email_from': email_item.get('from'),
                            'assigned_category': 'Marketing Mails',
                            'confidence_score': confidence,
                            'status': 'success' if label_success else 'failed',
                            'error_details': None if label_success else 'Failed to apply Marketing Mails label'
                        })
                    else:
                        # Log failure to create label
                        await categorization_service.log_email_processing(session_id, {
                            'email_id': email_item['id'],
                            'email_subject': email_item.get('subject'),
                            'email_from': email_item.get('from'),
                            'assigned_category': 'junk',
                            'confidence_score': confidence,
                            'status': 'failed',
                            'error_details': 'Failed to create Marketing Mails label'
                        })
                
                elif category and category in label_mapping:
                    # Apply the label to the email for non-archive categories
                    label_id = label_mapping[category]
                    success = await gmail_service.apply_label(service, email_item['id'], label_id)
                    print(f"Applied label '{category}' to email: {'Success' if success else 'Failed'}")
                    
                    # Log the processing result
                    await categorization_service.log_email_processing(session_id, {
                        'email_id': email_item['id'],
                        'email_subject': email_item.get('subject'),
                        'email_from': email_item.get('from'),
                        'assigned_category': category,
                        'confidence_score': confidence,
                        'status': 'success' if success else 'failed',
                        'error_details': None if success else 'Failed to apply label'
                    })
                else:
                    # Log as unprocessed
                    print(f"Skipping email - no category match (confidence: {confidence})")
                    await categorization_service.log_email_processing(session_id, {
                        'email_id': email_item['id'],
                        'email_subject': email_item.get('subject'),
                        'email_from': email_item.get('from'),
                        'assigned_category': None,
                        'confidence_score': confidence,
                        'status': 'skipped',
                        'error_details': 'No matching category or low confidence'
                    })
                
                processed_count += 1
                
                # Update progress
                await categorization_service.update_sorting_session(
                    session_id, 
                    processed_emails=processed_count
                )
                
                # Small delay to avoid API rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # Log processing error
                await categorization_service.log_email_processing(session_id, {
                    'email_id': email_item['id'],
                    'email_subject': email_item.get('subject'),
                    'email_from': email_item.get('from'),
                    'assigned_category': None,
                    'confidence_score': 0.0,
                    'status': 'error',
                    'error_details': str(e)
                })
                processed_count += 1
        
        # Mark session as completed
        await categorization_service.update_sorting_session(
            session_id, 
            status='completed',
            processed_emails=processed_count
        )
        
    except Exception as e:
        # Mark session as failed
        if 'session_id' in locals():
            await categorization_service.update_sorting_session(
                session_id, 
                status='failed',
                error_message=str(e)
            )

@router.post("/start")
async def start_email_sorting(background_tasks: BackgroundTasks, sort_data: Dict[str, Any]):
    """Start email sorting process"""
    try:
        email = sort_data.get("email")
        active_flags = sort_data.get("active_flags", [])
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        if not active_flags:
            raise HTTPException(status_code=400, detail="At least one active flag is required")
        
        # Verify user exists and is connected
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        service = gmail_service.build_service(user)
        if not service:
            raise HTTPException(status_code=401, detail="Gmail connection invalid")
        
        # Start background sorting task
        background_tasks.add_task(perform_email_sorting, email, active_flags)
        
        return {"message": "Email sorting started", "status": "running"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{email}")
async def get_sorting_status(email: str):
    """Get current sorting status for user"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT session_id, status, start_time, end_time, 
                           total_emails, processed_emails, error_message
                    FROM sorting_sessions 
                    WHERE email = %s 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """, (email,))
            else:
                cursor.execute("""
                    SELECT session_id, status, start_time, end_time, 
                           total_emails, processed_emails, error_message
                    FROM sorting_sessions 
                    WHERE email = ? 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """, (email,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "session_id": row["session_id"],
                    "status": row["status"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "total_emails": row["total_emails"],
                    "processed_emails": row["processed_emails"],
                    "error_message": row["error_message"]
                }
            
            return {"status": "no_session"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{email}")
async def get_sorting_history(email: str, limit: int = 10):
    """Get sorting history for user"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT session_id, status, start_time, end_time, 
                           total_emails, processed_emails, error_message, flags_used
                    FROM sorting_sessions 
                    WHERE email = %s 
                    ORDER BY start_time DESC 
                    LIMIT %s
                """, (email, limit))
            else:
                cursor.execute("""
                    SELECT session_id, status, start_time, end_time, 
                           total_emails, processed_emails, error_message, flags_used
                    FROM sorting_sessions 
                    WHERE email = ? 
                    ORDER BY start_time DESC 
                    LIMIT ?
                """, (email, limit))
            
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    "session_id": row["session_id"],
                    "status": row["status"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "total_emails": row["total_emails"],
                    "processed_emails": row["processed_emails"],
                    "error_message": row["error_message"],
                    "flags_used": row["flags_used"]
                })
            
            return {"history": history}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}/details")
async def get_session_details(session_id: str):
    """Get detailed processing log for a session"""
    try:
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT email_id, email_subject, email_from, assigned_label, 
                           confidence_score, processing_time, status, error_details
                    FROM email_processing_log 
                    WHERE session_id = %s 
                    ORDER BY processing_time DESC
                """, (session_id,))
            else:
                cursor.execute("""
                    SELECT email_id, email_subject, email_from, assigned_label, 
                           confidence_score, processing_time, status, error_details
                    FROM email_processing_log 
                    WHERE session_id = ? 
                    ORDER BY processing_time DESC
                """, (session_id,))
            
            rows = cursor.fetchall()
            
            details = []
            for row in rows:
                details.append({
                    "email_id": row["email_id"],
                    "email_subject": row["email_subject"],
                    "email_from": row["email_from"],
                    "assigned_label": row["assigned_label"],
                    "confidence_score": row["confidence_score"],
                    "processing_time": row["processing_time"],
                    "status": row["status"],
                    "error_details": row["error_details"]
                })
            
            return {"details": details}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/revert/{email}")
async def revert_email_sorting(email: str, background_tasks: BackgroundTasks):
    """Revert the most recent email sorting session by removing applied labels"""
    try:
        # Get user and build Gmail service
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        service = gmail_service.build_service(user)
        if not service:
            raise HTTPException(status_code=401, detail="Gmail connection invalid")
        
        # Get the most recent completed sorting session
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT session_id, flags_used 
                    FROM sorting_sessions 
                    WHERE email = %s AND status = 'completed'
                    ORDER BY start_time DESC 
                    LIMIT 1
                """, (email,))
            else:
                cursor.execute("""
                    SELECT session_id, flags_used 
                    FROM sorting_sessions 
                    WHERE email = ? AND status = 'completed'
                    ORDER BY start_time DESC 
                    LIMIT 1
                """, (email,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="No completed sorting sessions found to revert")
            
            if hasattr(row, 'keys'):  # PostgreSQL
                session_id = row['session_id']
                flags_used = row['flags_used']
            else:  # SQLite
                session_id = row[0]
                flags_used = row[1]
        
        # Start background revert task
        background_tasks.add_task(perform_email_revert, email, session_id, flags_used)
        
        return {"message": "Email sorting revert started", "status": "reverting", "session_id": session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def perform_email_revert(email: str, session_id: str, flags_used: str):
    """Background task to revert email labels from a sorting session"""
    try:
        # Get user and build Gmail service
        user = await get_user_by_email(email)
        if not user:
            return
        
        service = gmail_service.build_service(user)
        if not service:
            return
        
        # Get all emails that were processed in this session
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT email_id, assigned_label 
                    FROM email_processing_log 
                    WHERE session_id = %s AND status = 'success' AND assigned_label IS NOT NULL
                """, (session_id,))
            else:
                cursor.execute("""
                    SELECT email_id, assigned_label 
                    FROM email_processing_log 
                    WHERE session_id = ? AND status = 'success' AND assigned_label IS NOT NULL
                """, (session_id,))
            
            processed_emails = cursor.fetchall()
        
        if not processed_emails:
            print(f"No emails found to revert for session {session_id}")
            return
        
        # Get Gmail labels for the flags that were used
        flag_names = [flag.strip() for flag in flags_used.split(',') if flag.strip()]
        label_mapping = await gmail_service.verify_labels_exist(service, email, flag_names)
        
        # Add Marketing Mails label mapping
        marketing_label_id = await gmail_service.get_or_create_label(service, email, "Marketing Mails", "#ff6b35")
        if marketing_label_id:
            label_mapping["Marketing Mails"] = marketing_label_id
        
        reverted_count = 0
        failed_count = 0
        
        print(f"Starting revert for {len(processed_emails)} emails from session {session_id}")
        
        for email_row in processed_emails:
            try:
                if hasattr(email_row, 'keys'):  # PostgreSQL
                    email_id = email_row['email_id']
                    assigned_label = email_row['assigned_label']
                else:  # SQLite
                    email_id = email_row[0]
                    assigned_label = email_row[1]
                
                # Get the label ID for removal
                label_id = label_mapping.get(assigned_label)
                if label_id:
                    # Remove the label from the email
                    success = await gmail_service.remove_label(service, email_id, label_id)
                    if success:
                        reverted_count += 1
                        print(f"Removed label '{assigned_label}' from email {email_id}")
                    else:
                        failed_count += 1
                        print(f"Failed to remove label '{assigned_label}' from email {email_id}")
                else:
                    failed_count += 1
                    print(f"Label '{assigned_label}' not found for removal")
                
                # Small delay to avoid API rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                print(f"Error removing label from email {email_id}: {e}")
        
        print(f"Revert completed: {reverted_count} labels removed, {failed_count} failed")
        
        # Log the revert operation
        await categorization_service.create_sorting_session(email, ["REVERT"])
        revert_session_id = str(uuid.uuid4())
        
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    INSERT INTO sorting_sessions (session_id, email, flags_used, status, processed_emails, total_emails)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (revert_session_id, email, f"REVERT:{session_id}", 'completed', reverted_count, len(processed_emails)))
            else:
                cursor.execute("""
                    INSERT INTO sorting_sessions (session_id, email, flags_used, status, processed_emails, total_emails)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (revert_session_id, email, f"REVERT:{session_id}", 'completed', reverted_count, len(processed_emails)))
            db.commit()
        
    except Exception as e:
        print(f"Error during email revert: {e}")
        import traceback
        traceback.print_exc()

@router.post("/ai/enhance-keywords")
async def enhance_keywords_with_ai(data: Dict[str, Any]):
    """
    Enhance user prompt with AI-generated keywords using Gemini
    """
    try:
        user_prompt = data.get("user_prompt", "").strip()
        email_context = data.get("email_context", {})
        
        if not user_prompt:
            raise HTTPException(status_code=400, detail="User prompt is required")
        
        # Check if Gemini is available
        if not categorization_service.gemini.is_available():
            return {
                "success": False,
                "message": "AI keyword enhancement is not available (Gemini API not configured)",
                "enhanced_keywords": []
            }
        
        # Get enhanced keywords
        enhanced_keywords = await categorization_service.enhance_user_keywords(
            user_prompt=user_prompt,
            email_context=email_context
        )
        
        return {
            "success": True,
            "enhanced_keywords": enhanced_keywords,
            "original_prompt": user_prompt,
            "message": f"Generated {len(enhanced_keywords)} enhanced keywords"
        }
        
    except Exception as e:
        print(f"Error enhancing keywords with AI: {e}")
        raise HTTPException(status_code=500, detail=f"Error enhancing keywords: {str(e)}")

@router.post("/ai/suggest-flags")
async def suggest_flags_with_ai(data: Dict[str, Any]):
    """
    Get AI-powered flag suggestions for an email using Gemini
    """
    try:
        email_data = data.get("email_data", {})
        email = data.get("email", "")
        
        if not email_data:
            raise HTTPException(status_code=400, detail="Email data is required")
        
        if not email:
            raise HTTPException(status_code=400, detail="User email is required")
        
        # Check if Gemini is available
        if not categorization_service.gemini.is_available():
            return {
                "success": False,
                "message": "AI flag suggestions are not available (Gemini API not configured)",
                "suggestions": []
            }
        
        # Get user's flags
        with get_db() as db:
            cursor = db.cursor()
            if get_db_type() == "postgres":
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color
                    FROM user_flags 
                    WHERE email = %s AND is_active = true
                """, (email,))
            else:
                cursor.execute("""
                    SELECT flag_name, flag_description, flag_color
                    FROM user_flags 
                    WHERE email = ? AND is_active = 1
                """, (email,))
            
            user_flags = []
            for row in cursor.fetchall():
                user_flags.append({
                    "name": row["flag_name"],
                    "description": row["flag_description"],
                    "color": row["flag_color"]
                })
        
        if not user_flags:
            return {
                "success": False,
                "message": "No active flags found for user",
                "suggestions": []
            }
        
        # Get AI suggestions
        suggestions = await categorization_service.get_ai_flag_suggestions(
            email_data=email_data,
            user_flags=user_flags
        )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"Generated {len(suggestions)} flag suggestions"
        }
        
    except Exception as e:
        print(f"Error getting AI flag suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting flag suggestions: {str(e)}")

@router.get("/ai/status")
async def get_ai_status():
    """
    Check if AI services (Gemini) are available and configured
    """
    try:
        gemini_available = categorization_service.gemini.is_available()
        
        return {
            "gemini_available": gemini_available,
            "features_available": {
                "keyword_enhancement": gemini_available,
                "flag_suggestions": gemini_available,
                "smart_categorization": gemini_available
            },
            "message": "AI services are ready" if gemini_available else "AI services not configured"
        }
        
    except Exception as e:
        print(f"Error checking AI status: {e}")
        return {
            "gemini_available": False,
            "features_available": {
                "keyword_enhancement": False,
                "flag_suggestions": False,
                "smart_categorization": False
            },
            "message": f"Error checking AI status: {str(e)}"
        } 