import yaml
import logging
import anthropic
import os
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BotContext:
    def __init__(self, config_path: str = 'config'):
        self.config_path = config_path
        self.config = self.load_knowledge_base()
        
        # Initialize Anthropic client with API key from environment
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        logging.info("Anthropic client initialized successfully")
        
        self._load_responses_cache()
        
        logging.basicConfig(
            filename='muvne_bot.log',
            level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Update forms URLs to use FastAPI endpoints
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
        self.forms_urls = {
            'qualified_investor': f"{base_url}/forms/qualified-investor",
            'marketing_agreement': f"{base_url}/forms/marketing-agreement"
        }
        
        # Define keywords for returns questions
        self.returns_keywords = [
            'תשואה', 'תשואות', 'ריבית', 'קופון', 'רווח', 'רווחים', 
            'החזר', 'אחוזים', 'תשלום תקופתי'
        ]
        
        # Define qualified investor criteria
        self.qualified_investor_criteria = """
        משקיע כשיר הוא מי שעומד באחד מהתנאים הבאים:
        1. השווי הכולל של הנכסים הנזילים שבבעלותו עולה על 8,364,177 ₪
        2. הכנסתו השנתית בכל אחת מהשנתיים האחרונות עולה על 1,254,627 ₪ (או 1,881,940 ₪ להכנסת התא המשפחתי)
        3. השווי הכולל של נכסיו הנזילים עולה על 5,227,610 ₪ וגם הכנסתו השנתית עולה על 627,313 ₪ (או 940,969 ₪ לתא משפחתי)
        """

    def _load_responses_cache(self):
        """Load and cache common responses"""
        self.responses_cache = {}
        sales_responses = self.config.get('sales_responses', {})
        if isinstance(sales_responses, dict):
            for category, responses in sales_responses.items():
                if isinstance(responses, list):
                    for response in responses:
                        if isinstance(response, dict) and 'pattern' in response and 'response' in response:
                            patterns = response['pattern'].split('|')
                            for pattern in patterns:
                                self.responses_cache[pattern.lower()] = response['response']
        logging.info("Responses cache loaded successfully")

    def load_knowledge_base(self) -> Dict:
        """Load configuration files"""
        config = {}
        config_files = {
            'client_questionnaire': 'client_questionnaire.yaml',
            'company_info': 'company_info.yaml',
            'legal': 'legal.yaml',
            'products': 'products.yaml',
            'sales_responses': 'sales_responses.yaml'
        }
        
        for key, filename in config_files.items():
            try:
                file_path = os.path.join(self.config_path, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config[key] = yaml.safe_load(f)
                    logging.info(f"Loaded {filename}")
                else:
                    logging.error(f"File not found: {file_path}")
                    config[key] = {}
            except Exception as e:
                logging.error(f"Failed to load {filename}: {str(e)}")
                config[key] = {}
        return config

    def get_response(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Get response for user prompt"""
        try:
            logging.info(f"Getting response for prompt: {prompt}")
            
            # Try cached response first
            quick_response = self._get_cached_response(prompt)
            if quick_response:
                logging.info("Using cached response")
                db_manager.save_message(conversation_id, "user", prompt)
                db_manager.save_message(conversation_id, "assistant", quick_response)
                return quick_response

            # Handle special cases and get Claude response
            return self._get_claude_response(prompt, db_manager, conversation_id)
            
        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

    def _get_cached_response(self, prompt: str) -> Optional[str]:
        """Get response from cache if available"""
        try:
            prompt_lower = prompt.lower()
            
            # Add time-sensitive greeting
            hour = datetime.now().hour
            greeting = (
                "בוקר טוב" if 5 <= hour < 12
                else "צהריים טובים" if 12 <= hour < 17
                else "ערב טוב" if 17 <= hour < 21
                else "לילה טוב"
            )

            for pattern, response in self.responses_cache.items():
                if pattern in prompt_lower:
                    return response.replace('DYNAMIC_GREETING', greeting)
                    
            return None
        except Exception as e:
            logging.error(f"Error in cached response: {str(e)}")
            return None

    def is_question_requires_qualification(self, question: str) -> bool:
        """Check if question requires investor qualification"""
        return any(term in question.lower() for term in self.returns_keywords)

    def get_qualification_check_response(self) -> str:
        """Response for returns-related questions"""
        return f"""
        אשמח לספק לך מידע מפורט על התשואות והמוצרים שלנו.
        
        כחברה המפוקחת על ידי רשות ניירות ערך, עלינו לוודא תחילה האם אתה עומד בקריטריונים של משקיע כשיר.
        
        האם אתה משקיע כשיר? 
        
        {self.qualified_investor_criteria}
        """

    def handle_investor_response(self, is_qualified: bool) -> str:
        """Handle client response about qualified investor status"""
        if is_qualified:
            return f"""
            מצוין! על מנת שנוכל להמשיך, אנא מלא את טופס הצהרת המשקיע הכשיר בקישור הבא:
            {self.forms_urls['qualified_investor']}
            
            לאחר מילוי הטופס, נשמח לשלוח לך במייל מידע מפורט על המוצרים והתשואות שלנו.
            
            האם תרצה להשאיר את כתובת המייל שלך? 📧
            """
        else:
            return f"""
            תודה על הכנות. אני ממליץ להתחיל בחתימה על הסכם שיווק השקעות כדי שנוכל להכיר אותך טוב יותר:
            {self.forms_urls['marketing_agreement']}
            
            ההסכם כולל:
            - פרטי לקוח בסיסיים
            - שאלון להבנת צרכי ההשקעה שלך
            - מדיניות השקעות
            - פרופיל סיכון
            
            לאחר חתימה על ההסכם, נשמח לקבוע פגישה אישית להכרות מעמיקה יותר ולהתאים עבורך את הפתרון המושלם.
            
            האם יש משהו נוסף שתרצה לדעת על תהליך ההתקשרות? 🤝
            """

    def _get_claude_response(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Get response from Claude API with enhanced logic"""
        try:
            # Check if question is about returns
            if self.is_question_requires_qualification(prompt):
                conversation_history = db_manager.get_conversation_history(conversation_id)
                
                # Check if we already asked about qualified investor
                already_asked = any("האם אתה משקיע כשיר" in msg[1] 
                                  for msg in conversation_history 
                                  if msg[0] == 'assistant')
                
                if not already_asked:
                    response = self.get_qualification_check_response()
                    db_manager.save_message(conversation_id, "user", prompt)
                    db_manager.save_message(conversation_id, "assistant", response)
                    return response
                
                # Check if we got an answer to the qualified investor question
                last_question_index = max(i for i, msg in enumerate(conversation_history) 
                                        if msg[0] == 'assistant' and "האם אתה משקיע כשיר" in msg[1])
                
                if last_question_index < len(conversation_history) - 1:
                    user_response = conversation_history[last_question_index + 1][1].lower()
                    if "כן" in user_response:
                        response = self.handle_investor_response(True)
                    elif "לא" in user_response:
                        response = self.handle_investor_response(False)
                    else:
                        # Continue with normal response if no clear answer
                        return self._get_normal_claude_response(prompt, db_manager, conversation_id)
                        
                    db_manager.save_message(conversation_id, "user", prompt)
                    db_manager.save_message(conversation_id, "assistant", response)
                    return response
            
            # Check for agreement request
            if any(word in prompt.lower() for word in ['הסכם', 'חוזה', 'התקשרות']):
                response = self.handle_investor_response(False)  # Use same function for agreement info
                db_manager.save_message(conversation_id, "user", prompt)
                db_manager.save_message(conversation_id, "assistant", response)
                return response
            
            # Default to normal Claude response
            return self._get_normal_claude_response(prompt, db_manager, conversation_id)
            
        except Exception as e:
            logging.error(f"Error in _get_claude_response: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

    def _get_normal_claude_response(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Get standard response from Claude"""
        try:
            # Prepare system prompt
            system_prompt = self._get_system_prompt()
            
            # Get response from Claude
            response = self.client.messages.create(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-opus-20240229",
                max_tokens=800,
                system=system_prompt
            )
            
            bot_response = response.content[0].text if hasattr(response, 'content') else "מצטער, לא הצלחתי להבין. אנא נסה שוב."
            
            # Add legal disclaimer if needed
            if self._needs_legal_disclaimer(bot_response):
                bot_response = self._add_legal_disclaimer(bot_response)
            
            # Save messages
            db_manager.save_message(conversation_id, "user", prompt)
            db_manager.save_message(conversation_id, "assistant", bot_response)
            
            return bot_response
            
        except Exception as e:
            logging.error(f"Claude API error: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

    def _get_system_prompt(self) -> str:
        """Get system prompt from config"""
        company_info = self.config.get('company_info', {})
        products_info = self.config.get('products', {})
        
        return f"""אתה נציג שיווק השקעות מקצועי של מובנה גלובל.

        מידע בסיסי על החברה:
        {company_info.get('description', '')}

        מידע על המוצרים:
        {products_info.get('description', '')}

        חוקים חשובים:
        1. אסור לציין אחוזי תשואה או ריבית ספציפיים
        2. התמקד במידע כללי על החברה והמוצרים
        3. הצע פגישה רק אם הלקוח מביע עניין
        4. היה ידידותי אך מקצועי
        5. תן תשובות מעמיקות המעידות על הבנה פיננסית"""

    def _needs_legal_disclaimer(self, text: str) -> bool:
        """Check if response needs legal disclaimer"""
        terms_requiring_disclaimer = [
            'תשואה', 'ריבית', 'רווח', 'החזר',
            'השקעה', 'סיכון', 'הגנה', 'קרן'
        ]
        return any(term in text for term in terms_requiring_disclaimer)

    def _add_legal_disclaimer(self, text: str) -> str:
        """Add legal disclaimer to response"""
        disclaimer = self.config.get('legal', {}).get('disclaimer', 
            "\n\nאין לראות במידע המוצג המלצה או ייעוץ להשקעה.")
        return f"{text}{disclaimer}"

    def contains_restricted_info(self, text: str) -> bool:
        """Check if text contains restricted information"""
        restricted_patterns = [
            r'\d+%',  # Any percentage
            r'קופון של',
            r'תשואה של',
            r'ריבית של',
            r'החזר של',
            r'רווח של'
        ]
        return any(re.search(pattern, text) for pattern in restricted_patterns)

    def get_conversation_context(self, conversation_history: List[Tuple[str, str]]) -> str:
        """Get relevant context from conversation history"""
        try:
            recent_messages = conversation_history[-3:]  # Get last 3 messages
            return "\n".join([f"{'לקוח' if role == 'user' else 'נציג'}: {msg}" 
                            for role, msg in recent_messages])
        except Exception as e:
            logging.error(f"Error getting conversation context: {str(e)}")
            return ""

    def format_response(self, response: str) -> str:
        """Format the response with proper styling and structure"""
        try:
            # Add emojis based on content
            if 'פגישה' in response:
                response += ' 📅'
            elif 'מייל' in response:
                response += ' 📧'
            elif 'השקעה' in response:
                response += ' 📈'
            elif 'חתימה' in response or 'הסכם' in response:
                response += ' 📝'
                
            return response

        except Exception as e:
            logging.error(f"Error formatting response: {str(e)}")
            return response

    def handle_error(self, error: Exception) -> str:
        """Handle errors gracefully"""
        logging.error(f"Error occurred: {str(error)}")
        return "מצטער, אירעה שגיאה. אנא נסה שוב או פנה לנציג שירות."
