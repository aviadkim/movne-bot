import streamlit as st
from datetime import datetime
import uuid
import logging
import sys
import time
from src.database.models import DatabaseManager
from src.bot.context import BotContext
import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
import anthropic
import re

# Load environment variables
load_dotenv()

# Configure logging for Heroku
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def set_page_style():
    st.markdown("""
    <style>
    .main { direction: rtl; }
    .stChatMessage { direction: rtl; text-align: right; }
    .stChatInput { direction: rtl; }
    .stMarkdown { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

def create_header():
    st.markdown("""
    <div style='text-align: right; direction: rtl;'>
    <h1>מובנה גלובל</h1>
    <h3>חברה לשיווק השקעות</h3>
    <p>בעלת רישיון משווק השקעות מטעם רשות ניירות ערך</p>
    </div>
    """, unsafe_allow_html=True)

class EnhancedBotContext(BotContext):
    def __init__(self):
        super().__init__()
        self.document_processor = DocumentProcessor()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    def get_response(self, prompt, db_manager, conversation_id):
        try:
            # Get conversation history
            conversation_history = db_manager.get_conversation_history(conversation_id)
            history_text = "\n".join([f"{'לקוח' if msg[0] == 'user' else 'נציג'}: {msg[1]}" for msg in conversation_history[-3:]])
            
            # Get relevant knowledge
            company_info = self.document_processor.get_core_knowledge("company")
            product_info = self.document_processor.get_core_knowledge("product")
            advantages = self.document_processor.get_core_knowledge("advantages")
            
            # Get additional relevant info from documents
            relevant_info = self.document_processor.query_knowledge(prompt)
            doc_info = "\n".join(relevant_info) if relevant_info else ""
            
            # Prepare system prompt
            system_prompt = f"""אתה נציג שיווק השקעות מקצועי ומנוסה של מובנה גלובל, עם הבנה עמוקה במוצרים פיננסיים.

            מידע על החברה:
            {company_info}

            מידע על המוצרים:
            {product_info}

            יתרונות מרכזיים:
            {advantages}

            מידע נוסף מהמסמכים:
            {doc_info}

            היסטוריית השיחה האחרונה:
            {history_text}

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

            # Get response from Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=800,
                temperature=0.7,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            bot_response = response.content[0].text if response.content else "מצטער, לא הצלחתי להבין. אנא נסה שוב."
            
            # Save messages
            db_manager.save_message(conversation_id, "user", prompt)
            db_manager.save_message(conversation_id, "assistant", bot_response)
            
            return bot_response

        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

def main():
    try:
        # Initialize components
        db_manager = DatabaseManager()
        bot_context = EnhancedBotContext()

        # Page setup
        st.set_page_config(page_title="מובנה גלובל - שיווק השקעות", layout="wide")
        set_page_style()
        create_header()

        # Session state
        if 'conversation_id' not in st.session_state:
            st.session_state.conversation_id = str(uuid.uuid4())
            db_manager.create_conversation_if_not_exists(st.session_state.conversation_id)

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Chat interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("איך אוכל לעזור לך היום?"):
            logging.info(f"Received prompt: {prompt}")

            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get and display bot response
            with st.chat_message("assistant"):
                try:
                    response = bot_context.get_response(
                        prompt,
                        db_manager,
                        st.session_state.conversation_id
                    )
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    error_msg = "מצטער, אירעה שגיאה. אנא נסה שוב."
                    st.error(error_msg)
                    logging.error(f"Error generating response: {str(e)}", exc_info=True)

    except Exception as e:
        st.error("אירעה שגיאה בטעינת המערכת. אנא רענן את הדף.")
        logging.error(f"System error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
