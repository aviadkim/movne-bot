import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class DashboardManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_summary_stats(self) -> Dict[str, Any]:
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
            
            return {
                "metrics": stats.to_dict(orient='records')[0],
                "trends": trends.to_dict(orient='records')
            }
        except Exception as e:
            logging.error(f"Error getting summary stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def get_conversations(self) -> List[Dict[str, Any]]:
        try:
            conn = self.db_manager.get_connection()
            conversations = pd.read_sql_query("""
                SELECT 
                    c.conversation_id,
                    c.start_time,
                    c.investor_status,
                    c.qualification_reason,
                    COUNT(m.message_id) as messages_count,
                    CASE WHEN l.lead_id IS NOT NULL THEN true ELSE false END as has_lead
                FROM conversations c
                LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                LEFT JOIN leads l ON c.conversation_id = l.conversation_id
                GROUP BY c.conversation_id
                ORDER BY c.start_time DESC
            """, conn)
            
            result = []
            for _, conv in conversations.iterrows():
                messages = pd.read_sql_query("""
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp
                """, conn, params=(conv['conversation_id'],))
                
                conv_dict = conv.to_dict()
                conv_dict['messages'] = messages.to_dict(orient='records')
                result.append(conv_dict)
                
            return result
        except Exception as e:
            logging.error(f"Error getting conversations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def get_leads(self) -> List[Dict[str, Any]]:
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
            
            return leads.to_dict(orient='records')
        except Exception as e:
            logging.error(f"Error getting leads: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    def get_agreements(self) -> List[Dict[str, Any]]:
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
            
            return agreements.to_dict(orient='records')
        except Exception as e:
            logging.error(f"Error getting agreements: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

# FastAPI router endpoints
@router.get("/summary")
async def get_summary(dashboard: DashboardManager = Depends()):
    return dashboard.get_summary_stats()

@router.get("/conversations")
async def get_conversations(dashboard: DashboardManager = Depends()):
    return dashboard.get_conversations()

@router.get("/leads")
async def get_leads(dashboard: DashboardManager = Depends()):
    return dashboard.get_leads()

@router.get("/agreements")
async def get_agreements(dashboard: DashboardManager = Depends()):
    return dashboard.get_agreements()
