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

        # Form URLs
        self.forms_urls = {
            'qualified_investor': "https://movne-global.streamlit.app/הצהרת_משקיע_כשיר",
            'marketing_agreement': "https://movne-global.streamlit.app/הסכם_שיווק_השקעות"
        }
        
        # Returns related keywords
        self.returns_keywords = [
            'תשואה', 'תשואות', 'ריבית', 'קופון', 'רווח', 'רווחים', 
            'החזר', 'אחוזים', 'תשלום תקופתי'
        ]

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
            
            # Check for returns/rates related questions
            if self.is_returns_question(prompt):
                return self.handle_returns_inquiry(prompt, db_manager, conversation_id)

            # Check for agreement request
            if self.is_agreement_request(prompt):
                return self.handle_agreement_request()

            # Try cached response
            quick_response = self._get_cached_response(prompt)
            if quick_response:
                db_manager.save_message(conversation_id, "user", prompt)
                db_manager.save_message(conversation_id, "assistant", quick_response)
                return quick_response

            # Get normal Claude response
            return self._get_claude_response(prompt, db_manager, conversation_id)
            
        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

    def is_returns_question(self, text: str) -> bool:
        """Check if question is about returns"""
        return any(keyword in text.lower() for keyword in self.returns_keywords)

    def is_agreement_request(self, text: str) -> bool:
        """Check if request is about agreement"""
        agreement_keywords = ['הסכם', 'חוזה', 'התקשרות', 'טופס', 'רישום']
        return any(keyword in text.lower() for keyword in agreement_keywords)

    def handle_returns_inquiry(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Handle returns related questions"""
        conversation_history = db_manager.get_conversation_history(conversation_id)
        
        # Check if already asked about qualified investor status
        qualification_asked = any(
            "האם אתה משקיע כשיר" in msg[1] 
            for msg in conversation_history 
            if msg[0] == 'assistant'
        )
        
        if not qualification_asked:
            response = """
            לפני שנוכל לדבר על תשואות ספציפיות, 
            כחברה המפוקחת על ידי רשות ניירות ערך, עלי לוודא האם אתה משקיע כשיר.
            
            האם אתה עומד באחד מהתנאים הבאים:
            1. השווי הכולל של הנכסים הנזילים שבבעלותך עולה על 8,364,177 ₪
            2. הכנסתך השנתית בשנתיים האחרונות עולה על 1,254,627 ₪
            3. השווי הכולל של נכסיך הנזילים עולה על 5,227,610 ₪ וגם הכנסתך השנתית מעל 627,313 ₪

            האם אתה עומד באחד מהתנאים הללו? 🤔
            """
        else:
            # Check last response after qualification question
            last_question_index = max(i for i, msg in enumerate(conversation_history) 
                                    if msg[0] == 'assistant' and "האם אתה משקיע כשיר" in msg[1])
            
            if last_question_index < len(conversation_history) - 1:
                user_response = conversation_history[last_question_index + 1][1].lower()
                if "כן" in user_response:
                    response = f"""
                    מצוין! אנא מלא את טופס הצהרת המשקיע הכשיר בקישור הבא:
                    {self.forms_urls['qualified_investor']}
                    
                    לאחר מילוי הטופס נשמח לשלוח לך במייל את כל המידע המפורט על התשואות והמוצרים שלנו.
                    האם תרצה להשאיר את כתובת המייל שלך? 📧
                    """
                else:
                    response = f"""
                    תודה על הכנות. אני ממליץ שנתחיל בחתימה על הסכם שיווק השקעות:
                    {self.forms_urls['marketing_agreement']}
                    
                    ההסכם יעזור לנו:
                    • להכיר טוב יותר את הצרכים שלך
                    • להבין את מטרות ההשקעה שלך
                    • לקבוע את פרופיל הסיכון המתאים לך
                    
                    לאחר מילוי ההסכם, נשמח לקבוע פגישה אישית להתאמת מוצר מושלם עבורך.
                    
                    האם יש משהו נוסף שתרצה לדעת על תהליך ההתקשרות? 🤝
                    """
            else:
                response = self._get_claude_response(prompt, db_manager, conversation_id)

        db_manager.save_message(conversation_id, "user", prompt)
        db_manager.save_message(conversation_id, "assistant", response)
        return response

    def handle_agreement_request(self) -> str:
        """Handle agreement related requests"""
        return f"""
        אשמח להפנות אותך להסכם השיווק שלנו:
        {self.forms_urls['marketing_agreement']}
        
        ההסכם כולל:
        • פרטים אישיים בסיסיים
        • שאלון הכרת לקוח
        • הגדרת מטרות השקעה
        • בחירת פרופיל סיכון
        
        לאחר מילוי ההסכם נוכל:
        1. להתאים עבורך מוצר מושלם
        2. לקבוע פגישה אישית
        3. לדבר על פרטים ספציפיים
        
        האם יש משהו שתרצה לדעת על ההסכם לפני שתתחיל למלא? 📝
        """

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

    def _get_claude_response(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Get response from Claude API"""
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
            
            # Add form links if relevant
            bot_response = self.add_form_links_if_needed(bot_response)
            
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
        5. הדגש את היתרונות הייחודיים שלנו:
           - נזילות יומית עם מחיר מהמנפיק
           - העסקה ישירה מול הבנק
           - המוצר בחשבון הבנק של הלקוח
        6. תן תשובות מעמיקות המעידות על הבנה פיננסית"""

    def add_form_links_if_needed(self, response: str) -> str:
        """Add form links if relevant"""
        if any(word in response.lower() for word in ['הסכם', 'חוזה', 'טופס']):
            response += f"\n\nקישור להסכם שיווק השקעות: {self.forms_urls['marketing_agreement']}"
        
        if 'משקיע כשיר' in response.lower():
            response += f"\n\nקישור להצהרת משקיע כשיר: {self.forms_urls['qualified_investor']}"
        
        return response

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

def format_response(self, response: str) -> str:
        """Format and enhance the response"""
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
            elif 'תשואה' in response or 'רווח' in response:
                response += ' 💰'
            
            return response

        except Exception as e:
            logging.error(f"Error formatting response: {str(e)}")
            return response