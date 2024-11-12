import streamlit as st
from datetime import datetime
import os
import sys

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from src.database.models import DatabaseManager

def view_conversations(db_manager):
    st.title("היסטוריית שיחות 💬")
    
    # Get all conversations
    conversations = db_manager.get_all_conversations()
    
    if not conversations:
        st.info("אין עדיין שיחות מתועדות במערכת")
        return

    # Create filters
    col1, col2 = st.columns(2)
    with col1:
        filter_leads = st.checkbox("הצג רק לידים", value=False)
    with col2:
        filter_date = st.date_input("סנן לפי תאריך")
    
    # Display conversations
    for conv in conversations:
        try:
            # Apply filters
            if filter_leads and not conv.get('lead_captured'):
                continue
            
            start_time = conv.get('start_time', '')
            if not start_time:
                continue

            try:
                conv_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f').date()
            except:
                continue

            if filter_date and conv_date != filter_date:
                continue
            
            # Create a unique key for each conversation
            conv_key = conv.get('conversation_id', str(datetime.now().timestamp()))
            
            with st.expander(f"שיחה מתאריך {start_time} {'👤' if conv.get('contact') else ''}", key=f"conv_{conv_key}"):
                if conv.get('contact'):
                    st.info(f"פרטי קשר: {conv['contact']}")
                
                if conv.get('investor_status'):
                    st.success(f"סטטוס משקיע: {conv['investor_status']}")
                
                messages = conv.get('messages', [])
                if messages:
                    for msg in messages:
                        if msg.get('role') and msg.get('content'):
                            role_emoji = "🤖" if msg['role'] == "assistant" else "👤"
                            st.write(f"{role_emoji} **{msg['role']}**: {msg['content']}")
                else:
                    st.warning("אין הודעות בשיחה זו")

        except Exception as e:
            st.error(f"שגיאה בהצגת שיחה: {str(e)}")
            continue

def run_viewer():
    st.set_page_config(
        page_title="מערכת צפייה בשיחות - מובנה גלובל",
        page_icon="💬",
        layout="wide"
    )
    
    db = DatabaseManager()
    view_conversations(db)

if __name__ == "__main__":
    run_viewer()