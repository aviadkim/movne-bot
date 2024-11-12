# src/utils/lead_tracker.py
import re
import uuid
from datetime import datetime
import streamlit as st
import logging
import pandas as pd

class LeadTracker:
    def __init__(self, db_manager):
        """Initialize LeadTracker with database manager"""
        self.db_manager = db_manager
        self.init_lead_tracking()

    def init_lead_tracking(self):
        """Initialize lead tracking database table"""
        try:
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            
            # Create leads table if not exists
            c.execute('''CREATE TABLE IF NOT EXISTS leads
                     (lead_id TEXT PRIMARY KEY,
                      conversation_id TEXT,
                      contact_type TEXT,
                      contact_value TEXT,
                      timestamp TIMESTAMP,
                      status TEXT DEFAULT 'new',
                      notes TEXT,
                      FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id))''')
            conn.commit()
            logging.info("Lead tracking initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize lead tracking: {str(e)}")
        finally:
            if conn:
                conn.close()

    def extract_contact_info(self, text: str) -> dict:
        """Extract contact information from text"""
        # Israeli phone patterns
        phone_patterns = [
            r'(?:\+972|972|05|\+05)[0-9\-\s]{8,10}',  # Israeli mobile
            r'0[0-9\-\s]{8,9}'  # General Israeli phone
        ]
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Name pattern (Hebrew and English)
        name_pattern = r'(?:שמי|קוראים לי|אני)\s+([\u0590-\u05FF\w\s]{2,25})'
        
        contacts = {
            'phone': [],
            'email': [],
            'name': []
        }
        
        # Extract phone numbers
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            contacts['phone'].extend([re.sub(r'\s+|-', '', phone) for phone in phones])
        
        # Extract email
        emails = re.findall(email_pattern, text)
        contacts['email'].extend(emails)
        
        # Extract name
        names = re.findall(name_pattern, text)
        if names:
            contacts['name'].extend(names)
            
        return contacts

    def save_lead(self, conversation_id: str, contact_info: dict):
        """Save lead information to database"""
        try:
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            
            for contact_type, values in contact_info.items():
                if values:  # Only save if we found contact info
                    for value in values:
                        c.execute('''INSERT INTO leads
                                    (lead_id, conversation_id, contact_type, 
                                     contact_value, timestamp, status)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                 (str(uuid.uuid4()), conversation_id, contact_type,
                                  value, datetime.now(), 'new'))
            
            # Update conversation lead status
            c.execute('''UPDATE conversations
                        SET lead_captured = ?
                        WHERE conversation_id = ?''',
                     (True, conversation_id))
            
            conn.commit()
            logging.info(f"Saved lead for conversation {conversation_id}")
        except Exception as e:
            logging.error(f"Failed to save lead: {str(e)}")
        finally:
            if conn:
                conn.close()

def show_leads_dashboard(db_manager):
    """Display leads dashboard in the sidebar"""
    st.sidebar.title("לידים חדשים")
    
    try:
        conn = db_manager.get_connection()
        
        # Get recent leads
        leads_df = pd.read_sql_query('''
            SELECT 
                l.contact_type,
                l.contact_value,
                l.timestamp,
                l.status,
                c.conversation_id
            FROM leads l
            JOIN conversations c ON l.conversation_id = c.conversation_id
            WHERE l.timestamp >= datetime('now', '-7 day')
            ORDER BY l.timestamp DESC
        ''', conn)
        
        if not leads_df.empty:
            for _, lead in leads_df.iterrows():
                with st.sidebar.expander(f"ליד מתאריך {lead['timestamp'][:16]}"):
                    st.write(f"סוג קשר: {lead['contact_type']}")
                    st.write(f"פרטי קשר: {lead['contact_value']}")
                    st.write(f"סטטוס: {lead['status']}")
                    
                    # Add status update dropdown
                    new_status = st.selectbox(
                        "עדכן סטטוס",
                        ["חדש", "בטיפול", "נסגר בהצלחה", "לא רלוונטי"],
                        key=f"status_{lead['conversation_id']}"
                    )
                    
                    if st.button("עדכן", key=f"update_{lead['conversation_id']}"):
                        try:
                            c = conn.cursor()
                            c.execute('''
                                UPDATE leads 
                                SET status = ? 
                                WHERE conversation_id = ?
                            ''', (new_status, lead['conversation_id']))
                            conn.commit()
                            st.success("הסטטוס עודכן!")
                        except Exception as e:
                            st.error("שגיאה בעדכון הסטטוס")
                            logging.error(f"Failed to update lead status: {str(e)}")
        else:
            st.sidebar.write("אין לידים חדשים בשבוע האחרון")
            
    except Exception as e:
        logging.error(f"Failed to show leads dashboard: {str(e)}")
        st.sidebar.error("אירעה שגיאה בטעינת הלידים")
    finally:
        if conn:
            conn.close()

def show_conversation(db_manager, conversation_id: str):
    """Display full conversation history"""
    try:
        conn = db_manager.get_connection()
        
        messages_df = pd.read_sql_query('''
            SELECT role, content, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp
        ''', conn, params=(conversation_id,))
        
        st.subheader(f"שיחה: {conversation_id[:8]}")
        
        for _, msg in messages_df.iterrows():
            with st.chat_message(msg['role']):
                st.write(msg['content'])
                st.caption(f"{msg['timestamp'][:16]}")
                
    except Exception as e:
        logging.error(f"Failed to show conversation: {str(e)}")
        st.error("אירעה שגיאה בטעינת השיחה")
    finally:
        if conn:
            conn.close()