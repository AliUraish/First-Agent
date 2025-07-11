import re
import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from ..database import get_db, get_db_type
from .gemini import GeminiService

class EmailCategorizationService:
    def __init__(self):
        # Initialize Gemini service for AI-powered keyword enhancement
        self.gemini = GeminiService()
        
        # Enhanced keywords for better categorization
        self.category_keywords = {
            'urgent': {
                'subject': ['urgent', 'asap', 'immediate', 'emergency', 'critical', 'deadline', 'rush', 'priority'],
                'body': ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'deadline', 'rush', 'priority', 'time-sensitive'],
                'sender': ['boss', 'manager', 'ceo', 'director', 'admin', 'support']
            },
            'important': {
                'subject': ['important', 'meeting', 'conference', 'presentation', 'project', 'report', 'review', 'approval'],
                'body': ['important', 'meeting', 'conference', 'presentation', 'project', 'report', 'review', 'approval', 'decision'],
                'sender': ['client', 'customer', 'partner', 'vendor', 'stakeholder']
            },
            'business': {
                'subject': ['business', 'meeting', 'conference', 'presentation', 'project', 'report', 'review', 'approval', 'client', 'work'],
                'body': ['business', 'meeting', 'conference', 'presentation', 'project', 'report', 'review', 'approval', 'decision', 'client', 'work', 'professional'],
                'sender': ['client', 'customer', 'partner', 'vendor', 'stakeholder', 'business', 'company']
            },
            'follow-up': {
                'subject': ['follow up', 'follow-up', 'reminder', 'checking in', 'status', 'update', 'progress'],
                'body': ['follow up', 'follow-up', 'reminder', 'checking in', 'status', 'update', 'progress', 'next steps'],
                'sender': ['team', 'colleague', 'coordinator']
            },
            'junk': {
                'subject': ['newsletter', 'notification', 'receipt', 'confirmation', 'invoice', 'statement', 'update'],
                'body': ['newsletter', 'notification', 'receipt', 'confirmation', 'invoice', 'statement', 'unsubscribe'],
                'sender': ['no-reply', 'noreply', 'automated', 'system', 'notification']
            }
        }
        
        # Domain-based categorization
        self.domain_categories = {
            'urgent': ['emergency', 'alert', 'critical'],
            'important': ['business', 'corporate', 'company'],
            'business': ['business', 'corporate', 'company', 'work', 'professional'],
            'follow-up': ['team', 'project', 'collaboration'],
            'junk': ['newsletter', 'marketing', 'promo', 'deals', 'promotion', 'sale', 'discount', 'offer', 'coupon', 'advertisement', 'unsubscribe']
        }

    def normalize_flag_name(self, flag_name: str) -> str:
        """Normalize flag name for keyword matching"""
        return flag_name.lower().replace(' ', '-').replace('_', '-')

    def calculate_confidence_score(self, email_content: str, keywords: List[str]) -> float:
        """Calculate confidence score for a category based on keyword matches"""
        email_lower = email_content.lower()
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword.lower() in email_lower:
                matches += 1
        
        # Base confidence on keyword matches
        keyword_score = (matches / total_keywords) if total_keywords > 0 else 0
        
        # Add weight for subject line matches (higher importance)
        subject_matches = sum(1 for keyword in keywords if keyword.lower() in email_content[:100].lower())
        subject_weight = min(subject_matches * 0.2, 0.5)  # Max 50% boost from subject
        
        return min(keyword_score + subject_weight, 1.0)

    def categorize_email_enhanced(self, email_data: Dict, user_flags: List[Dict]) -> Tuple[Optional[str], float]:
        """Enhanced email categorization using sender, subject, and message content"""
        try:
            subject = email_data.get('subject', '').lower()
            sender = email_data.get('from', '').lower()
            body = email_data.get('body', '').lower()
            
            # Extract domain from sender
            domain = ''
            if '@' in sender:
                domain = sender.split('@')[1] if '@' in sender else ''
            
            # Score each flag category
            category_scores = {}
            
            for flag in user_flags:
                flag_name = flag['name'].lower()
                flag_description = flag['description'].lower().strip()
                
                score = 0.0
                
                # Check if user has provided custom description
                has_custom_description = (
                    flag_description and 
                    flag_description not in [
                        'high priority emails',
                        'important business emails', 
                        'emails requiring follow-up',
                        'marketing and promotional emails',
                        'business and work-related emails',
                        'emails to archive'
                    ]
                )
                
                if has_custom_description:
                    # Use ONLY user's custom description - ignore predefined keywords
                    print(f"Using custom description for '{flag['name']}': '{flag_description}'")
                    
                    # 1. Enhanced keyword analysis using Gemini AI (weight: 0.6)
                    enhanced_keywords = []
                    if self.gemini.is_available():
                        try:
                            enhanced_keywords = self.gemini.enhance_keywords(
                                user_prompt=flag_description,
                                email_subject=subject,
                                email_body=body
                            )
                            print(f"Gemini enhanced keywords for '{flag['name']}': {enhanced_keywords}")
                        except Exception as e:
                            print(f"Error getting Gemini keywords: {e}")
                    
                    # 2. Fallback: User's custom description analysis (weight: 0.8 if no Gemini, 0.4 if Gemini available)
                    # Split and clean description words, remove common stop words
                    stop_words = {'or', 'and', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at', 'with', 'by'}
                    description_words = [word.strip() for word in flag_description.split() 
                                       if len(word) > 1 and word.lower() not in stop_words]
                    
                    # Combine enhanced keywords with description words
                    all_keywords = enhanced_keywords + description_words
                    
                    if all_keywords:
                        # Check subject (higher weight) - with fuzzy matching for plurals/singulars
                        subject_matches = 0
                        for word in all_keywords:
                            word_lower = word.lower()
                            # Exact match
                            if word_lower in subject:
                                subject_matches += 1
                            # Check singular/plural variants
                            elif word_lower.endswith('s') and word_lower[:-1] in subject:  # plural -> singular
                                subject_matches += 1
                            elif not word_lower.endswith('s') and word_lower + 's' in subject:  # singular -> plural
                                subject_matches += 1
                        
                        if subject_matches > 0:
                            # Give higher weight if we have enhanced keywords from Gemini
                            weight_factor = 0.6 if enhanced_keywords else 0.5
                            score += min((subject_matches / len(all_keywords)) * weight_factor, weight_factor)
                        
                        # Check body with same fuzzy matching
                        body_matches = 0
                        for word in all_keywords:
                            word_lower = word.lower()
                            # Exact match
                            if word_lower in body:
                                body_matches += 1
                            # Check singular/plural variants
                            elif word_lower.endswith('s') and word_lower[:-1] in body:  # plural -> singular
                                body_matches += 1
                            elif not word_lower.endswith('s') and word_lower + 's' in body:  # singular -> plural
                                body_matches += 1
                        
                        if body_matches > 0:
                            # Give higher weight if we have enhanced keywords from Gemini
                            weight_factor = 0.4 if enhanced_keywords else 0.3
                            score += min((body_matches / len(all_keywords)) * weight_factor, weight_factor)
                    
                    # 2. Secondary: Basic urgency analysis only for urgent flags (weight: 0.2)
                    if flag_name == 'urgent':
                        urgency_score = self._analyze_urgency(subject, body)
                        score += urgency_score * 0.2
                
                else:
                    # Use predefined keywords for default descriptions
                    print(f"Using predefined keywords for '{flag['name']}'")
                    
                    # 1. Check against predefined keywords
                    if flag_name in self.category_keywords:
                        keywords = self.category_keywords[flag_name]
                        
                        # Subject analysis (weight: 0.5) - increased weight
                        subject_matches = sum(1 for keyword in keywords['subject'] if keyword in subject)
                        if subject_matches > 0:
                            score += min(subject_matches * 0.2, 0.5)  # Each match worth 0.2, max 0.5
                        
                        # Body analysis (weight: 0.4) - increased weight  
                        body_matches = sum(1 for keyword in keywords['body'] if keyword in body)
                        if body_matches > 0:
                            score += min(body_matches * 0.15, 0.4)  # Each match worth 0.15, max 0.4
                        
                        # Sender analysis (weight: 0.2)
                        sender_matches = sum(1 for keyword in keywords['sender'] if keyword in sender)
                        if sender_matches > 0:
                            score += min(sender_matches * 0.1, 0.2)  # Each match worth 0.1, max 0.2
                        
                        # Domain analysis (weight: 0.1)
                        if flag_name in self.domain_categories:
                            domain_keywords = self.domain_categories[flag_name]
                            domain_matches = sum(1 for keyword in domain_keywords if keyword in domain)
                            if domain_matches > 0:
                                score += min(domain_matches * 0.05, 0.1)  # Each match worth 0.05, max 0.1
                    
                    # 2. Pattern matching for common email types (weight: 0.3)
                    pattern_score = self._analyze_email_patterns(subject, body, sender, flag_name)
                    score += pattern_score * 0.3
                    
                    # 3. Sentiment and urgency analysis
                    urgency_score = self._analyze_urgency(subject, body)
                    if flag_name == 'urgent':
                        score += urgency_score * 0.3
                
                category_scores[flag['name']] = min(score, 1.0)  # Cap at 1.0
            
            # Find the best category
            if category_scores:
                best_category = max(category_scores.items(), key=lambda x: x[1])
                category, confidence = best_category
                
                # Lower threshold for better results
                if confidence >= 0.15:  # Lowered from 0.3 to 0.15
                    return category, confidence
            
            return None, 0.0
            
        except Exception as e:
            print(f"Error in email categorization: {e}")
            return None, 0.0

    def _analyze_email_patterns(self, subject: str, body: str, sender: str, flag_name: str) -> float:
        """Analyze email patterns for better categorization"""
        score = 0.0
        
        # Pattern analysis for different categories
        if flag_name == 'urgent':
            # Check for urgent patterns
            urgent_patterns = [
                r'\b(urgent|asap|immediate|emergency)\b',
                r'\b(deadline|due|expires?)\b',
                r'\b(action required|time sensitive)\b',
                r'[!]{2,}',  # Multiple exclamation marks
                r'\b(final notice|last chance)\b'
            ]
            for pattern in urgent_patterns:
                if re.search(pattern, subject + ' ' + body, re.IGNORECASE):
                    score += 0.2
        
        elif flag_name == 'important':
            # Check for important patterns
            important_patterns = [
                r'\b(meeting|conference|presentation)\b',
                r'\b(project|proposal|contract)\b',
                r'\b(approval|decision|review)\b',
                r'\b(client|customer|partner)\b'
            ]
            for pattern in important_patterns:
                if re.search(pattern, subject + ' ' + body, re.IGNORECASE):
                    score += 0.15
        
        elif flag_name == 'follow-up':
            # Check for follow-up patterns
            followup_patterns = [
                r'\b(follow.?up|reminder|checking in)\b',
                r'\b(status|update|progress)\b',
                r'\b(next steps|action items)\b',
                r'\bre:\s',  # Reply emails
                r'\bfwd:\s'  # Forwarded emails
            ]
            for pattern in followup_patterns:
                if re.search(pattern, subject + ' ' + body, re.IGNORECASE):
                    score += 0.2
        
        elif flag_name == 'junk':
            # Check for junk patterns (enhanced for marketing detection)
            junk_patterns = [
                r'\b(newsletter|notification|receipt)\b',
                r'\b(confirmation|invoice|statement)\b',
                r'\b(unsubscribe|opt.?out|preferences)\b',
                r'\b(automated|system|no.?reply|noreply)\b',
                r'\b(marketing|promo|promotion|promotional)\b',
                r'\b(sale|discount|offer|deal|coupon)\b',
                r'\b(advertisement|ad|sponsor|featured)\b',
                r'\b(limited.?time|expires?|hurry)\b',
                r'\b(free.?shipping|%\s*off|save\s*\$)\b',
                r'\b(subscribe|mailing.?list|newsletter)\b'
            ]
            for pattern in junk_patterns:
                if re.search(pattern, subject + ' ' + body + ' ' + sender, re.IGNORECASE):
                    score += 0.3  # Increased score for marketing detection
            
            # Check for marketing domains and sender patterns
            marketing_sender_patterns = [
                r'@.*marketing\.',
                r'@.*promo\.',
                r'@.*newsletter\.',
                r'@.*deals\.',
                r'@.*offers?\.',
                r'noreply@',
                r'no-reply@',
                r'donotreply@'
            ]
            for pattern in marketing_sender_patterns:
                if re.search(pattern, sender, re.IGNORECASE):
                    score += 0.4  # High score for marketing senders
        
        return min(score, 1.0)

    def _analyze_urgency(self, subject: str, body: str) -> float:
        """Analyze urgency indicators in email"""
        urgency_score = 0.0
        
        # High urgency indicators
        high_urgency = ['urgent', 'asap', 'immediate', 'emergency', 'critical']
        medium_urgency = ['important', 'priority', 'deadline', 'time-sensitive']
        
        text = subject + ' ' + body
        
        for word in high_urgency:
            if word in text:
                urgency_score += 0.3
        
        for word in medium_urgency:
            if word in text:
                urgency_score += 0.2
        
        # Check for punctuation indicators
        if '!!!' in text or '???' in text:
            urgency_score += 0.2
        
        # Check for time-based urgency
        time_patterns = [
            r'\b(today|tonight|tomorrow)\b',
            r'\b(this week|next week)\b',
            r'\b(deadline|due date|expires?)\b'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                urgency_score += 0.15
        
        return min(urgency_score, 1.0)

    # Keep the original method for backward compatibility
    def categorize_email(self, email_data: Dict, user_flags: List[Dict]) -> Tuple[Optional[str], float]:
        """Original categorization method - kept for backward compatibility"""
        return self.categorize_email_enhanced(email_data, user_flags)

    def batch_categorize_emails(self, emails: List[Dict], user_flags: List[Dict]) -> List[Dict]:
        """
        Categorize a batch of emails
        Returns list of categorization results
        """
        results = []
        
        for email in emails:
            category, confidence = self.categorize_email(email, user_flags)
            results.append({
                'email_id': email.get('id'),
                'email_subject': email.get('subject'),
                'email_from': email.get('from'),
                'assigned_category': category,
                'confidence_score': confidence,
                'timestamp': datetime.utcnow()
            })
        
        return results

    async def create_sorting_session(self, email: str, flag_names: List[str]) -> Optional[str]:
        """Create a new sorting session"""
        try:
            session_id = str(uuid.uuid4())
            flags_used = ','.join(flag_names)
            
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        INSERT INTO sorting_sessions (session_id, email, flags_used, status)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, email, flags_used, 'running'))
                else:
                    cursor.execute("""
                        INSERT INTO sorting_sessions (session_id, email, flags_used, status)
                        VALUES (?, ?, ?, ?)
                    """, (session_id, email, flags_used, 'running'))
                db.commit()
            
            return session_id
        except Exception as e:
            print(f"Error creating sorting session: {e}")
            return None

    async def update_sorting_session(self, session_id: str, **kwargs):
        """Update sorting session with new data"""
        try:
            # Build update query dynamically
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if value is not None:
                    update_fields.append(f"{key} = {'%s' if get_db_type() == 'postgres' else '?'}")
                    values.append(value)
            
            if not update_fields:
                return
            
            # Add end_time if status is being set to completed or failed
            if 'status' in kwargs and kwargs['status'] in ['completed', 'failed']:
                update_fields.append(f"end_time = {'%s' if get_db_type() == 'postgres' else '?'}")
                values.append(datetime.now())
            
            values.append(session_id)
            
            query = f"UPDATE sorting_sessions SET {', '.join(update_fields)} WHERE session_id = {'%s' if get_db_type() == 'postgres' else '?'}"
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute(query, values)
                db.commit()
                
        except Exception as e:
            print(f"Error updating sorting session: {e}")

    async def log_email_processing(self, session_id: str, email_data: Dict):
        """Log email processing result"""
        try:
            with get_db() as db:
                cursor = db.cursor()
                if get_db_type() == "postgres":
                    cursor.execute("""
                        INSERT INTO email_processing_log 
                        (session_id, email_id, email_subject, email_from, assigned_label, 
                         confidence_score, status, error_details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        session_id,
                        email_data.get('email_id'),
                        email_data.get('email_subject'),
                        email_data.get('email_from'),
                        email_data.get('assigned_category'),
                        email_data.get('confidence_score'),
                        email_data.get('status'),
                        email_data.get('error_details')
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO email_processing_log 
                        (session_id, email_id, email_subject, email_from, assigned_label, 
                         confidence_score, status, error_details)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        email_data.get('email_id'),
                        email_data.get('email_subject'),
                        email_data.get('email_from'),
                        email_data.get('assigned_category'),
                        email_data.get('confidence_score'),
                        email_data.get('status'),
                        email_data.get('error_details')
                    ))
                db.commit()
                
        except Exception as e:
            print(f"Error logging email processing: {e}")

    async def get_sorting_history(self, email: str, limit: int = 10) -> List[Dict]:
        """Get user's sorting session history"""
        try:
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("""
                    SELECT session_id, start_time, end_time, status, 
                           total_emails, processed_emails, flags_used, error_message
                    FROM sorting_sessions 
                    WHERE email = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (email, limit))
                
                rows = cursor.fetchall()
                history = []
                
                for row in rows:
                    history.append({
                        'session_id': row['session_id'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'status': row['status'],
                        'total_emails': row['total_emails'],
                        'processed_emails': row['processed_emails'],
                        'flags_used': row['flags_used'].split(',') if row['flags_used'] else [],
                        'error_message': row['error_message']
                    })
                
                return history
        except Exception:
            return []

    async def get_ai_flag_suggestions(self, email_data: Dict, user_flags: List[Dict]) -> List[Dict]:
        """
        Get AI-powered flag suggestions for an email using Gemini
        
        Args:
            email_data: Email content with subject, body, sender
            user_flags: List of user's configured flags
            
        Returns:
            List of flag suggestions with confidence scores and reasons
        """
        if not self.gemini.is_available():
            return []
        
        try:
            # Prepare email content for analysis
            email_content = f"Subject: {email_data.get('subject', '')}\n"
            email_content += f"From: {email_data.get('from', '')}\n"
            email_content += f"Body: {email_data.get('body', email_data.get('snippet', ''))}"
            
            # Get existing flag names
            flag_names = [flag['name'] for flag in user_flags]
            
            # Get AI suggestions
            suggestions = self.gemini.generate_flag_suggestions(email_content, flag_names)
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting AI flag suggestions: {e}")
            return []

    async def enhance_user_keywords(self, user_prompt: str, email_context: Dict = None) -> List[str]:
        """
        Enhance user prompt with AI-generated keywords
        
        Args:
            user_prompt: User's description of emails to flag
            email_context: Optional email context for better keyword generation
            
        Returns:
            List of enhanced keywords
        """
        if not self.gemini.is_available():
            return []
        
        try:
            email_subject = email_context.get('subject', '') if email_context else ''
            email_body = email_context.get('body', '') if email_context else ''
            
            enhanced_keywords = self.gemini.enhance_keywords(
                user_prompt=user_prompt,
                email_subject=email_subject,
                email_body=email_body
            )
            
            return enhanced_keywords
            
        except Exception as e:
            print(f"Error enhancing user keywords: {e}")
            return [] 