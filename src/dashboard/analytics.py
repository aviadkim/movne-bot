import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import logging

class DashboardManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def show_dashboard(self):
        st.sidebar.title("לוח בקרה")
        tabs = st.tabs(["סיכום", "שיחות", "לידים", "הסכמים"])
        
        with tabs[0]:
            self.show_summary_tab()
        with tabs[1]:
            self.show_conversations_tab()
        with tabs[2]:
            self.show_leads_tab()
        with tabs[3]:
            self.show_agreements_tab()

    def show_summary_tab(self):
        try:
            conn = self.db_manager.get_connection()
            stats = pd.read_sql_query("""
                SELECT
                    COUNT(DISTINCT c.conversation_id) as total_conversations,
                    COUNT(DISTINCT l.lead_id) as total_leads,
                    COUNT(DISTINCT CASE WHEN l.status = 'חתם על הסכם' THEN l.lead_id END) as signed_agreements,
                    COUNT(DISTINCT CASE WHEN c.investor_status = 'Qualified' THEN c.conversation_id END) as qualified_investors
                FROM conversations c
                LEFT JOIN leads l ON c.conversation_id = l.conversation_id
            """, conn)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("סה״כ שיחות", stats['total_conversations'][0])
            with col2:
                st.metric("סה״כ לידים", stats['total_leads'][0])
            with col3:
                st.metric("הסכמים חתומים", stats['signed_agreements'][0])
            with col4:
                st.metric("משקיעים כשירים", stats['qualified_investors'][0])
                
            # Conversion trends
            trends = pd.read_sql_query("""
                SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as conversations,
                    COUNT(DISTINCT l.lead_id) as leads,
                    COUNT(DISTINCT CASE WHEN l.status = 'חתם על הסכם' THEN l.lead_id END) as agreements
                FROM conversations c
                LEFT JOIN leads l ON c.conversation_id = l.conversation_id
                GROUP BY DATE(start_time)
                ORDER BY date
            """, conn)
            
            fig = px.line(trends, x='date', y=['conversations', 'leads', 'agreements'],
                         title='מגמות המרה')
            st.plotly_chart(fig)
            
        except Exception as e:
            logging.error(f"Error showing summary: {str(e)}")
        finally:
            conn.close()

    def show_conversations_tab(self):
        try:
            conn = self.db_manager.get_connection()
            conversations = pd.read_sql_query("""
                SELECT 
                    c.conversation_id,
                    c.start_time,
                    c.investor_status,
                    c.qualification_reason,
                    COUNT(m.message_id) as messages_count,
                    CASE WHEN l.lead_id IS NOT NULL THEN 'כן' ELSE 'לא' END as has_lead
                FROM conversations c
                LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                LEFT JOIN leads l ON c.conversation_id = l.conversation_id
                GROUP BY c.conversation_id
                ORDER BY c.start_time DESC
            """, conn)
            
            for _, conv in conversations.iterrows():
                with st.expander(f"שיחה מתאריך {conv['start_time'][:16]}"):
                    st.write(f"סטטוס משקיע: {conv['investor_status']}")
                    if conv['qualification_reason']:
                        st.write(f"סיבת כשירות: {conv['qualification_reason']}")
                    st.write(f"מספר הודעות: {conv['messages_count']}")
                    st.write(f"יצר קשר: {conv['has_lead']}")
                    
                    messages = pd.read_sql_query("""
                        SELECT role, content, timestamp
                        FROM messages
                        WHERE conversation_id = ?
                        ORDER BY timestamp
                    """, conn, params=(conv['conversation_id'],))
                    
                    for _, msg in messages.iterrows():
                        with st.chat_message(msg['role']):
                            st.write(msg['content'])
                            st.caption(msg['timestamp'][:16])
                            
        except Exception as e:
            logging.error(f"Error showing conversations: {str(e)}")
        finally:
            conn.close()

    def show_leads_tab(self):
        try:
            conn = self.db_manager.get_connection()
            leads = pd.read_sql_query("""
                SELECT 
                    l.*,
                    c.investor_status,
                    c.qualification_reason,
                    a.status as agreement_status
                FROM leads l
                JOIN conversations c ON l.conversation_id = c.conversation_id
                LEFT JOIN agreements a ON l.lead_id = a.lead_id
                ORDER BY l.timestamp DESC
            """, conn)
            
            if st.button("ייצא לאקסל"):
                leads.to_excel("leads_export.xlsx", index=False)
                st.success("הקובץ יוצא בהצלחה!")
                
            for _, lead in leads.iterrows():
                with st.expander(f"ליד מתאריך {lead['timestamp'][:16]}"):
                    cols = st.columns(3)
                    with cols[0]:
                        st.write(f"סוג קשר: {lead['contact_type']}")
                        st.write(f"פרטי קשר: {lead['contact_value']}")
                    with cols[1]:
                        st.write(f"סטטוס משקיע: {lead['investor_status']}")
                        st.write(f"סיבת כשירות: {lead['qualification_reason']}")
                    with cols[2]:
                        st.write(f"סטטוס: {lead['status']}")
                        st.write(f"סטטוס הסכם: {lead['agreement_status']}")
                        
        except Exception as e:
            logging.error(f"Error showing leads: {str(e)}")
        finally:
            conn.close()

    def show_agreements_tab(self):
        try:
            conn = self.db_manager.get_connection()
            agreements = pd.read_sql_query("""
                SELECT 
                    a.*,
                    l.contact_value as client_contact,
                    c.investor_status,
                    c.qualification_reason
                FROM agreements a
                JOIN leads l ON a.lead_id = l.lead_id
                JOIN conversations c ON l.conversation_id = c.conversation_id
                ORDER BY a.timestamp DESC
            """, conn)
            
            for _, agreement in agreements.iterrows():
                with st.expander(f"הסכם מתאריך {agreement['timestamp'][:16]}"):
                    st.write(f"פרטי קשר: {agreement['client_contact']}")
                    st.write(f"סטטוס משקיע: {agreement['investor_status']}")
                    st.write(f"סטטוס הסכם: {agreement['status']}")
                    st.text_area("תוכן ההסכם", agreement['content'], height=200)
                    st.write(f"חתימה: {agreement['signature']}")
                    
        except Exception as e:
            logging.error(f"Error showing agreements: {str(e)}")
        finally:
            conn.close()