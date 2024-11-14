import re
import uuid
from datetime import datetime
import streamlit as st
import logging
import pandas as pd
import json

class LeadTracker:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='leads.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def extract_contact_info(self, text: str) -> dict:
        """Extract contact information from conversation text"""
        contacts = {
            'phone': [],
            'email': [],
            'name': [],
            'investor_type': [],
            'company': []
        }
        
        # Phone patterns for Israeli numbers
        phone_patterns = [
            r'(?:\+972|972|05|\+05)[0-9\-\s]{8,10}',  # מספרי סלולר
            r'0[0-9\-\s]{8,9}',  # מספרי טלפון רגילים
            r'07[0-9\-\s]{8}'  # VOIPמספרי 
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            contacts['phone'].extend([re.sub(r'\s+|-', '', phone) for phone in phones])
        
        # Email pattern - improved
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        contacts['email'].extend([email.lower() for email in emails])
        
        # Name patterns - enhanced
        name_patterns = [
            r'(?:שמי|קוראים לי|אני)\s+([\u0590-\u05FF\w\s]{2,25})',
            r'(?:מדבר|מדברת)\s+([\u0590-\u05FF\w\s]{2,25})',
            r'(?:שלום|היי),?\s+([\u0590-\u05FF\w\s]{2,25})'
        ]
        for pattern in name_patterns:
            names = re.findall(pattern, text)
            if names:
                contacts['name'].extend(names)
        
        # Investor type patterns - expanded
        investor_patterns = {
            'accredited': [
                r'משקיע מוסדי', 
                r'כשיר', 
                r'מנוסה',
                r'תיק השקעות גדול',
                r'ניסיון בשוק ההון'
            ],
            'high_net_worth': [
                r'תיק השקעות של מעל',
                r'נכסים נזילים',
                r'הון עצמי',
                r'השקעות משמעותיות'
            ],
            'professional': [
                r'מנהל תיקים',
                r'יועץ השקעות',
                r'ברוקר',
                r'סוחר מקצועי'
            ]
        }
        
        for inv_type, patterns in investor_patterns.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                contacts['investor_type'].append(inv_type)

        # Company patterns
        company_patterns = [
            r'חברת\s+([\u0590-\u05FF\w\s]{2,30})',
            r'עובד ב([\u0590-\u05FF\w\s]{2,30})',
            r'מנכ"ל\s+([\u0590-\u05FF\w\s]{2,30})'
        ]
        for pattern in company_patterns:
            companies = re.findall(pattern, text)
            if companies:
                contacts['company'].extend(companies)

        return self._clean_contact_data(contacts)

    def _clean_contact_data(self, contacts: dict) -> dict:
        """Clean and validate contact information"""
        cleaned = {
            'phone': [],
            'email': [],
            'name': [],
            'investor_type': [],
            'company': []
        }
        
        # Clean phone numbers
        for phone in contacts['phone']:
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) >= 9:
                cleaned['phone'].append(phone)
        
        # Clean emails
        for email in contacts['email']:
            email = email.lower().strip()
            if '@' in email and '.' in email:
                cleaned['email'].append(email)
                
        # Clean names
        seen_names = set()
        for name in contacts['name']:
            name = name.strip()
            if 2 <= len(name) <= 40 and name not in seen_names:
                cleaned['name'].append(name)
                seen_names.add(name)
        
        # Clean investor types
        cleaned['investor_type'] = list(set(contacts['investor_type']))
        
        # Clean company names
        seen_companies = set()
        for company in contacts['company']:
            company = company.strip()
            if 2 <= len(company) <= 50 and company not in seen_companies:
                cleaned['company'].append(company)
                seen_companies.add(company)
        
        return cleaned

    def save_lead(self, conversation_id: str, contact_info: dict):
        """Save lead information to database"""
        try:
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            
            lead_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Save all contact information
            for contact_type, values in contact_info.items():
                if values:
                    for value in values:
                        c.execute('''INSERT INTO leads
                                    (lead_id, conversation_id, contact_type, contact_value,
                                     timestamp, status, notes, investor_status, agreement_status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (lead_id, conversation_id, contact_type,
                                  value, timestamp, 'new', 
                                  json.dumps({'source': 'chat', 'capture_time': str(timestamp)}),
                                  None, None))
            
            # Update conversation status
            c.execute('''UPDATE conversations
                        SET lead_captured = ?
                        WHERE conversation_id = ?''',
                     (True, conversation_id))
            
            conn.commit()
            logging.info(f"Saved lead {lead_id} for conversation {conversation_id}")
            return lead_id
            
        except Exception as e:
            logging.error(f"Failed to save lead: {str(e)}")
            return None
        finally:
            conn.close()

def show_leads_dashboard(db_manager):
    """Display leads dashboard in Streamlit"""
    st.sidebar.title("לידים חדשים")
    
    try:
        conn = db_manager.get_connection()
        
        # Get leads with full query
        leads_df = pd.read_sql_query('''
            SELECT 
                l.lead_id,
                l.contact_type,
                l.contact_value,
                l.timestamp,
                l.status,
                l.agreement_status,
                l.notes,
                l.investor_status,
                c.qualification_reason,
                COUNT(m.message_id) as message_count
            FROM leads l
            JOIN conversations c ON l.conversation_id = c.conversation_id
            LEFT JOIN messages m ON l.conversation_id = m.conversation_id
            WHERE l.timestamp >= datetime('now', '-7 day')
            GROUP BY l.lead_id, l.contact_type, l.contact_value, l.timestamp,
                     l.status, l.agreement_status, l.notes, l.investor_status,
                     c.qualification_reason
            ORDER BY l.timestamp DESC
        ''', conn)
        
        if not leads_df.empty:
            # Add filters
            status_filter = st.sidebar.multiselect(
                "סנן לפי סטטוס",
                options=leads_df['status'].unique()
            )
            
            # Apply filters
            if status_filter:
                leads_df = leads_df[leads_df['status'].isin(status_filter)]
            
            # Display leads
            for _, lead in leads_df.iterrows():
                with st.sidebar.expander(f"ליד מתאריך {lead['timestamp'][:16]}"):
                    st.write(f"סוג קשר: {lead['contact_type']}")
                    st.write(f"פרטי קשר: {lead['contact_value']}")
                    st.write(f"סטטוס: {lead['status']}")
                    st.write(f"סטטוס הסכם: {lead['agreement_status']}")
                    st.write(f"מספר הודעות: {lead['message_count']}")
                    
                    if lead['investor_status']:
                        st.write(f"סטטוס משקיע: {lead['investor_status']}")
                        if lead['qualification_reason']:
                            st.write(f"סיבת כשירות: {lead['qualification_reason']}")
                    
                    # Status update
                    new_status = st.selectbox(
                        "עדכן סטטוס",
                        ['חדש', 'בטיפול', 'חתם על הסכם', 'הושלם', 'לא רלוונטי'],
                        key=f"status_{lead['lead_id']}"
                    )
                    
                    if st.button("עדכן", key=f"update_{lead['lead_id']}"):
                        c = conn.cursor()
                        notes = json.loads(lead['notes'] or '{}')
                        notes['last_update'] = str(datetime.now())
                        notes['last_status'] = new_status
                        
                        c.execute("""
                            UPDATE leads 
                            SET status = ?,
                                notes = ?
                            WHERE lead_id = ?
                        """, (new_status, json.dumps(notes), lead['lead_id']))
                        conn.commit()
                        st.success("הסטטוס עודכן!")
                        
                    # Export lead data
                    if st.button("ייצא פרטי ליד", key=f"export_{lead['lead_id']}"):
                        lead_data = lead.to_dict()
                        st.download_button(
                            "הורד קובץ",
                            data=json.dumps(lead_data, ensure_ascii=False),
                            file_name=f"lead_{lead['lead_id'][:8]}.json",
                            mime="application/json"
                        )
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