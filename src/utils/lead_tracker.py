import re
import uuid
from datetime import datetime
import logging
import pandas as pd
import json
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/leads", tags=["leads"])

class LeadUpdate(BaseModel):
    status: str
    notes: Optional[Dict] = None

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
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def get_recent_leads(self, days: int = 7) -> List[Dict]:
        """Get recent leads from database"""
        try:
            conn = self.db_manager.get_connection()
            
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
                WHERE l.timestamp >= datetime('now', ?)
                GROUP BY l.lead_id, l.contact_type, l.contact_value, l.timestamp,
                         l.status, l.agreement_status, l.notes, l.investor_status,
                         c.qualification_reason
                ORDER BY l.timestamp DESC
            ''', conn, params=(f'-{days} day',))
            
            return leads_df.to_dict(orient='records')
            
        except Exception as e:
            logging.error(f"Failed to get leads: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def update_lead_status(self, lead_id: str, update: LeadUpdate) -> Dict:
        """Update lead status and notes"""
        try:
            conn = self.db_manager.get_connection()
            c = conn.cursor()
            
            # Get current notes
            c.execute("SELECT notes FROM leads WHERE lead_id = ?", (lead_id,))
            result = c.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Lead not found")
                
            current_notes = json.loads(result[0] or '{}')
            
            # Update notes
            notes = update.notes or {}
            notes.update({
                'last_update': str(datetime.now()),
                'last_status': update.status
            })
            notes.update(current_notes)  # Preserve existing notes
            
            # Update lead
            c.execute("""
                UPDATE leads 
                SET status = ?,
                    notes = ?
                WHERE lead_id = ?
            """, (update.status, json.dumps(notes), lead_id))
            
            conn.commit()
            
            return {"status": "success", "lead_id": lead_id}
            
        except Exception as e:
            logging.error(f"Failed to update lead: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        try:
            conn = self.db_manager.get_connection()
            messages_df = pd.read_sql_query('''
                SELECT role, content, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp
            ''', conn, params=(conversation_id,))
            
            return messages_df.to_dict(orient='records')
            
        except Exception as e:
            logging.error(f"Failed to get conversation: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

# FastAPI router endpoints
@router.get("/recent")
async def get_recent_leads(days: int = 7, tracker: LeadTracker = Depends()):
    return tracker.get_recent_leads(days)

@router.put("/{lead_id}")
async def update_lead(lead_id: str, update: LeadUpdate, tracker: LeadTracker = Depends()):
    return tracker.update_lead_status(lead_id, update)

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str, tracker: LeadTracker = Depends()):
    return tracker.get_conversation_history(conversation_id)
