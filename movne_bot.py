from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
import logging
import sys
import os
from src.database.models import DatabaseManager
from src.bot.context import BotContext
from dotenv import load_dotenv
from document_processor import DocumentProcessor
import anthropic
import re

# Load environment variables
load_dotenv()

# Configure logging for FastAPI
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(title="Movne Global Bot API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhancedBotContext(BotContext):
    def __init__(self):
        super().__init__()
        self.document_processor = DocumentProcessor()

    def _get_system_prompt(self) -> str:
        """Override system prompt to include document processor info"""
        company_info = self.document_processor.get_core_knowledge("company")
        product_info = self.document_processor.get_core_knowledge("product")
        advantages = self.document_processor.get_core_knowledge("advantages")
        
        return f"""אתה נציג שיווק השקעות מקצועי ומנוסה של מובנה גלובל, עם הבנה עמוקה במוצרים פיננסיים.

        מידע על החברה:
        {company_info}

        מידע על המוצרים:
        {product_info}

        יתרונות מרכזיים:
        {advantages}

        הנחיות חשובות:
        1. תן הסברים מקצועיים ומעמיקים, אבל בשפה ברורה
        2. אסור לציין אחוזי תשואה או ריבית ספציפיים ללא חתימת הסכם
        3. הדגש את היתרונות הייחודיים:
           - נזילות יומית עם מחיר מהמנפיק
           - העסקה ישירה מול הבנק
           - המוצר בחשבון הבנק של הלקוח
        4. התאם את רמת ההסבר לשאלה
        5. השתמש בדוגמאות להמחשה
        6. הוסף אימוג'י אחד מתאים בסוף

        ענה בצורה טבעית ומקצועית, כמו יועץ השקעות מנוסה שמסביר ללקוח."""

    def _get_claude_response(self, prompt: str, db_manager, conversation_id: str) -> str:
        """Override to include document processor info in the response"""
        try:
            # Get conversation history
            conversation_history = db_manager.get_conversation_history(conversation_id)
            history_text = "\n".join([f"{'לקוח' if msg[0] == 'user' else 'נציג'}: {msg[1]}" for msg in conversation_history[-3:]])
            
            # Get additional relevant info from documents
            relevant_info = self.document_processor.query_knowledge(prompt)
            doc_info = "\n".join(relevant_info) if relevant_info else ""
            
            # Add document info to system prompt
            system_prompt = self._get_system_prompt()
            if doc_info:
                system_prompt += f"\n\nמידע נוסף מהמסמכים:\n{doc_info}"
            if history_text:
                system_prompt += f"\n\nהיסטוריית השיחה האחרונה:\n{history_text}"

            # Get response from Claude
            response = self.client.messages.create(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-opus-20240229",
                max_tokens=800,
                temperature=0.7,
                system=system_prompt
            )

            bot_response = response.content[0].text if response.content else "מצטער, לא הצלחתי להבין. אנא נסה שוב."
            
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

# Initialize database manager and bot context
db_manager = DatabaseManager()
bot_context = EnhancedBotContext()

@app.post("/chat/")
async def chat(prompt: str, conversation_id: str = None):
    """
    Endpoint to handle chat interactions.
    If conversation_id is not provided, a new one is created.
    """
    try:
        # Generate a new conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            db_manager.create_conversation_if_not_exists(conversation_id)
        
        # Log the received prompt
        logging.info(f"Received prompt: {prompt}")

        # Get bot response
        response = bot_context._get_claude_response(prompt, db_manager, conversation_id)

        # Return the response with conversation ID
        return {
            "conversation_id": conversation_id,
            "response": response
        }

    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="מצטער, אירעה שגיאה. אנא נסה שוב.")

