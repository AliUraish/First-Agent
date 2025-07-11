import google.generativeai as genai
import logging
from typing import List, Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        if self.settings.gemini_api_key:
            genai.configure(api_key=self.settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("Gemini API key not configured - AI keyword enhancement disabled")

    def enhance_keywords(self, user_prompt: str, email_subject: str = "", email_body: str = "") -> List[str]:
        """
        Use Gemini AI to generate enhanced keywords based on user prompt and email content
        
        Args:
            user_prompt: User's description of what emails they want to flag
            email_subject: Subject of the email being categorized
            email_body: Body content of the email being categorized
            
        Returns:
            List of enhanced keywords for better email matching
        """
        if not self.model:
            logger.warning("Gemini model not available - returning empty keywords")
            return []
        
        try:
            # Create a comprehensive prompt for Gemini
            system_prompt = f"""
You are an email categorization expert. Given a user's description of emails they want to flag and optionally some email content, generate relevant keywords that would help identify similar emails.

User wants to flag emails about: "{user_prompt}"

Email context (if provided):
Subject: {email_subject}
Body excerpt: {email_body[:500]}...

Generate a list of 10-15 relevant keywords, phrases, and synonyms that would help identify emails matching the user's intent. Include:
- Direct keywords from the user prompt
- Synonyms and related terms
- Common phrases used in such emails
- Professional/formal variations
- Casual/informal variations

Return only the keywords/phrases, one per line, without numbering or bullet points.
Focus on terms that would appear in email subjects, sender names, or email content.
"""

            response = self.model.generate_content(system_prompt)
            
            if response.text:
                # Parse the response into a list of keywords
                keywords = [
                    keyword.strip() 
                    for keyword in response.text.split('\n') 
                    if keyword.strip() and len(keyword.strip()) > 1
                ]
                
                logger.info(f"Generated {len(keywords)} keywords from Gemini for prompt: {user_prompt}")
                return keywords[:15]  # Limit to 15 keywords
            else:
                logger.warning("Gemini returned empty response")
                return []
                
        except Exception as e:
            logger.error(f"Error generating keywords with Gemini: {str(e)}")
            return []

    def generate_flag_suggestions(self, email_content: str, existing_flags: List[str]) -> List[dict]:
        """
        Analyze email content and suggest which existing flags might apply
        
        Args:
            email_content: Full email content (subject + body)
            existing_flags: List of existing flag names
            
        Returns:
            List of flag suggestions with confidence scores
        """
        if not self.model:
            return []
        
        try:
            flags_list = ", ".join(existing_flags)
            prompt = f"""
Analyze this email content and suggest which flags from the available list would be most appropriate:

Available flags: {flags_list}

Email content:
{email_content[:1000]}

For each relevant flag, provide:
1. Flag name (must be from the available list)
2. Confidence score (0.0 to 1.0)
3. Brief reason

Format as: FLAG_NAME|CONFIDENCE|REASON
Example: Urgent|0.8|Contains time-sensitive deadline language

Only suggest flags with confidence > 0.3. Maximum 3 suggestions.
"""

            response = self.model.generate_content(prompt)
            
            if response.text:
                suggestions = []
                for line in response.text.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            flag_name = parts[0].strip()
                            try:
                                confidence = float(parts[1].strip())
                                reason = parts[2].strip()
                                if flag_name in existing_flags and confidence > 0.3:
                                    suggestions.append({
                                        'flag': flag_name,
                                        'confidence': confidence,
                                        'reason': reason
                                    })
                            except ValueError:
                                continue
                
                return suggestions[:3]  # Limit to top 3 suggestions
            
        except Exception as e:
            logger.error(f"Error generating flag suggestions with Gemini: {str(e)}")
            
        return []

    def is_available(self) -> bool:
        """Check if Gemini service is properly configured and available"""
        return self.model is not None 